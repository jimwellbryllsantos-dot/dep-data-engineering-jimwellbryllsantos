# Bata, Bata, Saan Ka Nagmula?
# *From Birthplace to Opportunity: Building Provincial Opportunity Index for the Philippines*


## Problem Statement


I want to answer:


> **"To what extent does being born in a specific province or urban center in the Philippines influence access to education, economic mobility, and development opportunities?"**


More specifically, this project aims to:


> **"Construct a Provincial Opportunity Index that quantifies and compares opportunity levels across Philippine provinces and Highly Urbanized Cities (HUCs) using measurable indicators of education, economic conditions, infrastructure, healthcare access, and digital connectivity."**


The Philippines exhibits persistent regional inequality, where provinces and independent cities differ significantly in income levels, infrastructure availability, and access to public services. While poverty statistics are widely used, they do not fully capture the broader concept of “opportunity” — defined here as the structural conditions that enable upward mobility.


This project addresses that gap by building a composite, data-driven index across **118 administrative domains** (82 provinces and 36 Highly Urbanized Cities) to measure and compare opportunity using publicly available datasets. Separating HUCs from their parent geographical provinces prevents dense economic centers from skewing rural provincial indicators.


---


## Audience


This project is intended for:


### Primary Audience
- Policy makers and government planning agencies (e.g., NEDA, PSA, DILG)
- Development organizations and NGOs working on poverty reduction and regional development
- Academic researchers in economics, statistics, and public policy


### Secondary Audience
- Private sector organizations conducting regional expansion (banks, telcos, retail, logistics)
- Data analysts and data engineers interested in geospatial and socioeconomic analytics
- Students and professionals exploring data-driven policy modeling


The goal is to provide a structured, evidence-based view of regional opportunity disparities in the Philippines that can support decision-making at both public and private levels.


---


## KPI or Key Metric


### Main Metric: Provincial Opportunity Index (POI)


The **Provincial Opportunity Index (POI)** is a composite score (0–100) representing the relative level of opportunity available within each province and HUC domain.

It is constructed from normalized indicators across five domains:


### 1. Economic Conditions
- Poverty incidence
- Average household income 
- Employment rate


### 2. Educational Access
- Number of schools per capita (Basic & Higher Education)
- Student-to-school ratio
- Student-to-teaching staff ratio


### 3. Healthcare Access
- Number of health facilities per capita


### 4. Infrastructure & Accessibility
- Road density (OpenStreetMap-derived road networks)


### Composite Construction Approach
- Min-max normalization of each indicator
- Weighted aggregation (initially equal weighting, subject to sensitivity testing)
- Optional PCA-based weighting for robustness comparison


---


## Data Source Notes

The Provincial Opportunity Index (POI) is constructed by integrating multiple authoritative government datasets across all 118 target domains (82 provinces + 36 HUCs). Each domain of the index is supported by one or more primary data sources.

---

## Domain 1 — Economic Conditions

### Primary Source 1
- **Name:** 2023 Official Poverty Statistics – Poverty Incidence Among Population by Region and Province
- **Agency:** Philippine Statistics Authority (PSA)
- **URL:** https://psa.gov.ph/statistics/poverty/stat-tables/released/2023
- **Format:** XLSX
- **Planned Ingestion Method:** Manual File Download
- **Coverage:** Domain level (Provinces & HUCs) poverty incidence for 2018, 2021, and 2023
- **Why it fits the problem:** Measures structural poverty across provinces and serves as one of the primary indicators of opportunity.
- **Known limitations:** Published periodically rather than annually.

---

### Primary Source 2
- **Name:** Family Income and Expenditure Survey (FIES) – Average Annual Family Income
- **Agency:** Philippine Statistics Authority (PSA)
- **URL:** https://psa.gov.ph/statistics/income-expenditure/fies/stat-tables/released/2024
- **Format:** XLSX
- **Planned Ingestion Method:** Manual File Download
- **Coverage:** Domain level (Provinces & HUCs) estimates for 2018, 2021, and 2023
- **Why it fits the problem:** Measures household economic capacity across provinces.
- **Known limitations:** Survey-based estimates; updated every three years.

---

### Primary Source 3
- **Name:** Family Income and Expenditure Survey (FIES) – Average Annual Family Expenditure
- **Agency:** Philippine Statistics Authority (PSA)
- **URL:** https://psa.gov.ph/statistics/income-expenditure/fies/stat-tables/released/2024
- **Format:** XLSX
- **Planned Ingestion Method:** Manual File Download
- **Coverage:** Domain level (Provinces & HUCs) estimates for 2018, 2021, and 2023
- **Why it fits the problem:** Complements income data by capturing household spending patterns.
- **Known limitations:** Survey-based estimates; updated every three years.

---

## Domain 2 — Educational Access

