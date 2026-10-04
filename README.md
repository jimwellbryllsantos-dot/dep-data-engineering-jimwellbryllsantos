# Bata, Bata, Saan Ka Nagmula?
## *From Birthplace to Opportunity: Building Provincial Opportunity Index for the Philippines*

> **Project purpose:** Build a data-driven, domain-level measure of structural opportunity across Philippine provinces, Highly Urbanized Cities (HUCs), and Independent Component Cities (ICCs).

---

## 1. Project Overview

This project asks:

> **To what extent do structural conditions in a person's province or urban center affect access to education, economic resources, healthcare, and physical infrastructure?**

The project operationalizes this question through a **Provincial Opportunity Index (POI)** that compares opportunity-related conditions across **119 administrative domains**:

- Provinces, Highly Urbanized Cities (HUCs), and Independent Component Cities (ICCs)

The project treats HUCs and ICCs as separate analytical domains where required. This prevents highly urbanized or independently administered centers from being absorbed into their parent provinces and skewing province-level measures.

### Current implemented dimensions

The current codebase computes four dimensions:

| Dimension | Main indicators currently used in the index |
|---|---|
| **Economic Conditions** | Per-capita income, poverty incidence, per-capita expenditure |
| **Educational Access** | Basic education school density, schools per capita, basic student-teacher ratio, higher education institution density, HEIs per capita, higher education student-faculty ratio, higher education graduates per capita |
| **Healthcare Access** | Hospital density, hospitals per capita, primary-health facility density, primary-health facilities per capita |
| **Infrastructure & Accessibility** | Road density, road network per capita, primary-road ratio, bridge density, average road-segment length |

The current implementation **does not yet include** a digital-connectivity index component or an employment-rate indicator, even though these appeared in the earlier project concept.

---

## 2. Audience

This project is intended for users who need a structured, evidence-based view of differences in economic conditions and access to public-service resources across Philippine administrative domains.

### Primary Audience

- **Policy makers and government planning agencies**, including organizations involved in national and local development planning, social protection, education, health, and infrastructure policy
- **Development organizations and NGOs** working on poverty reduction, regional development, and public-service access
- **Academic and policy researchers** in statistics, economics, geography, public policy, and related fields

### Secondary Audience

- **Private-sector organizations** evaluating regional expansion, market opportunities, logistics, telecommunications, and service coverage
- **Data analysts and data engineers** interested in geospatial, socioeconomic, and public-sector data integration
- **Students and professionals** exploring composite indicators, statistical modeling, and data-driven policymaking

The intended use is to support **comparative analysis and evidence-informed discussion**. The POI is not intended to replace official government statistics, program-specific indicators, or detailed local policy analysis.

---

## 3. Current Pipeline Architecture

The pipeline is organized as a sequential set of scripts. Each step produces an artifact consumed by the next step.

```text
Raw administrative boundaries
        |
        v
[01] Create master domains
        |
        +------------------------------+
        |                              |
        v                              v
[02] OSM road extraction        [03] Clean & stage government datasets
        |                              |
        |                              +--> population
        |                              +--> basic education
        |                              +--> teaching personnel
        |                              +--> income
        |                              +--> expenditure
        |                              +--> poverty
        |                              +--> higher education
        |                              +--> health facilities
        |                              |
        v                              v
GraphML files                Parquet staging datasets
        |                              |
        v                              |
[04] Infrastructure summarization -----+
                       |
                       v
              [05] Master dataset
                       |
             master_dataset.parquet
                       |
             +---------+---------+
             |                   |
             v                   v
 [06a] Min-Max approach   [06b] Rank-based approach
             |                   |
             v                   v
 analytical_master_      analytical_master_
 dataset_minmax.*        dataset_rank.*
```

### Processing principle

The pipeline follows a **master-domain-first** design:

1. Administrative boundaries define the authoritative set of analytical domains.
2. Every source dataset is cleaned and mapped to those domain names.
3. Source-specific data are stored as domain-level staging tables.
4. Staged data are merged onto the master domain list.
5. Spatial-density and per-capita indicators are engineered from the consolidated dataset.
6. The resulting master dataset is passed into either of two index-construction methods.

