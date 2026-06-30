"""
Phase 1B — UNT Faculty Information System Scraper
Project: UNT Collections Assessment Research
Source: https://facultyinfo.unt.edu

Searches the UNT Faculty Information System by department, collects faculty
profile links, visits each profile, and loads results into stg_unt_faculty.
"""

import os
import re
import time
import logging
from urllib.parse import urljoin, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup
import pyodbc

BASE_URL = "https://facultyinfo.unt.edu"
SEARCH_URL = f"{BASE_URL}/faculty-search"
PROFILE_URL = f"{BASE_URL}/faculty-profile"

UNT_DEPARTMENTS = [
    "Information Science",
    "Learning Technologies",
    "Linguistics",
    "Library Science",
    "Data Science",

    "Accounting",
    "Finance, Insurance, Real Estate and Law",
    "Information Technology and Decision Sciences",
    "Management",
    "Marketing",
    "Supply Chain Management",
    "Hospitality, Event and Tourism Management",

    "Biological Sciences",
    "Chemistry",
    "Mathematics",
    "Physics",
    "Psychology",
    "Data Analytics & Statistics",

    "Computer Science and Engineering",
    "Electrical Engineering",
    "Mechanical Engineering",
    "Materials Science and Engineering",
    "Biomedical Engineering",
    "Civil Engineering",

    "English",
    "History",
    "Philosophy and Religion",
    "Political Science",
    "Sociology",
    "Geography and the Environment",
    "Communication Studies",
    "World Languages, Literatures, and Cultures",
    "Technical Communication",

    "Educational Psychology",
    "Teacher Education and Administration",
    "Counseling and Higher Education",

    "Music",

    "Art Education",
    "Design",
    "Studio Art",

    "Audiology and Speech-Language Pathology",
    "Public Administration",
    "Rehabilitation and Health Services",
    "Social Work",
]

REQUEST_DELAY = 0.5
MAX_RETRIES = 4
RETRY_BACKOFF = 2.0
RETRY_HTTP_CODES = [429, 500, 502, 503]

HEADERS = {
    "User-Agent": os.environ.get(
        "SCRAPER_USER_AGENT",
        "UNT-Bibliometrics-Research/1.0 (contact: set SCRAPER_USER_AGENT env var)"
    )
}

DB_CONFIG = {
    "driver": "ODBC Driver 17 for SQL Server",
    "server": os.environ.get("DB_SERVER", "localhost"),
    "database": os.environ.get("DB_NAME", "UNT_Bibliometrics"),
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("unt_faculty_scrape.log"),
        logging.StreamHandler()
    ]
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


def create_faculty_table(conn):
    cursor = conn.cursor()

    cursor.execute("""
        IF NOT EXISTS (
            SELECT 1 FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME = 'stg_unt_faculty'
        )
        CREATE TABLE stg_unt_faculty (
            profile_id          VARCHAR(50)     PRIMARY KEY,
            faculty_name         NVARCHAR(300)   NULL,
            title                NVARCHAR(300)   NULL,
            department           NVARCHAR(300)   NULL,
            college              NVARCHAR(300)   NULL,
            email                VARCHAR(300)    NULL,
            profile_url          VARCHAR(500)    NULL,
            searched_under_dept  NVARCHAR(300)   NULL,
            extracted_at         DATETIME        DEFAULT GETDATE()
        )
    """)

    conn.commit()
    log.info("stg_unt_faculty table verified / created successfully.")


def fetch_html(url, params=None):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(
                url, params=params, headers=HEADERS, timeout=30
            )

            if response.status_code == 200:
                return response.text

            elif response.status_code in RETRY_HTTP_CODES:
                wait_time = RETRY_BACKOFF ** attempt
                log.warning(
                    f"HTTP {response.status_code} on attempt {attempt} "
                    f"for {url}. Retrying in {wait_time:.1f}s..."
                )
                time.sleep(wait_time)

            elif response.status_code == 404:
                log.warning(f"404 Not Found: {url}")
                return None

            else:
                log.error(f"Non-retryable HTTP error {response.status_code}: {url}")
                return None

        except requests.exceptions.Timeout:
            wait_time = RETRY_BACKOFF ** attempt
            log.warning(f"Timeout on attempt {attempt} for {url}. Retrying in {wait_time:.1f}s...")
            time.sleep(wait_time)

        except requests.exceptions.ConnectionError:
            wait_time = RETRY_BACKOFF ** attempt
            log.warning(f"Connection error on attempt {attempt} for {url}. Retrying in {wait_time:.1f}s...")
            time.sleep(wait_time)

        except Exception as e:
            log.error(f"Unexpected error fetching {url}: {e}")
            return None

    log.error(f"All {MAX_RETRIES} attempts failed for {url}. Skipping.")
    return None


def extract_profile_ids_from_search(html, dept_name):
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    found = []
    seen_ids = set()

    for link in soup.find_all("a", href=True):
        href = link["href"]

        if "faculty-profile" in href and "profile=" in href:
            full_url = urljoin(BASE_URL, href)
            parsed = urlparse(full_url)
            query_params = parse_qs(parsed.query)
            profile_id = query_params.get("profile", [None])[0]

            if profile_id and profile_id not in seen_ids:
                seen_ids.add(profile_id)
                found.append({
                    "profile_id": profile_id,
                    "profile_url": full_url,
                })

    log.info(f"  Found {len(found)} profile links under '{dept_name}'")
    return found


