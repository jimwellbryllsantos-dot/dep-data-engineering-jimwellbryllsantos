# Bata, Bata, Saan Ka Nagmula?
# *From Birthplace to Opportunity: Building Provincial Opportunity Index for the Philippines*


## Problem Statement


I want to answer:


> **"To what extent does being born in a specific province in the Philippines influence access to education, economic mobility, and development opportunities?"**


More specifically, this project aims to:


> **"Construct a Provincial Opportunity Index that quantifies and compares opportunity levels across Philippine provinces using measurable indicators of education, economic conditions, infrastructure, healthcare access, and digital connectivity."**


The Philippines exhibits persistent regional inequality, where provinces differ significantly in income levels, infrastructure availability, and access to public services. While poverty statistics are widely used, they do not fully capture the broader concept of “opportunity” — defined here as the structural conditions that enable upward mobility.


This project addresses that gap by building a composite, data-driven index to measure and compare opportunity across provinces using publicly available datasets.


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


The **Provincial Opportunity Index (POI)** is a composite score (0–100) representing the relative level of opportunity available within each province.


It is constructed from normalized indicators across five domains:


### 1. Economic Conditions
- Poverty incidence
- Average household income (or proxy indicators where limited)
- Employment rate


### 2. Educational Access
- Number of schools per capita
- Student-to-school ratio (where available)
- Literacy-related proxies (if available)


### 3. Healthcare Access
- Number of health facilities per capita
- Accessibility of hospitals/health centers


### 4. Infrastructure & Accessibility
- Road density (OpenStreetMap-derived)
- Distance to regional economic centers
- Urbanization level (proxy indicators)


### 5. Digital Connectivity (Proxy-Based)
- Population density as proxy for digital infrastructure access
- Available ICT penetration indicators (where accessible from public reports)


### Composite Construction Approach
- Min-max normalization of each indicator
- Weighted aggregation (initially equal weighting, subject to sensitivity testing)
- Optional PCA-based weighting for robustness comparison


---


## Data Source Notes

The Provincial Opportunity Index (POI) is constructed by integrating multiple authoritative government datasets. Each domain of the index is supported by one or more primary data sources. Where official datasets are pending approval or acquisition, fallback sources are identified to ensure project continuity.

---

## Domain 1 — Economic Conditions

### Primary Source 1
- **Status:** ✅ Confirmed
- **Name:** 2023 Official Poverty Statistics – Poverty Incidence Among Population by Region and Province
- **Agency:** Philippine Statistics Authority (PSA)
- **URL:** https://psa.gov.ph/statistics/poverty/stat-tables/released/2023
- **Format:** XLSX
- **Coverage:** Provincial-level poverty incidence for 2018, 2021, and 2023
- **Why it fits the problem:** Measures structural poverty across provinces and serves as one of the primary indicators of opportunity.
- **Known limitations:** Published periodically rather than annually.

---

### Primary Source 2
- **Status:** ✅ Confirmed
- **Name:** Family Income and Expenditure Survey (FIES) – Average Annual Family Income
- **Agency:** Philippine Statistics Authority (PSA)
- **URL:** https://psa.gov.ph/statistics/income-expenditure/fies/stat-tables/released/2024
- **Format:** XLSX
- **Coverage:** Provincial estimates for 2018, 2021, and 2023
- **Why it fits the problem:** Measures household economic capacity across provinces.
- **Known limitations:** Survey-based estimates; updated every three years.

---

### Primary Source 3
- **Status:** ✅ Confirmed
- **Name:** Family Income and Expenditure Survey (FIES) – Average Annual Family Expenditure
- **Agency:** Philippine Statistics Authority (PSA)
- **URL:** https://psa.gov.ph/statistics/income-expenditure/fies/stat-tables/released/2024
- **Format:** XLSX
- **Coverage:** Provincial estimates for 2018, 2021, and 2023
- **Why it fits the problem:** Complements income data by capturing household spending patterns.
- **Known limitations:** Survey-based estimates; updated every three years.

---

## Domain 2 — Educational Access

### Primary Source 4
- **Status:** 🟡 Pending FOI Request
- **Name:** Basic Education Information System (BEIS) School-Level Masterlist
- **Agency:** Department of Education (DepEd)
- **Format:** CSV / XLSX (Requested)
- **Coverage:** Latest finalized school year (preferably SY 2025–2026)
- **Requested Variables:**
  - School ID
  - School Name
  - Region
  - Province
  - City/Municipality
  - Public/Private Classification
  - School Level
  - School Status
  - Total Enrollment
  - Number of Teaching Personnel
- **Why it fits the problem:** Enables computation of schools per capita, enrollment per capita, and student-to-teacher ratios.
- **Known limitations:** Subject to FOI approval.

### Fallback Source
- **Name:** DepEd Regional/Division School Masterlists or BEIS Public Directory
- **Format:** XLSX / HTML
- **Coverage:** Regional or division-level school listings
- **Why it could still work:** School counts can be consolidated into a nationwide dataset if the FOI request is unsuccessful.
- **Known limitations:** Requires extensive consolidation and standardization.

---

