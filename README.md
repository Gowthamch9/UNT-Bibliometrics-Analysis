# 📚 UNT Bibliometric Research Pipeline

> An end-to-end data engineering and analytics pipeline built to understand the research output, citation impact, open access trends, and faculty productivity of the **University of North Texas** — powered by OpenAlex, Python, T-SQL, and Power BI.

---

## 🧭 Project Overview

 This independent research project builds a **reproducible, structured bibliometric pipeline** from scratch — transforming raw publication metadata into actionable institutional insights.

The pipeline extracts over **52,039 UNT-affiliated research works** spanning more than 25 years (2000–until now), enriches them with faculty directory data, cleanses and audits the data in SQL Server, and delivers findings through **four interactive Power BI dashboards**.

---

## 🏗️ Architecture — Three Phases

```
Phase 1 — Data Collection
    ├── 1A: OpenAlex API → stg_openalex_works / stg_openalex_authors / stg_openalex_topics
    └── 1B: UNT Faculty Directory Scraper → stg_unt_faculty

Phase 2 — Cleansing & EDA
    ├── Stage 0: Full data audit (row counts, NULL rates, duplicate analysis)
    ├── Stage 1: Works deduplication (DOI, title, exact duplicates)
    ├── Stage 2: Author affiliation cleansing & anomaly investigation
    ├── Stage 3: Entity disambiguation — author ↔ faculty matching
    ├── Stage 4: Topics hierarchy validation
    └── Stage 5: Exploratory analysis in T-SQL (10 analytical views)

Phase 3 — Insights & Dashboards
    └── Power BI: 4 dashboards — Overview · OA & Citations · Topics · Authors
```

---

## 📊 Data at a Glance

| Staging Table | Rows | Description |
|---|---|---|
| `stg_openalex_works` | 52,039 | One row per research publication |
| `stg_openalex_authors` | 359,947 | One row per author–institution pair per paper |
| `stg_openalex_topics` | 141,611 | Domain → Field → Subfield → Topic hierarchy |
| `stg_unt_faculty` | 1,889 | Current UNT faculty profiles with dept & college |

---

## ⚙️ Tech Stack

| Layer | Technology |
|---|---|
| Data Extraction | Python 3, OpenAlex REST API |
| Web Scraping | Python 3, BeautifulSoup, requests |
| Database | Microsoft SQL Server (MSSQL) |
| Transformation & EDA | T-SQL (10 analytical views) |
| Visualization | Microsoft Power BI |
| Version Control | Git / GitHub |

---

## 📁 Repository Structure

```
unt-collections-assessment/
│
├── extraction/
│   ├── openalex_unt_extractor.py    # Phase 1A — OpenAlex API pipeline
│   └── unt_faculty_scraper.py       # Phase 1B — Faculty directory scraper
│
├── sql/
│   ├── views/                       # 10 T-SQL analytical views
│   └── audit/                       # Stage 0 data audit queries
│
├── dashboards/
│   └── UNT_Bibliometrics.pbix       # Power BI dashboard file
│
└── README.md
```

---

## 🐍 Phase 1A — OpenAlex Extractor