---

## 4. Repository Structure

The scripts assume a repository layout similar to:

```text
project-root/
├── scripts/
│   ├── 01_create_domains.py
│   ├── 02_ingest.py
│   ├── 03_clean_datasets.py
│   ├── 04_infrastructure.py
│   ├── 05_transform.py
│   ├── 06a_compute_index_min-max_approach.py
│   └── 06b_compute_index_rank-based_approach.py
│
├── data/
│   ├── raw/
│   │   ├── *.xlsx / *.xls
│   │   ├── shape/
│   │   ├── osm/
│   │   └── osm_overpass_cache/
│   │
│   └── processed/
│       ├── Domains.shp
│       ├── staging/
│       └── final/
│
├── requirements.txt
└── README.md
```

The exact script location can be adjusted, but the scripts use paths relative to the repository structure described above.

If you are setting up from Git for the first time:

```bash
git clone https://github.com/jimwellbryllsantos-dot/dep-data-engineering-jimwellbryllsantos.git
cd dep-data-engineering-jimwellbryllsantos
```

---

## 5. Prerequisites

### Python

Use a Python virtual environment recommended for the project.

```bash
python -m venv venv
```

Activate it before running the pipeline.

**Windows PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
source venv/bin/activate
```

Install dependencies from the project requirements file:

```bash
pip install -r requirements.txt
```

The current scripts rely on libraries including:

- `pandas`
- `numpy`
- `geopandas`
- `networkx`
- `osmnx`
- `xlrd`
- a Parquet engine such as `pyarrow`

The scripts also rely on Excel-reading support through pandas for `.xlsx` inputs.

---

## 6. Required Raw Inputs

Place the source files under `data/raw/` using the filenames currently expected by `03_clean_datasets.py`.

| Source | Expected local filename | Output staging file |
|---|---|---|
| PSA population | `Total Population - Philippines 2024_2026-07-11.xlsx` | `staging_population.parquet` |
| DepEd basic education enrollment | `_SY 2025-2026 SCHOOL LEVEL DATA ON ENROLLMENT (BY_SCHOOL_FR)_1_2026-07-27.xlsx` | `staging_education_basic.parquet` |
| DepEd teaching personnel | `SY 2024-2025 PERSONNEL DATA - TEACHING PERSONNEL BY POSITION TITLE BY SCHOOL_2026-07-27.xlsx` | `staging_education_personnel.parquet` |
| PSA family income | `Table 1. 2018, 2021 and 2023p Average Annual Family Income, by Per Capita Income Decile Class and by Region, Province and HUCs_2026-07-10.xlsx` | `staging_income.parquet` |
| PSA family expenditure | `Table 2. 2018, 2021 and 2023p Average Annual Family Expenditure, by Per Capita Income Decile Class and by Region, Province and HUC_2026-07-10.xlsx` | `staging_expenditure.parquet` |
| PSA poverty statistics | `2023 Full Year Official Poverty Statistics_r2_2026-07-10.xlsx` | `staging_poverty.parquet` |
| CHED higher education | `Higher Education Enrollment and Graduates.xlsx` | `staging_higher_education.parquet` |
| DOH health facilities | `Stat_HFProvincial_2026-07-11.xls` | `staging_health.parquet` |
| Administrative boundaries | `data/raw/shape/phl_admbnda_adm3_psa_namria_20231106_2023-11-08.shp` | `data/processed/Domains.shp` |

### Important

The filenames above are **hard-coded in the current scripts**. Updating a raw file name requires either renaming the file or changing the corresponding script configuration.

The administrative-boundary source is read by `01_create_domains.py`, which maps municipality and province records into the project's master domains before dissolving the geometries into domain-level polygons.

---

## 7. How to Run the Full Pipeline

Run the scripts from the repository root in the following order.

```bash
python scripts/01_create_domains.py
python scripts/02_ingest.py
python scripts/03_clean_datasets.py
python scripts/04_infrastructure.py
python scripts/05_transform.py
python scripts/06a_compute_index_min-max_approach.py
```

Use `06b` instead of `06a` when you want the rank-based index output:

```bash
python scripts/06b_compute_index_rank-based_approach.py
```

You can run **both 06a and 06b** because they write to different output files.

---

# 7. Run the Pipeline Flow-by-Flow

This section is intended for debugging, partial reruns, and development work.

## Flow 1 — Create Master Domains

```bash
python scripts/01_create_domains.py
```

### What it does

- Reads the ADM3 shapefile.
- Maps municipalities/cities into the project's HUC/independent-city domains.
- Maps provinces into province-level domains while explicitly excluding HUCs where required.
- Uses aliases to handle naming variations.
- Dissolves ADM3 geometries by the resulting `DOMAIN` field.

### Main output

```text
data/processed/Domains.shp
```

This shapefile becomes the geographic reference used by later stages.

---

## Flow 2 — Ingest OSM Road Networks

```bash
python scripts/02_ingest.py
```

### What it does

- Loads the master domain polygons.
- Ensures geometries are in **EPSG:4326 (WGS 84)** before querying OSMnx.
- Extracts **driving networks** using OSMnx and the Overpass API.
- Saves one GraphML file per domain.
- Keeps `retain_all=True`.
- Uses retry logic with up to 3 attempts and a 120-second delay between failed attempts.
- Uses OSMnx caching for raw API responses.
- Skips an already-existing GraphML file, allowing the ingestion to resume without re-downloading completed domains.

### Main outputs

```text
data/raw/osm/<domain_name>.graphml
data/raw/osm_overpass_cache/
```

### Resume behavior

A domain is treated as already completed when its expected GraphML file exists. This means the script can be rerun after an interruption and will skip completed domains.

### Operational note

This is the most network-dependent stage. Large provincial polygons can take substantially longer to process than individual HUCs, and Overpass availability can affect runtime.

---

## Flow 3 — Clean and Stage Government Datasets

```bash
python scripts/03_clean_datasets.py
```

This script performs **eight** dataset-specific cleaning jobs in one run.

### Execution order inside the script

```text
1. Population
2. DepEd basic education enrollment
3. DepEd teaching personnel
4. PSA income
5. PSA expenditure
6. PSA poverty
7. CHED higher education
8. DOH health facilities
```

### Outputs

```text
data/processed/staging/staging_population.parquet
data/processed/staging/staging_education_basic.parquet
data/processed/staging/staging_education_personnel.parquet
data/processed/staging/staging_income.parquet
data/processed/staging/staging_expenditure.parquet
data/processed/staging/staging_poverty.parquet
data/processed/staging/staging_higher_education.parquet
data/processed/staging/staging_health.parquet
```

### Main cleaning behavior

The cleaning stage generally follows the same pattern:

```text
Raw source
   -> identify relevant rows/columns
   -> clean numeric values
   -> standardize geographic names
   -> map to master-domain names
   -> aggregate to domain level
   -> write Parquet staging table