### Primary Source 5
- **Status:** 🟡 Pending FOI Request
- **Name:** Directory of Higher Education Institutions (HEIs)
- **Agency:** Commission on Higher Education (CHED)
- **Format:** CSV / XLSX (Requested)
- **Coverage:** Latest finalized academic year
- **Requested Variables:**
  - HEI ID
  - Institution Name
  - Province
  - Region
  - City/Municipality
  - Public/Private Classification
  - Institution Type
  - Operational Status
  - Total Enrollment (if available)
  - Total Faculty (if available)
- **Why it fits the problem:** Measures accessibility to tertiary education.
- **Known limitations:** Enrollment and faculty information may not be included in the standard directory.

### Fallback Source
- **Name:** CHED Public Directory of Higher Education Institutions
- **URL:** https://ched.gov.ph/list-of-higher-education-institutions/
- **Format:** HTML
- **Coverage:** Nationwide
- **Why it could still work:** Provides an official list of HEIs that can be scraped and aggregated by province.
- **Known limitations:** May not include enrollment or faculty statistics.

---

## Domain 3 — Healthcare Access

### Primary Source 6
- **Status:** ✅ Confirmed
- **Name:** National Health Facility Registry (NHFR) – Provincial Facility Details
- **Agency:** Department of Health (DOH)
- **URL:** https://nhfr.doh.gov.ph/StatHfProvincialList
- **Format:** CSV / XLSX
- **Coverage:** Licensed hospitals, rural health units, clinics, and other health facilities nationwide
- **Why it fits the problem:** Supports calculation of healthcare facility density and accessibility.
- **Known limitations:** Does not measure service quality or utilization.

---

## Domain 4 — Infrastructure & Accessibility

### Primary Source 7
- **Status:** 🔵 To Be Sourced
- **Name:** OpenStreetMap Road Network
- **Agency:** OpenStreetMap
- **Format:** PBF / SHP / GeoJSON
- **Coverage:** Nationwide
- **Why it fits the problem:** Enables derivation of road density and transportation accessibility indicators.
- **Known limitations:** Community-maintained dataset with varying completeness across locations.

### Primary Source 8
- **Status:** 🔵 To Be Sourced
- **Name:** Philippine Administrative Boundary Shapefiles
- **Agency:** PSA / NAMRIA
- **Format:** SHP / GeoJSON
- **Coverage:** Provincial administrative boundaries
- **Why it fits the problem:** Required for spatial joins and choropleth mapping.
- **Known limitations:** Boundary revisions should be documented.

### Fallback Source
- **Name:** GADM Administrative Areas
- **URL:** https://gadm.org
- **Format:** SHP / GeoPackage
- **Coverage:** Global administrative boundaries
- **Why it could still work:** Widely used alternative for GIS analyses.
- **Known limitations:** May lag behind official Philippine administrative updates.

---

## Domain 5 — Digital Connectivity (Optional)

**Status:** ⚪ Planned for Future Enhancement

Digital connectivity indicators are currently under evaluation. Reliable province-level public datasets are being assessed for inclusion in a future iteration of the Provincial Opportunity Index.

Potential sources include:
- Department of Information and Communications Technology (DICT)
- National Telecommunications Commission (NTC)
- PSA ICT-related indicators (where available)

# Supporting Data Sources

These datasets support multiple domains of the Provincial Opportunity Index by providing denominators for per-capita indicators or enabling spatial analysis.

## Supporting Source 1

- **Status:** ✅ Confirmed
- **Name:** Census of Population and Housing (CPH) / Population Estimates
- **Agency:** Philippine Statistics Authority (PSA)
- **URL:** https://psa.gov.ph/statistics/population-and-housing/stat-tables
- **Format:** XLSX
- **Coverage:** National, regional, provincial, and Highly Urbanized City population estimates
- **Why it fits the problem:** Provides population counts used to normalize education, healthcare, and higher education indicators into comparable per-capita measures.
- **Known limitations:** Official census occurs every five years; projected population estimates may be used for more recent years.

---

## Supporting Source 2

- **Status:** 🔵 To Be Sourced
- **Name:** Philippine Administrative Boundary Shapefiles
- **Agency:** PSA / NAMRIA
- **Format:** SHP / GeoJSON
- **Coverage:** Provincial administrative boundaries
- **Why it fits the problem:** Enables province-level aggregation, spatial joins, and choropleth visualizations.
- **Known limitations:** Administrative boundary revisions should be documented.

### Fallback Source

- **Name:** GADM Administrative Areas
- **URL:** https://gadm.org
- **Format:** SHP / GeoPackage
- **Coverage:** Global administrative boundaries
- **Why it could still work:** Widely used alternative for GIS analyses when official boundary files are unavailable.
- **Known limitations:** May lag behind official Philippine administrative updates.

---


## Possible Final Dashboard


The dashboard will help users quickly understand:


> **Which Philippine provinces offer the highest and lowest levels of opportunity, and what structural factors explain these differences.**


### Page 1: National Opportunity Map
- Choropleth map of the Philippines by province
- Opportunity Index ranking
- Top and bottom provinces highlighted


### Page 2: Opportunity Drivers
- Breakdown of POI by domain:
 - Education
 - Economy
 - Infrastructure
 - Health
 - Connectivity
- Feature contribution visualization


### Page 3: Provincial Comparison Tool
- Side-by-side comparison of two provinces
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