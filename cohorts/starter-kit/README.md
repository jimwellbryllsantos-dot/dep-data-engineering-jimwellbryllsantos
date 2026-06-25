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


## Likely Data Sources


This project relies on **public, semi-structured, and scrapeable datasets**, combined into a unified data warehouse.


### 1. Philippine Statistics Authority (PSA)


Provides:
- Poverty incidence by province
- Population and demographic data
- Income and employment statistics (aggregated surveys)


**Usage in pipeline:**
- Core socioeconomic indicators
- Primary ground truth for inequality analysis


---


### 2. Department of Education (DepEd)


Provides:
- School directory (institution-level data)
- Enrollment statistics (limited aggregation)


**Usage in pipeline:**
- Aggregation of schools per province
- Education access proxy metrics


---


### 3. Department of Health (DOH)


Provides:
- Health facility registry
- Location of hospitals, rural health units, clinics


**Usage in pipeline:**
- Healthcare access indicators per province


---


### 4. OpenStreetMap (OSM)


Provides:
- Road networks
- Infrastructure data
- Geographic features


**Usage in pipeline:**
- Road density computation
- Accessibility and spatial connectivity metrics


---


### 5. Philippine Administrative Boundaries (GIS Data)


Sources may include:
- PSA shapefiles
- GADM dataset
- NAMRIA datasets (if accessible)


**Usage in pipeline:**
- Spatial joins
- Province-level aggregation
- Choropleth visualization


---


### 6. Optional / Exploratory Sources


- DICT reports (digital infrastructure proxies)
- BSP reports (financial access indicators)
- World Bank regional datasets (contextual benchmarking)


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