```

### Geographic reconciliation

The script uses a shared domain map plus explicit aliases to resolve naming differences across datasets. It contains special handling for cases such as:

- Manila subdistrict/division names
- HUC naming variants
- Lapu-Lapu / Opon
- Isabela City versus Isabela province
- Cotabato / North Cotabato / Special Geographic Area
- Maguindanao del Norte / del Sur mappings
- Provinces reported with “without” or “excluding” HUC language

The population cleaning stage also contains a specific **Cotabato City / Maguindanao del Norte decoupling adjustment** so that the two analytical domains remain separate.

---

## Flow 4 — Convert OSM Graphs to Infrastructure Metrics

```bash
python scripts/04_infrastructure.py
```

### What it does

For every domain in the master shapefile, the script:

- looks for its corresponding GraphML file;
- reads the graph using OSMnx when available, otherwise NetworkX;
- counts nodes and edges;
- sums road-segment length;
- counts bridges;
- groups road length into standardized highway classes.

Current road categories include:

- primary
- secondary
- tertiary
- trunk/motorway
- residential
- other

### Main output

```text
data/processed/staging/staging_infrastructure.parquet
```

### Missing GraphML behavior

If a domain has no GraphML file, the script does **not** fail the entire stage. It writes zero-valued infrastructure metrics for that domain.

This makes the pipeline resilient to partial OSM extraction, but it also means missing OSM data can propagate as zeros into downstream indicators.

---

## Flow 5 — Build the Master Dataset

```bash
python scripts/05_transform.py
```

### What it does

1. Loads the master domain shapefile.
2. Calculates domain land area in square kilometers from geometry.
3. Loads the available staging Parquet files.
4. Left-merges them onto the master domain list using `clean_domain`.
5. Computes per-capita and spatial-density indicators.
6. Standardizes numeric data types.
7. Performs validation checks.
8. Exports the consolidated analytical dataset.

### Main outputs

```text
data/processed/final/master_dataset.parquet
data/processed/final/master_dataset.csv
```

### Derived indicators currently created

#### Infrastructure

- road kilometers per 100,000 population
- primary-road ratio
- bridges per 100,000 population
- road kilometers per square kilometer
- bridges per 100 square kilometers

#### Basic education

- total teachers
- total enrollment
- total schools
- schools per 100,000 population
- schools per 10 square kilometers
- student-teacher ratio

#### Higher education

- HEI count
- faculty count
- enrollment
- graduates
- HEIs per 100,000 population
- HEIs per 100 square kilometers
- student-faculty ratio
- graduates per 100,000 population

#### Healthcare

- primary-care facility total
- total health facilities
- primary-health facilities per 100,000 population
- hospitals per 100,000 population
- primary-health facilities per 100 square kilometers
- hospitals per 100 square kilometers

### Validation checks

The current script checks:

- master-domain row count versus final row count;
- uniqueness of `clean_domain`;
- non-positive land area;
- infinite numeric values.

A failed validation condition causes the script to exit with status 1 after writing the output files.

---

# 8. Compute the Opportunity Index

There are currently **two alternative index-construction scripts**. Both use the same master dataset, indicator set, sector weights, and overall dimension weights. They differ only in the normalization method.

## 9.1 Min-Max Approach

```bash
python scripts/06a_compute_index_min-max_approach.py
```

Normalization:

\[
X' = \frac{X - X_{min}}{X_{max} - X_{min}}
\]

The lowest observed value becomes 0 and the highest becomes 1. Indicators where lower values are better are inverted.

For an indicator with only one unique value, the script assigns a normalized value of **0.5**.

### Output

```text
data/processed/final/analytical_master_dataset_minmax.parquet
data/processed/final/analytical_master_dataset_minmax.csv
```

---

## 9.2 Rank-Based Approach

```bash
python scripts/06b_compute_index_rank-based_approach.py
```

This method converts indicators to percentile-style rank scores before aggregation.

The implementation uses:

```python
series.rank(ascending=True, method="average")
```

and scales the resulting ranks to the 0–1 interval. Indicators where lower values are better are inverted.

This approach is intended to reduce the influence of very large numerical outliers or highly skewed indicators on the resulting score.

For an indicator with only one unique value, the script assigns a normalized value of **0.5**.

### Output

```text
data/processed/final/analytical_master_dataset_rank.parquet
data/processed/final/analytical_master_dataset_rank.csv
```

---

## 10. Current Index Output Fields

The analytical index files currently contain the domain identifiers, four sector scores, the overall composite score, and corresponding ranks. The main composite field is:

```text
overall_composite_score
```

Rank fields currently include:

```text
rank_infrastructure
rank_economic
rank_education
rank_health
rank_overall
```

The output is sorted by `rank_overall`.

---

## 11. Current Index Weighting

The current implementation uses four sector scores and an overall weighted composite.

### Infrastructure sub-index

| Indicator | Weight |
|---|---:|
| Road density per square kilometer | 25% |
| Road density per capita | 20% |
| Primary-road ratio | 25% |
| Bridge density | 15% |
| Average segment length, inverse | 15% |

### Economic sub-index

| Indicator | Weight |
|---|---:|
| Per-capita income | 60% |
| Poverty incidence, inverse | 20% |
| Per-capita expenditure | 20% |

### Education sub-index

| Indicator | Weight |
|---|---:|
| Basic student-teacher ratio, inverse | 25% |
| Basic schools per square kilometer | 15% |
| Basic schools per capita | 10% |
| HEIs per square kilometer | 10% |
| HEIs per capita | 15% |
| Higher-education student-faculty ratio, inverse | 15% |
| Higher-education graduates per capita | 10% |

### Health sub-index

| Indicator | Weight |
|---|---:|
| Hospitals per square kilometer | 30% |
| Hospitals per capita | 30% |
| Primary-health facilities per square kilometer | 20% |
| Primary-health facilities per capita | 20% |

### Overall composite score

```text
Overall Score =
    25% Infrastructure
  + 40% Economic
  + 25% Education
  + 10% Health
