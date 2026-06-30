"""
Phase 1A — OpenAlex UNT Publication Data Extractor
Project: UNT Collections Assessment Research

Extracts UNT-affiliated works from the OpenAlex API (publication_year >= 2000)
and loads them into MSSQL staging tables: stg_openalex_works,
stg_openalex_authors, stg_openalex_topics.
"""

import os
import json
import time
import logging
from datetime import datetime

import requests
import pyodbc

UNT_OPENALEX_ID = "I123534392"
API_KEY = os.environ.get("OPENALEX_API_KEY", "")
BASE_URL = "https://api.openalex.org/works"
FROM_YEAR = 2000
PER_PAGE = 200
REQUEST_DELAY = 0.15

MAX_RETRIES = 5
RETRY_BACKOFF = 2.0
RETRY_HTTP_CODES = [429, 500, 503]

DB_CONFIG = {
    "driver": "ODBC Driver 17 for SQL Server",
    "server": os.environ.get("DB_SERVER", "localhost"),
    "database": os.environ.get("DB_NAME", "UNT_Bibliometrics"),
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("openalex_extraction.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


def get_db_connection():
    conn_str = (
        f"DRIVER={{{DB_CONFIG['driver']}}};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"Trusted_Connection=yes;"
    )
    return pyodbc.connect(conn_str)


def create_staging_tables(conn):
    cursor = conn.cursor()

    cursor.execute("""
        IF NOT EXISTS (
            SELECT 1 FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME = 'stg_openalex_works'
        )
        CREATE TABLE stg_openalex_works (
            work_id                 VARCHAR(50)     PRIMARY KEY,
            doi                     VARCHAR(500)    NULL,
            title                   NVARCHAR(2000)  NULL,
            publication_year        SMALLINT        NULL,
            publication_date        DATE            NULL,
            work_type               VARCHAR(100)    NULL,
            venue_id                VARCHAR(50)     NULL,
            venue_name              NVARCHAR(500)   NULL,
            venue_issn              VARCHAR(50)     NULL,
            venue_publisher         NVARCHAR(500)   NULL,
            volume                  VARCHAR(50)     NULL,
            issue                   VARCHAR(50)     NULL,
            first_page              VARCHAR(20)     NULL,
            last_page               VARCHAR(20)     NULL,
            cited_by_count          INT             NULL,
            referenced_works_count  INT             NULL,
            is_oa                   BIT             NULL,
            oa_status               VARCHAR(50)     NULL,
            oa_url                  VARCHAR(1000)   NULL,
            language                VARCHAR(20)     NULL,
            raw_json                NVARCHAR(MAX)   NULL,
            extracted_at            DATETIME        DEFAULT GETDATE()
        )
    """)

    cursor.execute("""
        IF NOT EXISTS (
            SELECT 1 FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME = 'stg_openalex_authors'
        )
        CREATE TABLE stg_openalex_authors (
            record_id           INT IDENTITY(1,1) PRIMARY KEY,
            work_id              VARCHAR(50)     NOT NULL,
            author_position      INT             NULL,
            author_id            VARCHAR(50)     NULL,
            author_name          NVARCHAR(500)   NULL,
            author_orcid         VARCHAR(100)    NULL,
            institution_id       VARCHAR(50)     NULL,
            institution_name     NVARCHAR(500)   NULL,
            is_unt_affiliated    BIT             NULL,
            extracted_at         DATETIME        DEFAULT GETDATE()
        )
    """)

    cursor.execute("""
        IF NOT EXISTS (
            SELECT 1 FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME = 'stg_openalex_topics'
        )
        CREATE TABLE stg_openalex_topics (
            record_id        INT IDENTITY(1,1) PRIMARY KEY,
            work_id          VARCHAR(50)     NOT NULL,
            topic_rank       INT             NULL,
            topic_id         VARCHAR(50)     NULL,
            topic_name       NVARCHAR(500)   NULL,
            topic_score      FLOAT           NULL,
            domain_id        VARCHAR(50)     NULL,
            domain_name      NVARCHAR(500)   NULL,
            field_id         VARCHAR(50)     NULL,
            field_name       NVARCHAR(500)   NULL,
            subfield_id      VARCHAR(50)     NULL,
            subfield_name    NVARCHAR(500)   NULL,
            extracted_at     DATETIME        DEFAULT GETDATE()
        )
    """)

    conn.commit()
    log.info("Staging tables verified / created successfully.")


def fetch_with_retry(url, params):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 200:
                return response.json()

            elif response.status_code in RETRY_HTTP_CODES:
                wait_time = RETRY_BACKOFF ** attempt
                log.warning(
                    f"HTTP {response.status_code} on attempt {attempt}. "
                    f"Retrying in {wait_time:.1f}s..."
                )
                time.sleep(wait_time)

            else:
                log.error(f"Non-retryable HTTP error: {response.status_code}")
                return None

        except requests.exceptions.Timeout:
            wait_time = RETRY_BACKOFF ** attempt
            log.warning(f"Timeout on attempt {attempt}. Retrying in {wait_time:.1f}s...")
            time.sleep(wait_time)

        except requests.exceptions.ConnectionError:
            wait_time = RETRY_BACKOFF ** attempt
            log.warning(f"Connection error on attempt {attempt}. Retrying in {wait_time:.1f}s...")
            time.sleep(wait_time)

        except Exception as e:
            log.error(f"Unexpected error on attempt {attempt}: {e}")
            return None

    log.error(f"All {MAX_RETRIES} attempts failed. Skipping this page.")
    return None


def parse_work(work):
    work_id = work.get("id", "").replace("https://openalex.org/", "")

    venue = work.get("primary_location") or {}
    source = venue.get("source") or {}
    venue_id = (source.get("id") or "").replace("https://openalex.org/", "") or None
    venue_name = source.get("display_name")
    venue_issn = source.get("issn_l")
    venue_pub = source.get("host_organization_name")

    biblio = work.get("biblio") or {}
    oa = work.get("open_access") or {}

    pub_date_str = work.get("publication_date")
    pub_date = None
    if pub_date_str:
        try:
            pub_date = datetime.strptime(pub_date_str, "%Y-%m-%d").date()
        except Exception:
            pass

    work_row = {
        "work_id": work_id,
        "doi": work.get("doi"),
        "title": (work.get("title") or "")[:2000],
        "publication_year": work.get("publication_year"),
        "publication_date": pub_date,
        "work_type": work.get("type"),
        "venue_id": venue_id or None,
        "venue_name": (venue_name or "")[:500],
        "venue_issn": venue_issn,
        "venue_publisher": (venue_pub or "")[:500],
        "volume": biblio.get("volume"),
        "issue": biblio.get("issue"),
        "first_page": biblio.get("first_page"),
        "last_page": biblio.get("last_page"),
        "cited_by_count": work.get("cited_by_count"),
        "referenced_works_count": work.get("referenced_works_count"),
        "is_oa": int(oa.get("is_oa") or 0),
        "oa_status": oa.get("oa_status"),
        "oa_url": (oa.get("oa_url") or "")[:1000],
        "language": work.get("language"),
        "raw_json": json.dumps(work),
    }

    author_rows = []
    for pos, authorship in enumerate(work.get("authorships") or [], start=1):
        author = authorship.get("author") or {}
        author_id = (author.get("id") or "").replace("https://openalex.org/", "") or None
        institutions = authorship.get("institutions") or []

        for inst in institutions or [{}]:
            inst_id = (inst.get("id") or "").replace("https://openalex.org/", "") or None
            inst_name = inst.get("display_name")
            is_unt = 1 if inst_id == UNT_OPENALEX_ID else 0

            author_rows.append({
                "work_id": work_id,
                "author_position": pos,
                "author_id": author_id,
                "author_name": author.get("display_name"),
                "author_orcid": author.get("orcid"),
                "institution_id": inst_id,
                "institution_name": (inst_name or "")[:500],
                "is_unt_affiliated": is_unt,
            })

        if not institutions:
            author_rows.append({
                "work_id": work_id,
                "author_position": pos,
                "author_id": author_id,
                "author_name": author.get("display_name"),
                "author_orcid": author.get("orcid"),
                "institution_id": None,
                "institution_name": None,
                "is_unt_affiliated": 0,
            })

    topic_rows = []
    for rank, topic_entry in enumerate(work.get("topics") or [], start=1):
        domain = topic_entry.get("domain") or {}
        field = topic_entry.get("field") or {}
        subfield = topic_entry.get("subfield") or {}

        topic_rows.append({
            "work_id": work_id,
            "topic_rank": rank,
            "topic_id": (topic_entry.get("id") or "").replace("https://openalex.org/", "") or None,
            "topic_name": topic_entry.get("display_name"),
            "topic_score": topic_entry.get("score"),
            "domain_id": (domain.get("id") or "").replace("https://openalex.org/", "") or None,
            "domain_name": domain.get("display_name"),
            "field_id": (field.get("id") or "").replace("https://openalex.org/", "") or None,
            "field_name": field.get("display_name"),
            "subfield_id": (subfield.get("id") or "").replace("https://openalex.org/", "") or None,
            "subfield_name": subfield.get("display_name"),
        })

    return work_row, author_rows, topic_rows


WORKS_INSERT = """
    IF NOT EXISTS (SELECT 1 FROM stg_openalex_works WHERE work_id = ?)
    INSERT INTO stg_openalex_works (
        work_id, doi, title, publication_year, publication_date,
        work_type, venue_id, venue_name, venue_issn, venue_publisher,
        volume, issue, first_page, last_page,
        cited_by_count, referenced_works_count,
        is_oa, oa_status, oa_url, language, raw_json
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
"""

AUTHORS_INSERT = """
    INSERT INTO stg_openalex_authors (
        work_id, author_position, author_id, author_name,
        author_orcid, institution_id, institution_name, is_unt_affiliated
    ) VALUES (?,?,?,?,?,?,?,?)
"""

TOPICS_INSERT = """
    INSERT INTO stg_openalex_topics (
        work_id, topic_rank, topic_id, topic_name, topic_score,
        domain_id, domain_name, field_id, field_name,
        subfield_id, subfield_name
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
"""


def insert_works_batch(cursor, works_batch):
    rows = []
    for w in works_batch:
        rows.append((
            w["work_id"],
            w["work_id"],
            w["doi"],
            w["title"],
            w["publication_year"],
            w["publication_date"],
            w["work_type"],
            w["venue_id"],
            w["venue_name"],
            w["venue_issn"],
            w["venue_publisher"],
            w["volume"],
            w["issue"],
            w["first_page"],
            w["last_page"],
            w["cited_by_count"],
            w["referenced_works_count"],
            w["is_oa"],
            w["oa_status"],
            w["oa_url"],
            w["language"],
            w["raw_json"],
        ))
    cursor.executemany(WORKS_INSERT, rows)


def insert_authors_batch(cursor, authors_batch):
    rows = [
        (
            a["work_id"], a["author_position"], a["author_id"],
            a["author_name"], a["author_orcid"],
            a["institution_id"], a["institution_name"], a["is_unt_affiliated"]
        )
        for a in authors_batch
    ]
    cursor.executemany(AUTHORS_INSERT, rows)


def insert_topics_batch(cursor, topics_batch):
    rows = [
        (
            t["work_id"], t["topic_rank"], t["topic_id"],
            t["topic_name"], t["topic_score"],
            t["domain_id"], t["domain_name"],
            t["field_id"], t["field_name"],
            t["subfield_id"], t["subfield_name"]
        )
        for t in topics_batch
    ]
    cursor.executemany(TOPICS_INSERT, rows)


def fetch_and_load():
    log.info("=" * 70)
    log.info("UNT OpenAlex Extraction — Starting")
    log.info(f"  Institution : {UNT_OPENALEX_ID}")
    log.info(f"  From Year   : {FROM_YEAR}")
    log.info(f"  Page Size   : {PER_PAGE}")
    log.info("=" * 70)

    conn = get_db_connection()
    cursor = conn.cursor()
    create_staging_tables(conn)

    params = {
        "api_key": API_KEY,
        "filter": (
            f"institutions.id:{UNT_OPENALEX_ID},"
            f"publication_year:>{FROM_YEAR - 1}"
        ),
        "per-page": PER_PAGE,
        "cursor": "*",
        "select": ",".join([
            "id", "doi", "title", "publication_year", "publication_date",
            "type", "primary_location", "biblio", "open_access",
            "cited_by_count", "referenced_works_count",
            "authorships", "topics", "language"
        ]),
    }

    total_works = 0
    total_authors = 0
    total_topics = 0
    page_num = 0

    while True:
        page_num += 1
        log.info(f"Fetching page {page_num}...")

        data = fetch_with_retry(BASE_URL, params)
        if data is None:
            log.error(f"Failed to fetch page {page_num}. Stopping extraction.")
            break

        results = data.get("results", [])
        meta = data.get("meta", {})
        next_cursor = meta.get("next_cursor")

        if not results:
            log.info("No results on this page — extraction complete.")
            break

        works_batch = []
        authors_batch = []
        topics_batch = []

        for work in results:
            work_row, author_rows, topic_rows = parse_work(work)
            works_batch.append(work_row)
            authors_batch.extend(author_rows)
            topics_batch.extend(topic_rows)

        try:
            insert_works_batch(cursor, works_batch)
            insert_authors_batch(cursor, authors_batch)
            insert_topics_batch(cursor, topics_batch)
            conn.commit()
        except Exception as e:
            log.error(f"DB insert failed on page {page_num}: {e}")
            conn.rollback()

        total_works += len(works_batch)
        total_authors += len(authors_batch)
        total_topics += len(topics_batch)

        log.info(
            f"Page {page_num:>4} | "
            f"Works: {len(works_batch):>3} | "
            f"Cumulative \u2192 Works: {total_works:>6}, "
            f"Authors: {total_authors:>7}, "
            f"Topics: {total_topics:>7}"
        )

        if not next_cursor:
            log.info("No next cursor returned — all pages fetched.")
            break

        params["cursor"] = next_cursor
        time.sleep(REQUEST_DELAY)

    log.info("=" * 70)
    log.info("Extraction Complete!")
    log.info(f"  Total Works   : {total_works:,}")
    log.info(f"  Total Authors : {total_authors:,}")
    log.info(f"  Total Topics  : {total_topics:,}")
    log.info(f"  Pages Fetched : {page_num:,}")
    log.info("=" * 70)

    cursor.close()
    conn.close()


if __name__ == "__main__":
    fetch_and_load()
