# Data Ingestion Log & File Provenance

This document tracks all manual file downloads, raw file locations, source URLs, and acquisition rationale for the **Provincial Opportunity Index (POI)** project.

---

## Domain 1 — Economic Conditions

### 1. PSA FIES Average Family Income
* **Saved file:** `data/raw/Table 1. 2018, 2021 and 2023p Average Annual Family Income, by Per Capita Income Decile Class and by Region, Province and HUCs_2026-07-10.xlsx`
* **Source URL:** https://psa.gov.ph/statistics/income-expenditure/fies/stat-tables/released/2024
* **Downloaded on:** 2026-07-10
* **Notes:** Manual download was required because the triennial Family Income and Expenditure Survey (FIES) datasets are distributed as static Excel tables on the official PSA web portal.

### 2. PSA FIES Average Family Expenditure
* **Saved file:** `data/raw/Table 2. 2018, 2021 and 2023p Average Annual Family Expenditure, by Per Capita Income Decile Class and by Region, Province and HUC_2026-07-10.xlsx`
* **Source URL:** https://psa.gov.ph/statistics/income-expenditure/fies/stat-tables/released/2024
* **Downloaded on:** 2026-07-10
* **Notes:** Manual download was required as expenditure tables are hosted as static Excel downloads on the PSA portal alongside the FIES income tables.

---

## Domain 2 — Educational Access

### 3. DepEd SY 2025–2026 School Level Enrollment Data
* **Saved file:** `data/raw/_SY 2025-2026 SCHOOL LEVEL DATA ON ENROLLMENT (BY_SCHOOL_FR)_1_2026-07-27.xlsx`
* **Source URL:** Provided directly via official DepEd Freedom of Information (FOI) portal request
* **Downloaded on:** 2026-07-27
* **Notes:** Manual download was necessary because school-level enrollment microdata is restricted from direct web scraping and must be retrieved through an official government FOI request payload.

### 4. DepEd SY 2024–2025 Teaching Personnel Data
* **Saved file:** `data/raw/SY 2024-2025 PERSONNEL DATA - TEACHING PERSONNEL BY POSITION TITLE BY SCHOOL_2026-07-27.xlsx`
* **Source URL:** Provided directly via official DepEd Freedom of Information (FOI) portal request
* **Downloaded on:** 2025-07-27
* **Notes:** Manual download was necessary as public school personnel distribution spreadsheets are distributed on request via the FOI mechanism separately from enrollment records.

---

## Domain 3 — Healthcare Access

### 5. DOH National Health Facility Registry (NHFR)
* **Saved file:** `data/raw/Stat_HFProvincial_2026-07-11.xls`
* **Source URL:** https://nhfr.doh.gov.ph/StatHfProvincialList
* **Downloaded on:** 2026-07-11
* **Notes:** Manual export was necessary because the DOH NHFR portal generates static file downloads per user request session rather than offering a programmatic database connection endpoint.

---

## Supporting Data Sources

### 7. PSA Census of Population and Housing (CPH) / Population Estimates
* **Saved file:** `data/raw/Total Population - Philippines 2024_2026-07-11.xlsx`
* **Source URL:** https://psa.gov.ph/statistics/population-and-housing/stat-tables
* **Downloaded on:** 2026-07-11
* **Notes:** Manual file download was required as national census counts and official population projections are hosted as static tabular datasets on the PSA statistical portal.

### 8. HDX Philippines Administrative Boundaries (COD-AB)
* **Saved file:** `data/raw/shape/phl_admbnda_adm3_psa_namria_20231106_2023-11-08.shp`
* **Source URL:** https://data.humdata.org/dataset/cod-ab-phl
* **Downloaded on:** 2023-11-08
* **Notes:** Manual download was required to acquire and archive the specific, version-controlled shapefile bundle published by UN OCHA on the Humanitarian Data Exchange.