```

Each sub-index is expressed on a **0–100 scale**, and the overall score is also on a 0–100 scale.

The current ranking implementation defines **Rank 1 as the highest score / best relative performance**.

---

## 12. Interpretation of the Score

The current index is a **relative composite measure**, not a probability, causal estimate, or prediction of an individual's future outcome.

A higher score means that, relative to the other domains included in the same run, the domain has stronger observed values on the indicators and weights used by the model.

Because both normalization methods depend on the observed cross-domain distribution, index values should be interpreted together with:

- the underlying indicators;
- the sector-level scores;
- the selected normalization method;
- the reporting period of each source dataset.

The index should therefore be used as a structured comparison tool rather than as a direct measure of individual human mobility or life outcomes.

---

## 13. Handling Missing Inputs and Missing Data

There are several deliberate resilience mechanisms in the current scripts.

### Missing staging file in Flow 5

`05_transform.py` warns and skips a missing staging file rather than stopping the entire merge process.

### Missing indicator column in Flow 6

The index scripts use `_get_series()`. When none of the candidate column names exists, the function returns zeros for that indicator.

### Missing OSM graph in Flow 4

Missing GraphML files result in zero infrastructure metrics for the affected domain.

These behaviors make partial reruns easier, but they also create an important analytical consideration:

> **A zero-valued indicator may represent either a true zero or missing source data, depending on the upstream stage.**

For policy interpretation, missingness should therefore be distinguished from actual absence of a facility/resource whenever the data permit.

---

## 14. Data Sources

### Economic Conditions

**PSA Official Poverty Statistics**  
Used for the 2023 family poverty incidence measure and poverty threshold.

**PSA Family Income and Expenditure Survey (FIES)**  
Used for the income and expenditure components. The current cleaning scripts select the 2023 values from the supplied 2018/2021/2023 tables.

### Educational Access

**Department of Education (DepEd)**  
School-level enrollment data are aggregated to domain level. Teaching personnel data are separately aggregated and later combined with enrollment to derive the basic student-teacher ratio.

**Commission on Higher Education (CHED)**  
Higher education enrollment, graduates, faculty, and HEI counts are aggregated to domain level.

### Healthcare Access

**Department of Health (DOH) / National Health Facility Registry**  
Facility counts are aggregated to domain level and grouped into primary-care and hospital/infirmary-related measures.

### Infrastructure

**OpenStreetMap via OSMnx / Overpass API**  
Used to build domain-level driving-network GraphML files and derive road and bridge metrics.

### Spatial reference / administrative domains

The current domain-generation stage reads the supplied administrative boundary shapefile, maps ADM3 records to the project's project-defined domain structure, and dissolves them into domain polygons.

For source URLs, download details, timestamps, and provenance notes, retain the project's separate data-log documentation where applicable.

---

## 15. Geographic Standardization and Policy-Relevant Design Choices

The geographic crosswalk is one of the most important parts of this project because public datasets do not consistently use the same labels for Philippine provinces, cities, HUCs, and special administrative areas.

The current implementation explicitly handles:

- HUC separation from parent provinces;
- alternative city naming conventions;
- spelling and punctuation variants;
- Manila administrative subdistrict references;
- Cotabato and Special Geographic Area naming differences;
- Maguindanao provincial restructuring/split handling;
- source-specific “without HUC” / “excluding HUC” labels.

This is not merely a formatting step. It determines the unit to which statistics are ultimately assigned, so changes to the crosswalk can materially change the final index.

---

## 16. Recommended Run Modes

### Full rebuild

Use all stages when the administrative boundaries or raw source files have changed materially:

```bash
python scripts/01_create_domains.py
python scripts/02_ingest.py
python scripts/03_clean_datasets.py
python scripts/04_infrastructure.py
python scripts/05_transform.py
python scripts/06a_compute_index_min-max_approach.py
python scripts/06b_compute_index_rank-based_approach.py
```

### Rebuild from government datasets only

Use this when raw statistical files changed but OSM networks did not:

```bash
python scripts/03_clean_datasets.py
python scripts/04_infrastructure.py
python scripts/05_transform.py
python scripts/06a_compute_index_min-max_approach.py
```

The infrastructure step is still included because `05_transform.py` expects `staging_infrastructure.parquet` alongside the other staging tables.

### Recompute only the index

Use this when the master dataset is unchanged and you only want to compare normalization methods:

```bash
python scripts/06a_compute_index_min-max_approach.py
python scripts/06b_compute_index_rank-based_approach.py
```

---

## 17. Final Data Products & Schema Architecture

The pipeline is organized into four practical data layers: **spatial reference**, **staging datasets**, the **consolidated master dataset**, and the **final analytical index outputs**.

### 16.1 Spatial Reference Layer

**Primary artifact:**

```text
data/processed/Domains.shp
```

- **Grain:** One geometry per project-defined administrative domain
- **Current scope:** 119 domains, including provinces, HUCs, selected ICCs, and other project-defined domains
- **Primary join key:** `clean_domain` in downstream processed datasets
- **Purpose:** Authoritative spatial/domain reference for the rest of the pipeline

`01_create_domains.py` builds this layer by mapping ADM3 administrative records into the project's domain definitions and dissolving the resulting geometries by `DOMAIN`.

### 16.2 Raw OSM Network Layer

**Location:**

```text
data/raw/osm/<domain_name>.graphml
data/raw/osm_overpass_cache/
```

- **Grain:** One road-network graph per domain
- **Network type:** Driving network (`drive`)
- **Source:** OpenStreetMap through OSMnx / Overpass
- **Purpose:** Preserve the network-level source artifact before conversion into domain-level infrastructure indicators

The GraphML files contain graph nodes and road-segment edges. The current infrastructure stage uses node count, edge count, segment length, bridge tags, and highway classification to produce domain-level metrics.

### 16.3 Domain-Level Staging Layer

**Location:**

```text
data/processed/staging/
```

Each staging table has **one row per mapped domain** (subject to source coverage) and uses `clean_domain` as the common join key.

| Staging file | Main content | Typical key fields / metrics |
|---|---|---|
| `staging_population.parquet` | PSA population and household measures | `clean_domain`, `total_population`, `household_population`, `number_of_households`, `avg_household_size` |
| `staging_education_basic.parquet` | DepEd school-level enrollment aggregation | `clean_domain`, `total_schools`, `public_schools`, `private_schools`, `total_enrollment` |
| `staging_education_personnel.parquet` | DepEd teaching personnel aggregation | `clean_domain` plus teacher-position counts |
| `staging_income.parquet` | PSA 2023 family-income measures | `clean_domain` plus standardized 2023 income fields from the source table |
| `staging_expenditure.parquet` | PSA 2023 family-expenditure measures | `clean_domain` plus standardized 2023 expenditure fields from the source table |
| `staging_poverty.parquet` | PSA poverty measures | `clean_domain`, `poverty_threshold_2023`, `family_poverty_incidence_2023_pct` |
| `staging_higher_education.parquet` | CHED HEI aggregation | `clean_domain`, `higher_ed_enrolment`, `higher_ed_graduates`, `higher_ed_faculty`, `total_heis` |
| `staging_health.parquet` | DOH facility aggregation | `clean_domain` plus source facility-count fields prefixed with `health_` |
| `staging_infrastructure.parquet` | OSM-derived road/bridge metrics | `clean_domain`, `osm_nodes_count`, `osm_edges_count`, `osm_total_road_km`, bridge and road-class metrics |

The staging layer intentionally keeps source-specific measures separate so that individual cleaning/aggregation logic can be debugged without rebuilding the entire consolidated dataset.

### 16.4 Consolidated Master Dataset

**Files:**

```text
data/processed/final/master_dataset.parquet
data/processed/final/master_dataset.csv
```

- **Grain:** One row per project-defined domain
- **Current target grain:** 119 domains
- **Primary analytical key:** `clean_domain`
- **Spatial measure:** `land_area_sqkm`

The master dataset is created in `05_transform.py` by:

```text
master domain list
      + population staging
      + education staging
      + personnel staging
      + income staging
      + expenditure staging
      + poverty staging
      + higher-education staging
      + health staging
      + infrastructure staging
      -> consolidated domain table
      -> derived rates / densities
      -> type casting and validation