def extract_faculty_details(html, profile_id, profile_url):
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    page_text = soup.get_text(separator="\n")

    def extract_field(label, text):
        pattern = rf"{re.escape(label)}\s*:\s*(.+?)(?:\n|$)"
        match = re.search(pattern, text)
        return match.group(1).strip() if match else None

    name_tag = soup.find("h1")
    faculty_name = name_tag.get_text(strip=True) if name_tag else None

    title = extract_field("Title", page_text)
    department = extract_field("Department", page_text)
    college = extract_field("College", page_text)

    email = None
    mailto_link = soup.find("a", href=lambda h: h and h.startswith("mailto:"))
    if mailto_link:
        email = mailto_link["href"].replace("mailto:", "").strip()

    return {
        "profile_id": profile_id,
        "faculty_name": faculty_name,
        "title": title,
        "department": department,
        "college": college,
        "email": email,
        "profile_url": profile_url,
    }


FACULTY_UPSERT = """
    IF EXISTS (SELECT 1 FROM stg_unt_faculty WHERE profile_id = ?)
        UPDATE stg_unt_faculty
        SET faculty_name = ?, title = ?, department = ?, college = ?,
            email = ?, profile_url = ?, extracted_at = GETDATE()
        WHERE profile_id = ?
    ELSE
        INSERT INTO stg_unt_faculty (
            profile_id, faculty_name, title, department, college,
            email, profile_url, searched_under_dept
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
"""


def upsert_faculty(cursor, faculty_row, searched_under_dept):
    cursor.execute(FACULTY_UPSERT, (
        faculty_row["profile_id"],
        faculty_row["faculty_name"], faculty_row["title"],
        faculty_row["department"], faculty_row["college"],
        faculty_row["email"], faculty_row["profile_url"],
        faculty_row["profile_id"],
        faculty_row["profile_id"], faculty_row["faculty_name"],
        faculty_row["title"], faculty_row["department"],
        faculty_row["college"], faculty_row["email"],
        faculty_row["profile_url"], searched_under_dept,
    ))


def scrape_and_load():
    log.info("=" * 70)
    log.info("UNT Faculty Information System Scrape — Starting")
    log.info(f"  Departments to search : {len(UNT_DEPARTMENTS)}")
    log.info("=" * 70)

    conn = get_db_connection()
    cursor = conn.cursor()
    create_faculty_table(conn)

    all_seen_profile_ids = set()
    total_inserted = 0
    total_skipped_duplicate = 0
    total_failed = 0

    for dept_index, dept_name in enumerate(UNT_DEPARTMENTS, start=1):
        log.info(f"[{dept_index}/{len(UNT_DEPARTMENTS)}] Searching department: {dept_name}")

        search_html = fetch_html(SEARCH_URL, params={"dept": dept_name})
        time.sleep(REQUEST_DELAY)

        if not search_html:
            log.warning(f"  Skipping '{dept_name}' — search request failed.")
            continue

        profile_links = extract_profile_ids_from_search(search_html, dept_name)

        if not profile_links:
            log.warning(f"  No profiles found for '{dept_name}' — check spelling/name match.")
            continue

        for entry in profile_links:
            profile_id = entry["profile_id"]
            profile_url = entry["profile_url"]

            if profile_id in all_seen_profile_ids:
                total_skipped_duplicate += 1
                continue

            all_seen_profile_ids.add(profile_id)

            profile_html = fetch_html(profile_url)
            time.sleep(REQUEST_DELAY)

            if not profile_html:
                log.warning(f"  Failed to fetch profile: {profile_id}")
                total_failed += 1
                continue

            faculty_row = extract_faculty_details(profile_html, profile_id, profile_url)

            if not faculty_row or not faculty_row.get("faculty_name"):
                log.warning(f"  Could not parse details for profile: {profile_id}")
                total_failed += 1
                continue

            try:
                upsert_faculty(cursor, faculty_row, searched_under_dept=dept_name)
                conn.commit()
                total_inserted += 1
            except Exception as e:
                log.error(f"  DB upsert failed for {profile_id}: {e}")
                conn.rollback()
                total_failed += 1

        log.info(
            f"  Progress so far - Unique faculty: {len(all_seen_profile_ids)}, "
            f"Saved: {total_inserted}, Failed: {total_failed}"
        )

    log.info("=" * 70)
    log.info("UNT Faculty Scrape Complete!")
    log.info(f"  Departments Searched      : {len(UNT_DEPARTMENTS)}")
    log.info(f"  Unique Faculty Found      : {len(all_seen_profile_ids)}")
    log.info(f"  Successfully Saved        : {total_inserted}")
    log.info(f"  Skipped (cross-dept dupes): {total_skipped_duplicate}")
    log.info(f"  Failed to Fetch/Parse     : {total_failed}")
    log.info("=" * 70)

    cursor.close()
    conn.close()


if __name__ == "__main__":
    scrape_and_load()