### Primary Source 4
- **Name:** _SY 2025-2026 SCHOOL LEVEL DATA ON ENROLLMENT (BY_SCHOOL_FR)_1
- **Agency:** Department of Education (DepEd)
- **Format:** XLSX
- **Planned Ingestion Method:** Manual File Download (official dataset provided by DepEd through FOI request)
- **Coverage:** School Year 2025–2026 (Latest update: January 17, 2026)
- **Why it fits the problem:** Provides school-level enrollment data that can be aggregated to the domain level (Provinces & HUCs) to derive education access indicators such as schools per capita, enrollment per capita, and public-private school distribution.
- **Known limitations:** Enrollment information is maintained separately from personnel records and therefore requires integration with the personnel dataset.

---

### Primary Source 5
- **Name:** SY 2024-2025 PERSONNEL DATA - TEACHING PERSONNEL BY POSITION TITLE BY SCHOOL
- **Agency:** Department of Education (DepEd)
- **Format:** XLSX
- **Planned Ingestion Method:** Manual File Download (official dataset provided by DepEd through FOI request)
- **Coverage:** Latest available personnel records (Last updated: June 5, 2025)
- **Why it fits the problem:** Provides teaching personnel counts that can be linked to the enrollment dataset through School ID to compute student-to-teacher ratios at the domain level (Provinces & HUCs).
- **Known limitations:** Personnel data is updated independently of enrollment data, resulting in a difference in reporting periods between the two datasets.

---

### Primary Source 6
- **Name:** Higher Education Enrollment and Graduates
- **Agency:** Commission on Higher Education (CHED)
- **Format:** XLSX
- **Planned Ingestion Method:** Manual File Download
- **Coverage:** AY 2025-2026 (Enrollments & Faculty), AY 2024-2025 (Graduates)
- **Why it fits the problem:** Measures accessibility to tertiary education.
- **Known limitations:** Does not measure educational quality or utilization for each institution.

---

## Domain 3 — Healthcare Access

### Primary Source 7
- **Name:** National Health Facility Registry (NHFR) – Provincial Facility Details
- **Agency:** Department of Health (DOH)
- **URL:** https://nhfr.doh.gov.ph/StatHfProvincialList
- **Format:** XLS
- **Planned Ingestion Method:** Manual File Download
- **Coverage:** Licensed hospitals, rural health units, clinics, and other health facilities nationwide by domain level (Provinces & HUCs).
- **Why it fits the problem:** Supports calculation of healthcare facility density and accessibility.
- **Known limitations:** Does not measure service quality or utilization.

---

## Domain 4 — Infrastructure & Accessibility

### Primary Source 8
- **Name:** OpenStreetMap Road Network Graphs
- **Agency:** OpenStreetMap (via OSMnx)
- **Format:** `.graphml` files
- **Planned Ingestion Method:** Automated Script Ingestion (`scripts/ingest.py`)
- **Coverage:** 118 / 118 Target Domains (All 82 Provinces + 36 HUCs)
- **Why it fits the problem:** Enables derivation of road density, intersection connectivity, network length, and transport accessibility indicators.
- **Known limitations:** Large network graph file size; excluded from Git tracking and managed via local data storage.

# Supporting Data Sources

These datasets support multiple domains of the Provincial Opportunity Index by providing denominators for per-capita indicators or enabling spatial analysis.

## Supporting Source 1
- **Name:** Census of Population and Housing (CPH) / Population Estimates
- **Agency:** Philippine Statistics Authority (PSA)
- **URL:** https://psa.gov.ph/statistics/population-and-housing/stat-tables
- **Format:** XLSX
- **Planned Ingestion Method:** Manual File Download
- **Coverage:** Provincial, and Highly Urbanized City population estimates
- **Why it fits the problem:** Provides population counts used to normalize education, healthcare, and higher education indicators into comparable per-capita measures.
- **Known limitations:** Official census occurs every five years; projected population estimates may be used for more recent years.

---

### Supporting Source 2
- **Name:** Philippines Administrative Boundaries (COD-AB)
- **Agency:** Humanitarian Data Exchange (HDX)
- **Provider:** United Nations Office for the Coordination of Humanitarian Affairs (OCHA)
- **URL:** https://data.humdata.org/dataset/cod-ab-phl
- **Format:** Shapefile (SHP)
- **Planned Ingestion Method:** Manual File Download
- **Coverage:** National administrative boundaries (Regions, Provinces, Municipalities, and Barangays)
- **Data Currency:** Last reviewed: April 1, 2024
- **Why it fits the problem:** Provides standardized administrative boundary polygons required for province-level spatial joins, aggregation of indicators, computation of area-based metrics (e.g., road density), and choropleth map visualizations.
- **Known limitations:** Administrative boundaries may be revised over time. The project will document the dataset version used to ensure reproducibility.

---

## Processed Data Plan (Schema Architecture)