```

#### Important master-dataset fields

| Column | Meaning | Role |
|---|---|---|
| `clean_domain` | Standardized project domain name | Primary analytical key / join key |
| `land_area_sqkm` | Domain land area derived from geometry | Spatial denominator |
| `total_population` | Domain population | Per-capita denominator |
| `road_density_km_per_100k` | Road length per 100,000 population | Infrastructure indicator |
| `road_density_per_sqkm` | Road length per square kilometer | Infrastructure indicator |
| `primary_road_ratio` | Primary-road length relative to total road length | Infrastructure indicator |
| `bridges_per_100k` | Bridges per 100,000 population | Infrastructure indicator |
| `bridges_per_100sqkm` | Bridges per 100 square kilometers | Infrastructure indicator |
| `basic_schools_per_100k` | Basic schools per 100,000 population | Education indicator |
| `basic_schools_per_10sqkm` | Basic schools per 10 square kilometers | Education indicator |
| `basic_student_teacher_ratio` | Basic enrollment relative to teaching personnel | Education indicator |
| `hei_per_100k` | HEIs per 100,000 population | Education indicator |
| `hei_per_100sqkm` | HEIs per 100 square kilometers | Education indicator |
| `higher_ed_student_faculty_ratio` | Higher-education enrollment relative to faculty | Education indicator |
| `higher_ed_graduates_per_100k` | Graduates per 100,000 population | Education indicator |
| `primary_health_per_100k` | Primary-health facilities per 100,000 population | Health indicator |
| `primary_health_per_100sqkm` | Primary-health facilities per 100 square kilometers | Health indicator |
| `hospitals_per_100k` | Hospitals per 100,000 population | Health indicator |
| `hospitals_per_100sqkm` | Hospitals per 100 square kilometers | Health indicator |

The master dataset is the **main analytical handoff point**: the index scripts do not read the raw or staging files directly; they read `master_dataset.parquet`.

### 16.5 Final Analytical Index Layer

The two index methods produce parallel analytical datasets from the same master dataset.

| Output | Method | Main score fields |
|---|---|---|
| `analytical_master_dataset_minmax.parquet` / `.csv` | Min-Max normalization | Four sector scores, overall score, sector ranks, overall rank |
| `analytical_master_dataset_rank.parquet` / `.csv` | Percentile/rank-based normalization | Four sector scores, overall score, sector ranks, overall rank |

#### Important final fields

| Column | Meaning |
|---|---|
| `clean_domain` | Domain identifier carried from the master dataset |
| `score_infrastructure` | Infrastructure sub-index, 0–100 |
| `score_economic` | Economic sub-index, 0–100 |
| `score_education` | Education sub-index, 0–100 |
| `score_health` | Health sub-index, 0–100 |
| `overall_composite_score` | Weighted overall index, 0–100 |
| `rank_infrastructure` | Rank within infrastructure score; 1 = highest |
| `rank_economic` | Rank within economic score; 1 = highest |
| `rank_education` | Rank within education score; 1 = highest |
| `rank_health` | Rank within health score; 1 = highest |
| `rank_overall` | Overall domain rank; 1 = highest |

### 16.6 Related Tables & Joins

The current pipeline is primarily a **domain-keyed relational workflow** rather than a collection of independent spatial joins after the domain-generation stage.

The main relationships are:

```text
Domains.shp
    |
    +--> clean_domain <---- staging_population
    |
    +--> clean_domain <---- staging_education_basic
    |
    +--> clean_domain <---- staging_education_personnel
    |
    +--> clean_domain <---- staging_income
    |
    +--> clean_domain <---- staging_expenditure
    |
    +--> clean_domain <---- staging_poverty
    |
    +--> clean_domain <---- staging_higher_education
    |
    +--> clean_domain <---- staging_health
    |
    +--> clean_domain <---- staging_infrastructure
                              |
                              v
                       master_dataset
                              |
                     +--------+--------+
                     |                 |
                     v                 v
                 Min-Max           Rank-Based