**Source:** [OpenAlex API](https://api.openalex.org) — a free, open catalog of 200M+ research publications.

**What it does:**
- Filters to UNT's institution ID (`I123534392`) and publication year ≥ 2000
- Paginates through all results using **cursor-based pagination** (200 records/page)
- Parses nested JSON — flattening venue, authorship, open access, and topic hierarchy
- Loads into three normalized MSSQL staging tables via **idempotent batch inserts**
- Handles transient failures with **exponential backoff retry logic** (up to 5 attempts)

**Python packages:** `requests` · `pyodbc` · `json` · `time` · `logging` · `datetime`

### Setup

```bash
pip install requests pyodbc
```

```bash
export OPENALEX_API_KEY="your_key_here"      # free at openalex.org/settings/api
export DB_SERVER="your_sql_server_name"
export DB_NAME="UNT_Bibliometrics"
```

```bash
python extraction/openalex_unt_extractor.py
```

---

## 🕷️ Phase 1B — UNT Faculty Scraper

**Source:** [facultyinfo.unt.edu](https://facultyinfo.unt.edu) — UNT's official Faculty Information System.

**What it does:**
- Searches the FIS by department name (~40 UNT departments across all colleges)
- Collects faculty profile links from search results using **BeautifulSoup**
- Visits each profile page individually to extract Name, Title, Department, College, and Email
- Deduplicates cross-department results by `profile_id` (handles joint appointments)
- Loads into MSSQL via **UPSERT logic** — refreshes changed records on re-run

**Python packages:** `requests` · `BeautifulSoup` · `pyodbc` · `re` · `urllib.parse` · `logging`

```bash
pip install requests beautifulsoup4 pyodbc
```

```bash
export DB_SERVER="your_sql_server_name"
export DB_NAME="UNT_Bibliometrics"
export SCRAPER_USER_AGENT="YourProject/1.0 (contact: your@email.com)"
```

```bash
python extraction/unt_faculty_scraper.py
```

> **Why UPSERT?** Unlike publications — which are fixed once written — a faculty member's title or department can change. UPSERT ensures the table stays current on every re-run rather than silently retaining stale data.

---

## 🧹 Phase 2 — Cleansing & EDA

### Data Audit Findings (Stage 0)

| Table | Rows | Key Findings |
|---|---|---|
| `stg_openalex_works` | 52,039 | 2,497 null DOIs · 8 exact dupes · 28 DOI dupes · 1,388 title dupes |
| `stg_openalex_authors` | 359,947 | 14,425 null author IDs · 122,890 null ORCIDs · 27,147 null institution IDs |
| `stg_openalex_topics` | 141,611 | ✅ No NULLs |
| `stg_unt_faculty` | 1,889 | ✅ No duplicates |

### Notable Root Cause Discovery

One of the more interesting findings: **31 works passed the API filter but showed no UNT-affiliated author in the staging table.** Investigation revealed these papers had **500+ authors**, and OpenAlex truncates authorship lists at 100 positions — the UNT author was simply beyond the extraction window. These works were confirmed as genuinely UNT-affiliated and retained.

### Analytical Views (Stage 5 EDA)

| View | Description |
|---|---|
| `publication_volume_trend` | Works per year (2000–2025) |
| `domain_stats` | Work counts by OpenAlex domain (4 domains) |
| `domain_field_stats` | Work counts by field within each domain (26 fields) |
| `domain_field_subfield_stats` | Full subfield breakdown |
| `domain_field_subfield_topic_stats` | 4,081 unique topic classifications |
| `open_access_stats` | OA rate, OA count, closed count — by year |
| `domain_citations` | Citation bucket distribution by domain and field |
| `work_type_stats` | Article vs book-chapter vs preprint breakdown |
| `unt_affiliation_stats` | UNT authorship concentration per work (fractional counting) |
| `author_stats` / `faculty_stats` | Prolific UNT authors with department mapping |

---

## 📈 Phase 3 — Power BI Dashboards

Four interactive dashboards built on top of the T-SQL views via DirectQuery:

| **Research Overview** | KPI cards · 25-year publication trend · Work type split · Domain breakdown |
![Dashboard 1](https://github.com/Gowthamch9/UNT-Bibliometrics-Analysis/blob/main/Power%20BI%20Dashboards/Screenshot%202026-06-30%20133134.png)

| **Open Access & Citation Impact** | OA rate over time · OA vs closed donut · Citation distribution by field |
![Dashboard 2](https://github.com/Gowthamch9/UNT-Bibliometrics-Analysis/blob/main/Power%20BI%20Dashboards/Screenshot%202026-06-30%20133142.png)

| **Research Topics Deep Dive** | Cascading domain → field → subfield → topic filters · Treemap · Topic table |
![Dashboard 3](https://github.com/Gowthamch9/UNT-Bibliometrics-Analysis/blob/main/Power%20BI%20Dashboards/Screenshot%202026-06-30%20133151.png)

| **Authors & Collaboration** | UNT authorship concentration · Prolific authors · Faculty dept/college table |
![Dashboard 4](https://github.com/Gowthamch9/UNT-Bibliometrics-Analysis/blob/main/Power%20BI%20Dashboards/Screenshot%202026-06-30%20133200.png)

### Methodological Highlights

**Fractional Counting** — When UNT is one of 50 authors on a paper, that paper is not counted as a full UNT publication. The `unt_affiliation_stats` view computes UNT's proportional share of authorship, producing fairer productivity metrics aligned with standard bibliometric practice.

**Two-source pipeline** — OpenAlex tells us *what* was published and *who* was listed as UNT-affiliated. The faculty directory tells us *which department* that person belongs to and whether they are current faculty (as opposed to alumni or visiting researchers). Together, they enable department and college-level dashboards that OpenAlex alone cannot produce.

---

## ⚠️ Known Limitations

- **Author position cap:** OpenAlex returns a maximum of 100 author positions per work. Papers with 500+ authors may silently miss UNT affiliations deep in the list.
- **Alumni misattribution:** OpenAlex's ML algorithm may carry forward a researcher's past UNT affiliation onto papers published after they have moved to another institution.
- **Missing ORCIDs:** ~34% of author rows have no ORCID, limiting the reliability of author disambiguation.
- **Faculty directory coverage:** 1,889 of ~3,327 reported UNT faculty were captured. The department list in `unt_faculty_scraper.py` can be expanded to improve coverage.
- **No `raw_affiliation_string`:** This field was scoped for a future extraction pass and is not yet in `stg_openalex_authors`. Its absence limits the ability to catch missed UNT affiliations via text matching.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Microsoft SQL Server with ODBC Driver 17
- Power BI Desktop (for `.pbix` file)
- Free OpenAlex API key ([register here](https://openalex.org/settings/api))

### Environment Variables

```bash
OPENALEX_API_KEY=your_openalex_api_key
DB_SERVER=your_sql_server_name
DB_NAME=UNT_Bibliometrics
SCRAPER_USER_AGENT=YourProject/1.0 (contact: your@email.com)
```

> **Never hardcode credentials.** Use environment variables or a `.env` file (add `.env` to `.gitignore`).

### Run Order

```bash
# 1. Extract publications from OpenAlex
python extraction/openalex_unt_extractor.py

# 2. Scrape faculty directory
python extraction/unt_faculty_scraper.py

# 3. Run audit and cleansing SQL scripts (sql/audit/)

# 4. Create analytical views (sql/views/)

# 5. Open dashboards/UNT_Bibliometrics.pbix in Power BI Desktop
#    → Refresh data source connection to your local SQL Server
```

---

## 🎓 About

This project was built independently as part of research in Information Science at the **University of North Texas**, in collaboration with the UNT Collections Assessment team. It represents a full-stack applied research portfolio spanning data engineering, bibliometrics methodology, SQL analytics, and interactive visualization.

**Author:** Gowtham Venkat Eathamokkala
**Program:** PhD, Information Science — University of North Texas
**Contact:** GowthamVenkatEathamokkala@unt.edu

---

## 📄 License

This project is for academic and research purposes. Data sourced from [OpenAlex](https://openalex.org) (CC0) and UNT's publicly accessible Faculty Information System.