This section outlines the schema plan for intermediate spatial features and the processed index output tables.

### 1. Spatial Domain Networks (Graph Artifacts)
- **File Name / Path:** `data/raw/osm/<domain_id>.graphml` (or `data/processed/osm/<domain_id>_network.gpkg`)
- **Grain:** One file per administrative domain (82 Provinces + 36 HUCs = 118 domains)
- **Primary Key:** `domain_id`

#### Important Columns (`edges` layer)
| Column | Meaning | Expected Type |
| :--- | :--- | :--- |
| `u` | Origin intersection node identifier | `Integer` / `String` |
| `v` | Destination intersection node identifier | `Integer` / `String` |
| `key` | Multi-graph edge key (parallel segments) | `Integer` |
| `osmid` | OpenStreetMap segment ID | `Integer` / `List[Integer]` |
| `highway` | Road functional classification (e.g., primary, secondary) | `String` |
| `length` | Physical road segment length in meters | `Float` |
| `geometry` | Spatial vector LineString representation | `Geometry (LineString)` |

---

### 2. Domain Infrastructure & Opportunity Metrics (Intermediate Table)
- **File Name / Path:** `data/processed/domain_infrastructure_metrics.parquet`
- **Grain:** One row = one administrative domain (118 total)
- **Primary Key:** `domain_id`

#### Important Columns
| Column | Meaning | Expected Type |
| :--- | :--- | :--- |
| `domain_id` | Unique standardized domain code | `String` |
| `domain_name` | Official domain name (e.g., "Agusan Del Norte", "City of Butuan") | `String` |
| `domain_type` | Administrative classification (`Province` vs `HUC`) | `String` |
| `total_road_km` | Total drivable road network length in kilometers | `Float` |
| `intersection_density` | Intersections per square kilometer | `Float` |
| `hei_count` | Total CHED-accredited higher education institutions | `Integer` |
| `hei_density_per_100k` | HEI access per 100,000 population | `Float` |

---

### 3. Final Provincial Opportunity Index Output
- **File Name / Path:** `data/processed/provincial_opportunity_index.csv`
- **Grain:** One row = one administrative domain
- **Primary Key:** `domain_id`

#### Important Columns
| Column | Meaning | Expected Type |
| :--- | :--- | :--- |
| `domain_id` | Unique domain identifier | `String` |
| `infra_density_score` | Normalized road network density score (0–100) | `Float` |
| `education_access_score`| Normalized education accessibility score (0–100) | `Float` |
| `poi_score` | Composite Provincial Opportunity Index score (0–100) | `Float` |
| `poi_rank` | National opportunity rank across all 118 domains | `Integer` |
| `updated_at` | Execution run timestamp | `Timestamp` |

---

### Related Tables & Joins
- `domain_infrastructure_metrics` joins to **Philippines Administrative Boundaries (COD-AB)** on `domain_id` for spatial visualization.
- `ched_hei_spatial` spatial-joins onto `domain_infrastructure_metrics` on `domain_id` to aggregate per-capita institutional counts.

---

## Data Source Provenance
For exact raw file paths, source URLs, download timestamps, and manual acquisition rationale for all datasets, see the [`data/DATA_LOG.md`](./data/DATA_LOG.md).

---

## How to Run the Data Ingestion Pipeline

### 1. Prerequisites & Environment Setup
Ensure your environment is active and spatial dependencies are installed:

```bash
# Clone repository
git clone [https://github.com/jimwellbryllsantos-dot/dep-data-engineering-jimwellbryllsantos.git](https://github.com/jimwellbryllsantos-dot/dep-data-engineering-jimwellbryllsantos.git)
cd dep-data-engineering-jimwellbryllsantos

# Create & activate environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1

# Install required spatial packages
pip install -r requirements.txt

---
```

## Possible Final Dashboard


The dashboard will help users quickly understand:


> **Which Philippine provinces and independent cities offer the highest and lowest levels of opportunity, and what structural factors explain these differences.**


### Page 1: National Opportunity Map
- Choropleth map of the Philippines by domain level (Provinces & HUCs)
- Opportunity Index ranking
- Top and bottom provinces highlighted


### Page 2: Opportunity Drivers
- Breakdown of POI by domain:
 - Education
 - Economy
 - Infrastructure
 - Health
- Feature contribution visualization


### Page 3: Provincial Comparison Tool
- Side-by-side comparison of two domains
- Radar/spider chart of indicators
- Rank differences per domain


### Page 4: Inequality Insights
- Distribution of opportunity scores
- Identification of “high poverty, high opportunity” vs “low opportunity traps”
- Regional clustering of opportunity levels


---


## Final Note


This project does not claim that birthplace fully determines life outcomes. Instead, it measures how structural conditions vary across provinces and how those conditions may influence access to opportunity.


The goal is not to predict destiny, but to quantify disparity.