```

`clean_domain` is therefore the current canonical cross-dataset key. A separate `domain_id` field is **not currently generated by the pipeline**.

---

## 18. Current Limitations

The current pipeline is functional, but several methodological and engineering limitations remain.

### Temporal mismatch

The source datasets do not all refer to the same reporting period. For example, the current DepEd enrollment data are for SY 2025–2026 while the teaching personnel data are for SY 2024–2025, and higher-education graduates are from a different academic year than higher-education enrollment/faculty data.

### Relative normalization

Min-max and rank-based scores are sensitive to the cross-domain distribution in the current dataset. Adding or removing domains can change normalized scores even when a domain's raw indicators do not change.

### Missingness versus zero

The current fallback behavior can convert unavailable information into numeric zeros. This improves pipeline robustness but can weaken interpretability if data availability is uneven across domains.

### Source coverage and measurement limits

The current indicators describe structural access and conditions. They do not directly capture service quality, utilization, learning outcomes, institutional quality, road quality, travel time, or individual-level socioeconomic mobility.

### Causal interpretation

The index is descriptive and comparative. It should not be interpreted as evidence that birthplace causes a specific socioeconomic outcome.

---

## 19. Possible Future Dashboard

A future dashboard can build on the outputs from `06a` and `06b`.

### Page 1 — National Opportunity Map

- Philippine map at domain level
- overall score and rank
- top/bottom domains
- filters by region and domain type

### Page 2 — Opportunity Drivers

- infrastructure score
- economic score
- education score
- health score
- raw indicator drill-down

### Page 3 — Domain Comparison

- compare two provinces/HUCs
- show sector-level differences
- show underlying indicator values
- show rank differences

### Page 4 — Inequality Insights

- distribution of scores
- regional patterns
- high/low combinations across sectors
- identification of domains where one sector strongly diverges from the overall score

---

## 20. Low-Priority Engineering Improvements

These are not required to use the current pipeline, but they would improve maintainability and reproducibility later.

1. **Standardize the domain shapefile path/casing** (`Domains.shp` vs `domains.shp`) and centralize file paths/parameters in one configuration file.
2. **Add a pipeline runner** (for example, `run_pipeline.py`) so the complete workflow can be executed with one command while preserving the option to run each stage independently.
3. **Add explicit data-completeness checks** so missing staging files and missing indicators are distinguishable from true zero values.
4. **Version the domain crosswalk** separately from the processing code because domain mapping changes can materially alter results.
5. **Add automated tests** for high-risk geographic mappings such as HUC exclusions, Cotabato, Maguindanao, Manila subdistricts, and Isabela City.
6. **Store source dates/versions in the output metadata** so temporal comparability can be assessed directly from the final dataset.
7. **Validate indicator semantics before final publication.** In particular, confirm that the income field selected by `05_transform.py` represents the intended income concept, and review the poverty fallback candidates in the index scripts so a poverty threshold cannot be substituted for a poverty percentage if the expected field is unavailable.
8. **Add sensitivity-analysis outputs** comparing min-max and rank-based methods, and later test alternative weighting schemes rather than treating one weighting system as definitive.

These are intentionally secondary to keeping the current data flow stable.

---

## 21. Final Note

The purpose of this project is not to claim that birthplace determines an individual's destiny. The index measures how structural conditions differ across Philippine provinces, HUCs, ICCs, and other project-defined domains and provides a reproducible way to compare those differences.

The intended use is to make disparities visible, identify which sectors drive those disparities, and provide a structured empirical basis for further policy analysis.
