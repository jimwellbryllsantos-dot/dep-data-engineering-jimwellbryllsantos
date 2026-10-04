import os
import re
import xlrd
from pathlib import Path
import pandas as pd
import geopandas as gpd

# Define base directory paths
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
REF_DIR = BASE_DIR / "data" / "processed"
STAGING_DIR = BASE_DIR / "data" / "processed" / "staging"

SHAPEFILE_PATH = REF_DIR / "domains.shp"

# Manila sub-districts/zones in DepEd dataset that collapse into 'city of manila' or 'manila'
MANILA_SUBDISTRICTS = {
    "tondo", "intramuros", "sampaloc", "san miguel", "santa ana", "quiapo",
    "malate", "santa cruz", "san nicolas", "binondo", "paco", "ermita",
    "pandacan", "port area", 
    "sta cruz", "sta mesa" # other alias
}

# Direct mapping from cleaned variants -> EXACT Qualified Shapefile Domain Names
EXACT_ALIAS_MAP = {
    # Pateros
    "municipality of pateros": "pateros",
    "pateros": "pateros",
    
    # Isabela City
    "isabela city": "city of isabela (not a province)",
    "city of isabela": "city of isabela (not a province)",
    "city of isabela (not a province) (huc)": "city of isabela (not a province)",
    
    # Cotabato & SGA
    "north cotabato": "cotabato (north cotabato)",
    "cotabato": "cotabato (north cotabato)",
    "sga north cotabato": "special geographic area",
    "(sga - north cotabato)": "special geographic area",
    "sga": "special geographic area",
    "special geographic area": "special geographic area",
    
    # Samar
    "samar": "samar (western samar)",
    "western samar": "samar (western samar)",
    "samar (western samar)": "samar (western samar)",
    
    # Quezon (excluding Lucena)
    "quezon": "quezon (excluding city of lucena)",
    "quezon (excluding city of lucena)": "quezon (excluding city of lucena)",
    "quezon province": "quezon (excluding city of lucena)",
    
    # Cebu (excluding HUCs)
    "cebu": "cebu (excluding the cities of cebu, lapu-lapu and mandaue)",
    "cebu (excluding the cities of cebu lapu lapu and mandaue)": "cebu (excluding the cities of cebu, lapu-lapu and mandaue)",
    "cebu (excluding the cities of cebu  lapu lapu and mandaue)": "cebu (excluding the cities of cebu, lapu-lapu and mandaue)",

    # Lapu-Lapu (Opon) 
    "lapu lapu city (opon)": "city of lapu-lapu (opon)",
    "lapu lapu city": "city of lapu-lapu (opon)",

    # Mandaue
    "mandaue city": "city of mandaue",

    # Lucena
    "lucena city (capital)": "city of lucena",
    "lucena city": "city of lucena",

    # Iloilo (Excluding Iloilo City)
    "iloilo": "iloilo (excluding city of iloilo)",

    # Mountain Province
    "mt province": "mountain province",

    # Major Cities
    "cebu city": "city of cebu",
    "iloilo city": "city of iloilo",
}


def clean_str(text: str) -> str:
    """Basic alphanumeric normalization without destroying parenthesis structure."""
    if pd.isna(text) or not text:
        return ""
    text = str(text).lower().strip()
    text = re.sub(r"[*0-9/]", "", text)
    text = re.sub(r"[.,\-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def load_shapefile_domain_map(filepath: Path) -> tuple[dict, set]:
    """
    Loads shapefile domains and creates a dynamic lookup map:
    normalized_variant -> exact_shapefile_domain_name
    """
    target_path = filepath
    if not target_path.exists():
        spatial_files = list(REF_DIR.glob("*.shp")) + list(REF_DIR.glob("*.geojson")) + list(REF_DIR.glob("*.gpkg"))
        if not spatial_files:
            raise FileNotFoundError(f"Reference shapefile not found at: {filepath}")
        target_path = spatial_files[0]

    gdf = gpd.read_file(target_path)
    
    target_col = None
    for col in ["clean_domain", "domain", "ADM2_EN", "ADM1_EN", "NAME_1", "NAME_2"]:
        if col in gdf.columns:
            target_col = col
            break
    if not target_col:
        target_col = gdf.columns[0]

    raw_shape_domains = set(gdf[target_col].dropna().astype(str).str.strip())
    
    # Build bidirectional lookup dictionary
    domain_map = {}
    for official_name in raw_shape_domains:
        # 1. Exact lower
        domain_map[official_name.lower()] = official_name
        
        # 2. Cleaned version
        c_name = clean_str(official_name)
        domain_map[c_name] = official_name
        
        # 3. Stripped variant (without city prefix or parenthesis)
        stripped = (
            c_name.replace("city of ", "")
            .replace(" city", "")
            .replace("municipality of ", "")
            .replace(" municipality", "")
            .strip()
        )
        stripped_no_paren = re.sub(r"\(.*?\)", "", stripped).strip()
        stripped_no_paren = re.sub(r"\s+", " ", stripped_no_paren)
        
        if stripped and stripped not in domain_map:
            domain_map[stripped] = official_name
        if stripped_no_paren and stripped_no_paren not in domain_map:
            domain_map[stripped_no_paren] = official_name

    # Apply hard explicit aliases over auto-generated map
    for alias, official in EXACT_ALIAS_MAP.items():
        if official in raw_shape_domains:
            domain_map[alias] = official

    print(f"Loaded {len(raw_shape_domains)} domains from {target_path.name} (Mapped {len(domain_map)} variants)")
    return domain_map, raw_shape_domains


# =============================================================================
# MODULE 1: PSA Population & Household Cleaning
# =============================================================================
def clean_population_dataset(domain_map: dict) -> Path:
    """Cleans PSA Population & Household data and aligns with reference shapefile domains."""
    print("\n--- Processing PSA Population & Household Data ---")

    pop_file = RAW_DIR / "Total Population - Philippines 2024_2026-07-11.xlsx"
    if not pop_file.exists():
        raise FileNotFoundError(f"Population file not found at: {pop_file}")

    df_raw = pd.read_excel(pop_file, sheet_name=0)

    df = df_raw.iloc[4:160, [0, 2, 4, 5, 6]].copy()
    df.columns = [
        "raw_domain_name",
        "total_population",
        "household_population",
        "number_of_households",
        "avg_household_size",
    ]

    df = df.dropna(subset=["raw_domain_name", "total_population"])

    numeric_cols = [
        "total_population",
        "household_population",
        "number_of_households",
        "avg_household_size",
    ]
    for col in numeric_cols:
        df[col] = df[col].astype(str).str.replace(",", "").str.strip()
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Exclude regional totals
    df = df[~df["raw_domain_name"].str.startswith("Region", na=False)]
    df = df[~df["raw_domain_name"].str.startswith("National Capital Region", na=False)]
    df = df[~df["raw_domain_name"].str.startswith("Cordillera Administrative", na=False)]
    df = df[~df["raw_domain_name"].str.startswith("Negros Island Region", na=False)]
    df = df[~df["raw_domain_name"].str.startswith("Bangsamoro Autonomous Region", na=False)]
    df = df[~df["raw_domain_name"].str.startswith("MIMAROPA Region", na=False)]
    df = df[df["raw_domain_name"].str.strip() != "Philippines"]

    def resolve_pop_domain(raw_name: str) -> str:
        raw_clean = str(raw_name).lower().strip()
        c_raw = clean_str(raw_name)
        
        # 1. Direct Alias Match
        if raw_clean in EXACT_ALIAS_MAP:
            return EXACT_ALIAS_MAP[raw_clean]
        if c_raw in EXACT_ALIAS_MAP:
            return EXACT_ALIAS_MAP[c_raw]

        # 2. Domain Map Match
        if c_raw in domain_map:
            return domain_map[c_raw]
            
        stripped = c_raw.replace("city of ", "").replace(" city", "").replace("municipality of ", "").strip()
        if stripped in domain_map:
            return domain_map[stripped]

        return raw_name.strip()

    df["clean_domain"] = df["raw_domain_name"].apply(resolve_pop_domain)

    # =========================================================================
    # COTABATO CITY & MAGUINDANAO DEL NORTE DECOUPLING TRANSFORMATION
    # =========================================================================
    COTABATO_CITY_POP = 383383

    mask_m_norte = df["clean_domain"] == "maguindanao_del_norte"
    if mask_m_norte.any():
        idx_m_norte = df[mask_m_norte].index[0]
        
        merged_pop = df.loc[idx_m_norte, "total_population"]
        merged_hh_pop = df.loc[idx_m_norte, "household_population"]
        merged_num_hh = df.loc[idx_m_norte, "number_of_households"]

        if merged_pop > COTABATO_CITY_POP:
            # Proportional ratio to split household metrics accurately
            pop_ratio = COTABATO_CITY_POP / merged_pop

            cotabato_hh_pop = round(merged_hh_pop * pop_ratio)
            cotabato_num_hh = round(merged_num_hh * pop_ratio)
            cotabato_avg_hh = round(cotabato_hh_pop / cotabato_num_hh, 2) if cotabato_num_hh > 0 else 0.0

            # 1. Subtract Cotabato City metrics from Maguindanao del Norte
            df.loc[idx_m_norte, "total_population"] -= COTABATO_CITY_POP
            df.loc[idx_m_norte, "household_population"] -= cotabato_hh_pop
            df.loc[idx_m_norte, "number_of_households"] -= cotabato_num_hh

            rem_hh_pop = df.loc[idx_m_norte, "household_population"]
            rem_num_hh = df.loc[idx_m_norte, "number_of_households"]
            df.loc[idx_m_norte, "avg_household_size"] = round(rem_hh_pop / rem_num_hh, 2) if rem_num_hh > 0 else 0.0

            # 2. Update existing Cotabato City record or append a new row
            mask_cotabato = df["clean_domain"] == "cotabato_city"
            if mask_cotabato.any():
                idx_cotabato = df[mask_cotabato].index[0]
                df.loc[idx_cotabato, "total_population"] = COTABATO_CITY_POP
                df.loc[idx_cotabato, "household_population"] = cotabato_hh_pop
                df.loc[idx_cotabato, "number_of_households"] = cotabato_num_hh
                df.loc[idx_cotabato, "avg_household_size"] = cotabato_avg_hh
            else:
                cotabato_row = pd.DataFrame([{
                    "raw_domain_name": "Cotabato City",
                    "clean_domain": "cotabato_city",
                    "total_population": COTABATO_CITY_POP,
                    "household_population": cotabato_hh_pop,
                    "number_of_households": cotabato_num_hh,
                    "avg_household_size": cotabato_avg_hh,
                }])
                df = pd.concat([df, cotabato_row], ignore_index=True)

            print(f"  • Successfully unmerged Cotabato City ({COTABATO_CITY_POP:,}) from Maguindanao del Norte.")

    out_cols = [
        "clean_domain",
        "raw_domain_name",
        "total_population",
        "household_population",
        "number_of_households",
        "avg_household_size",
    ]
    df_staging = df[out_cols].reset_index(drop=True)

    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    out_path = STAGING_DIR / "staging_population.parquet"
    df_staging.to_parquet(out_path, index=False)

    print(f"Generated {out_path.name} with {len(df_staging)} records.")
    print(df_staging.head(5).to_string())
    return out_path

# =============================================================================
# MODULE 2: DepEd School-Level Enrollment Cleaning
# =============================================================================
def clean_deped_dataset(domain_map: dict) -> Path:
    """Cleans DepEd SY 2025-2026 school-level data and aggregates to domain level."""
    print("\n--- Processing DepEd Basic Education Data ---")

    deped_file = (
        RAW_DIR / "_SY 2025-2026 SCHOOL LEVEL DATA ON ENROLLMENT (BY_SCHOOL_FR)_1_2026-07-27.xlsx"
    )
    if not deped_file.exists():
        raise FileNotFoundError(f"DepEd file not found at: {deped_file}")

    df_raw = pd.read_excel(deped_file, sheet_name="DATABASE", header=None)

    header_idx = df_raw[df_raw.iloc[:, 0] == "#EMISD"].index[0]
    df = df_raw.iloc[header_idx + 1:].copy()
    df.columns = df_raw.iloc[header_idx].values

    def resolve_school_domain(row):
        muni_raw = str(row.get("Municipality", ""))
        prov_raw = str(row.get("Province", ""))
        div_raw = str(row.get("Division", "")).strip()

        muni_c = clean_str(muni_raw)
        prov_c = clean_str(prov_raw)
        div_c = clean_str(div_raw)

        # 1. Check Manila sub-districts
        if muni_c in MANILA_SUBDISTRICTS or any(sub in div_c for sub in MANILA_SUBDISTRICTS):
            if "city of manila" in domain_map:
                return domain_map["city of manila"]
            elif "manila" in domain_map:
                return domain_map["manila"]

        # 2. Check Explicit Aliases across fields
        for test_val in [muni_c, div_c, prov_c]:
            if test_val in EXACT_ALIAS_MAP:
                return EXACT_ALIAS_MAP[test_val]

        # 3. Try matching Municipality directly
        if muni_c in domain_map:
            return domain_map[muni_c]
        
        muni_stripped = muni_c.replace("city of ", "").replace(" city", "").strip()
        if muni_stripped in domain_map:
            return domain_map[muni_stripped]

        # 4. Try matching Division directly
        if div_c in domain_map:
            return domain_map[div_c]
            
        div_stripped = div_c.replace("city of ", "").replace(" city", "").replace("division of ", "").strip()
        if div_stripped in domain_map:
            return domain_map[div_stripped]

        # 5. Maguindanao & SGA Splits
        if "sga" in div_c or "special geographic area" in div_c:
            if "special geographic area" in domain_map:
                return domain_map["special geographic area"]

        if "maguindanao" in prov_c or "maguindanao" in div_c:
            if "maguindanao i" in div_c and "ii" not in div_c:
                if "maguindanao del sur" in domain_map:
                    return domain_map["maguindanao del sur"]
            elif "maguindanao ii" in div_c:
                if "maguindanao del norte" in domain_map:
                    return domain_map["maguindanao del norte"]

        # 6. Fallback to Province lookup
        if prov_c in domain_map:
            return domain_map[prov_c]
            
        prov_stripped = prov_c.replace("city of ", "").replace(" city", "").strip()
        if prov_stripped in domain_map:
            return domain_map[prov_stripped]

        return prov_raw.strip()

    df["clean_domain"] = df.apply(resolve_school_domain, axis=1)

    enrollment_cols = [
        c for c in df.columns
        if any(k in str(c).lower() for k in ["male", "female", "g1", "g11", "k"])
    ]
    for col in enrollment_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["school_total_enrollment"] = df[enrollment_cols].sum(axis=1)

    df_staging = (
        df.groupby("clean_domain")
        .agg(
            total_schools=("beis_school_id", "nunique"),
            public_schools=(
                "Sector",
                lambda x: (x.astype(str).str.upper() == "PUBLIC").sum(),
            ),
            private_schools=(
                "Sector",
                lambda x: (x.astype(str).str.upper() == "PRIVATE").sum(),
            ),
            total_enrollment=("school_total_enrollment", "sum"),
        )
        .reset_index()
    )

    df_staging = df_staging[df_staging["clean_domain"] != ""].reset_index(drop=True)

    out_path = STAGING_DIR / "staging_education_basic.parquet"
    df_staging.to_parquet(out_path, index=False)

    print(f"Generated {out_path.name} with {len(df_staging)} domain records.")
    print(df_staging.head(5).to_string())
    return out_path


# =============================================================================
# MODULE 3: DepEd Teaching Personnel Cleaning 
# =============================================================================
def clean_teaching_personnel_dataset(domain_map: dict) -> Path:
    """Cleans DepEd SY 2024-2025 teaching personnel data, extracts per-level counts, and aggregates to domain level."""
    print("\n--- Processing DepEd Teaching Personnel Data ---")

    teaching_file = (
        RAW_DIR / "SY 2024-2025 PERSONNEL DATA - TEACHING PERSONNEL BY POSITION TITLE BY SCHOOL_2026-07-27.xlsx"
    )
    if not teaching_file.exists():
        raise FileNotFoundError(f"Teaching personnel file not found at: {teaching_file}")

    def resolve_school_domain(row):
        muni_raw = str(row.get("Municipality", ""))
        prov_raw = str(row.get("Province", ""))
        div_raw = str(row.get("Division", "")).strip()

        muni_c = clean_str(muni_raw)
        prov_c = clean_str(prov_raw)
        div_c = clean_str(div_raw)

        # 1. Check Manila sub-districts
        if muni_c in MANILA_SUBDISTRICTS or any(sub in div_c for sub in MANILA_SUBDISTRICTS):
            if "city of manila" in domain_map: return domain_map["city of manila"]
            elif "manila" in domain_map: return domain_map["manila"]

        # 2. Check Explicit Aliases
        for test_val in [muni_c, div_c, prov_c]:
            if test_val in EXACT_ALIAS_MAP: return EXACT_ALIAS_MAP[test_val]

        # 3. Match Municipality
        if muni_c in domain_map: return domain_map[muni_c]
        muni_stripped = muni_c.replace("city of ", "").replace(" city", "").strip()
        if muni_stripped in domain_map: return domain_map[muni_stripped]

        # 4. Match Division
        if div_c in domain_map: return domain_map[div_c]
        div_stripped = div_c.replace("city of ", "").replace(" city", "").replace("division of ", "").strip()
        if div_stripped in domain_map: return domain_map[div_stripped]

        # 5. Maguindanao & SGA Splits
        if "sga" in div_c or "special geographic area" in div_c:
            if "special geographic area" in domain_map: return domain_map["special geographic area"]

        if "maguindanao" in prov_c or "maguindanao" in div_c:
            if "maguindanao i" in div_c and "ii" not in div_c:
                if "maguindanao del sur" in domain_map: return domain_map["maguindanao del sur"]
            elif "maguindanao ii" in div_c:
                if "maguindanao del norte" in domain_map: return domain_map["maguindanao del norte"]

        # 6. Fallback to Province
        if prov_c in domain_map: return domain_map[prov_c]
        prov_stripped = prov_c.replace("city of ", "").replace(" city", "").strip()
        if prov_stripped in domain_map: return domain_map[prov_stripped]

        return prov_raw.strip()

    dfs = []
    xls = pd.ExcelFile(teaching_file)
    
    for sheet in ["ES", "JHS", "SHS"]:
        if sheet in xls.sheet_names:
            # Header is on row index 7 (8th row) in all three sheets
            df_sheet = pd.read_excel(xls, sheet_name=sheet, header=7)
            df_sheet = df_sheet.dropna(subset=["BEIS School ID"])
            
            cols = df_sheet.columns.tolist()
            
            # Dynamically slice all columns from 'Enrollment' up to 'Total {sheet}'
            if 'Enrollment' in cols:
                start_idx = cols.index('Enrollment')
                total_col = f"Total {sheet}"
                end_idx = cols.index(total_col) if total_col in cols else len(cols)
                target_cols = cols[start_idx:end_idx]
            else:
                # Fallback if structure changes slightly
                target_cols = [c for c in cols if any(x in str(c) for x in ['Teacher', 'Instructor', 'SPED', 'Enrollment'])]
            
            loc_cols = ["Division", "Province", "Municipality"]
            keep_cols = loc_cols + target_cols
            
            # Filter the dataframe to only keep location identifiers + metric columns
            df_sheet = df_sheet[[c for c in keep_cols if c in df_sheet.columns]].copy()
            
            # Ensure all metric columns are numeric
            for c in target_cols:
                if c in df_sheet.columns:
                    df_sheet[c] = pd.to_numeric(df_sheet[c], errors="coerce").fillna(0)
            
            dfs.append(df_sheet)

    if not dfs:
        raise ValueError("Could not read teaching personnel sheets.")

    # Combine all sheets (aligns varying teacher titles like 'Instructor' from JHS with 'Teacher' from ES/SHS)
    df_all = pd.concat(dfs, ignore_index=True)
    df_all = df_all.fillna(0)  # Fill NaNs for teacher positions that only exist in certain sheets
    
    # Resolve names using your domain map
    df_all["clean_domain"] = df_all.apply(resolve_school_domain, axis=1)

    # Identify the final list of numeric metric columns to sum
    agg_cols = [c for c in df_all.columns if c not in ["Division", "Province", "Municipality", "clean_domain"]]

    # Aggregate metric columns to domain level
    df_staging = (
        df_all.groupby("clean_domain")[agg_cols]
        .sum()
        .reset_index()
    )

    # Remove unmatched records
    df_staging = df_staging[df_staging["clean_domain"] != ""].reset_index(drop=True)

    # Export
    out_path = STAGING_DIR / "staging_education_personnel.parquet"
    df_staging.to_parquet(out_path, index=False)

    print(f"Generated {out_path.name} with {len(df_staging)} domain records.")
    print(df_staging.head(5).to_string())
    return out_path

# =============================================================================
# MODULE 4: PSA Annual Income Cleaning 
# =============================================================================
def clean_income_dataset(domain_map: dict) -> Path:
    """Cleans PSA 2023 income data, filters out regions/metadata, handles Maguindanao variants, and maps to master domains."""
    print("\n--- Processing PSA Income Data ---")

    income_file = (
        RAW_DIR / "Table 1. 2018, 2021 and 2023p Average Annual Family Income, by Per Capita Income Decile Class and by Region, Province and HUCs_2026-07-10.xlsx"
    )
    if not income_file.exists():
        raise FileNotFoundError(f"Income file not found at: {income_file}")

    def resolve_income_domain(loc_raw):
        if pd.isna(loc_raw):
            return ""
            
        loc_str = str(loc_raw).strip()
        loc_c = clean_str(loc_str)

        # 1. Filter out regions, footnotes, sources, and metadata rows
        skip_keywords = [
            "philippines", "region", "car", "caraga", "mimaropa", 
            "national capital region", "negros island region", "barmm", 
            "notes:", "source:", "family income", "ncr i", "ncr ii", "ncr iii",
            "p estimates are preliminary and may change"
        ]
        if any(loc_c.startswith(kw) or loc_c == kw for kw in skip_keywords) or loc_str[0].isdigit():
            return ""

        # 2. Check Explicit Aliases
        if loc_c in EXACT_ALIAS_MAP: 
            return EXACT_ALIAS_MAP[loc_c]

        # 3. Handle Special Cases / Fallbacks (e.g., Special Geographic Area or Maguindanao adjustments if needed)
        if "sga" in loc_c or "special geographic area" in loc_c:
            if "special geographic area" in domain_map: 
                return domain_map["special geographic area"]

        # 4. Direct Match
        if loc_c in domain_map: 
            return domain_map[loc_c]

        # 5. Strip common prefixes/suffixes
        loc_stripped = loc_c.replace("city of ", "").replace(" city", "").strip()
        if loc_stripped in domain_map: 
            return domain_map[loc_stripped]

        return loc_str

    # Load the sheet blindly first to locate headers dynamically
    df = pd.read_excel(income_file, sheet_name="Table 1", header=None)
    
    # Locate the main header row
    header_idx = df[df.iloc[:, 0] == 'Region/Province/HUC'].index[0]
    
    top_header = pd.Series(df.iloc[header_idx].values).ffill()
    sub_header = df.iloc[header_idx + 2].values
    
    combined_cols = []
    for top, sub in zip(top_header, sub_header):
        if top == 'Region/Province/HUC':
            combined_cols.append('Region/Province/HUC')
        else:
            combined_cols.append(f"{top}_{sub}")
            
    df_data = df.iloc[header_idx + 3:].copy()
    df_data.columns = combined_cols
    
    # Filter strictly for 2023 columns (drops percent changes)
    loc_col = 'Region/Province/HUC'
    target_cols = [loc_col] + [c for c in combined_cols if str(c).startswith('2023')]
    
    df_2023 = df_data[target_cols].copy()
    
    # Clean and map geographic locations
    df_2023 = df_2023.dropna(subset=[loc_col])
    df_2023["clean_domain"] = df_2023[loc_col].apply(resolve_income_domain)
    
    # Remove junk rows
    df_2023 = df_2023[df_2023["clean_domain"] != ""].reset_index(drop=True)

    # Clean numeric columns
    numeric_cols = [c for c in df_2023.columns if c not in [loc_col, 'clean_domain']]
    for c in numeric_cols:
        df_2023[c] = df_2023[c].astype(str).str.replace(r'[^\d.]', '', regex=True)
        df_2023[c] = pd.to_numeric(df_2023[c], errors='coerce').fillna(0)

    # Aggregate by clean domain (handles potential duplicates if variants map to the same domain)
    df_staging = df_2023.groupby("clean_domain")[numeric_cols].sum().reset_index()

    # Standardize column names
    df_staging.columns = [
        c.replace('2023p_', '2023_').lower().replace(' ', '_') for c in df_staging.columns
    ]

    # Export
    out_path = STAGING_DIR / "staging_income.parquet"
    df_staging.to_parquet(out_path, index=False)

    print(f"Generated {out_path.name} with {len(df_staging)} domain records.")
    print(df_staging.head(5).to_string()) 
    
    return out_path

# =============================================================================
# MODULE 5: PSA Annual Expenditure Cleaning 
# =============================================================================
def clean_expenditure_dataset(domain_map: dict) -> Path:
    """Cleans PSA 2023 expenditure data, extracting only expenditure values, and maps to master domains."""
    print("\n--- Processing PSA Expenditure Data ---")

    exp_file = (
        RAW_DIR / "Table 2. 2018, 2021 and 2023p Average Annual Family Expenditure, by Per Capita Income Decile Class and by Region, Province and HUC_2026-07-10.xlsx"
    )
    if not exp_file.exists():
        raise FileNotFoundError(f"Expenditure file not found at: {exp_file}")

    def resolve_expenditure_domain(loc_raw):
        if pd.isna(loc_raw):
            return ""
            
        loc_str = str(loc_raw).strip()
        loc_c = clean_str(loc_str)

        # Ignore aggregate headers, footnotes, or blank spaces
        skip_keywords = [
            "philippines", "region", "car", "caraga", "mimaropa", 
            "national capital region", "negros island region", "barmm", 
            "notes:", "source:", "family expenditure", "ncr i", "ncr ii", "ncr iii",
            "p estimates are preliminary and may change"
        ]
        if any(loc_c.startswith(kw) or loc_c == kw for kw in skip_keywords) or loc_str[0].isdigit():
            return ""

        # 1. Check Explicit Aliases
        if loc_c in EXACT_ALIAS_MAP: 
            return EXACT_ALIAS_MAP[loc_c]

        # 2. Handle Special Cases / Fallbacks 
        if "sga" in loc_c or "special geographic area" in loc_c:
            if "special geographic area" in domain_map: 
                return domain_map["special geographic area"]

        # 3. Match Directly
        if loc_c in domain_map: 
            return domain_map[loc_c]

        # 4. Strip common prefixes/suffixes
        loc_stripped = loc_c.replace("city of ", "").replace(" city", "").strip()
        if loc_stripped in domain_map: 
            return domain_map[loc_stripped]

        return loc_str

    # Load the sheet blindly first to locate headers dynamically
    df = pd.read_excel(exp_file, sheet_name="Table 2", header=None)
    
    # Locate the main header row (e.g., 'Region/Province/HUC')
    header_idx = df[df.iloc[:, 0] == 'Region/Province/HUC'].index[0]
    
    # Forward-fill the top header row across the merged year groups
    top_header = pd.Series(df.iloc[header_idx].values).ffill()
    
    # The sub-header containing deciles / "All Income Groups" is 2 rows down (Row index header_idx + 2)
    sub_header = df.iloc[header_idx + 2].values
    
    # Combine them to create explicit column names
    combined_cols = []
    for top, sub in zip(top_header, sub_header):
        if top == 'Region/Province/HUC':
            combined_cols.append('Region/Province/HUC')
        else:
            combined_cols.append(f"{top}_{sub}")
            
    # Apply these explicit columns to the actual data rows
    df_data = df.iloc[header_idx + 3:].copy()
    df_data.columns = combined_cols
    
    # Filter strictly for 2023 columns (drops percent changes)
    loc_col = 'Region/Province/HUC'
    target_cols = [loc_col] + [c for c in combined_cols if str(c).startswith('2023')]
    
    df_2023 = df_data[target_cols].copy()
    
    # Clean and map geographic locations
    df_2023 = df_2023.dropna(subset=[loc_col])
    df_2023["clean_domain"] = df_2023[loc_col].apply(resolve_expenditure_domain)
    
    # Remove junk rows (footnotes, aggregate headers)
    df_2023 = df_2023[df_2023["clean_domain"] != ""].reset_index(drop=True)

    # Clean numeric columns (Remove commas, asterisks)
    numeric_cols = [c for c in df_2023.columns if c not in [loc_col, 'clean_domain']]
    for c in numeric_cols:
        df_2023[c] = df_2023[c].astype(str).str.replace(r'[^\d.]', '', regex=True)
        df_2023[c] = pd.to_numeric(df_2023[c], errors='coerce').fillna(0)

    # Aggregate by clean domain 
    df_staging = df_2023.groupby("clean_domain")[numeric_cols].sum().reset_index()

    # Make the exported column names neat and standard (e.g. "2023_all_income_groups")
    df_staging.columns = [
        c.replace('2023p_', '2023_exp_').lower().replace(' ', '_') for c in df_staging.columns
    ]

    # Export
    out_path = STAGING_DIR / "staging_expenditure.parquet"
    df_staging.to_parquet(out_path, index=False)

    print(f"Generated {out_path.name} with {len(df_staging)} domain records.")
    print(df_staging.head(5).to_string()) 
    
    return out_path

# =============================================================================
# MODULE 6: PSA Official Poverty Statistics Cleaning 
# =============================================================================
def clean_poverty_dataset(domain_map: dict) -> Path:
    """Cleans PSA Official Poverty Statistics data (tab1a) for 2023 and maps to master shapefile domains."""
    print("\n--- Processing PSA Poverty Statistics Data ---")

    poverty_file = RAW_DIR / "2023 Full Year Official Poverty Statistics_r2_2026-07-10.xlsx"
    if not poverty_file.exists():
        raise FileNotFoundError(f"Poverty statistics file not found at: {poverty_file}")

    # Expanded Alias Map to handle 'w/o' vs 'excluding' and provincial name variations
    EXACT_ALIAS_MAP_POV = {
        **EXACT_ALIAS_MAP,
        "agusan del norte (wo the city of butuan)": "agusan del norte (excluding city of butuan)",
        "benguet (wo the city of baguio)": "benguet (excluding city of baguio)",
        "cebu (wo the cities of cebu lapu lapu and mandaue)": "cebu (excluding the cities of cebu, lapu-lapu and mandaue)",
        "davao del sur (wo the city of davao)": "davao del sur (excluding city of davao)",
        "iloilo (wo the city of iloilo)": "iloilo (excluding city of iloilo)",
        "lanao del norte (wo the city of iligan)": "lanao del norte (excluding city of iligan)",
        "leyte (wo the city of tacloban)": "leyte (excluding city of tacloban)",
        "misamis oriental (wo the city of cagayan de oro)": "misamis oriental (excluding city of cagayan de oro)",
        "negros occidental (wo the city of bacolod)": "negros occidental (excluding city of bacolod)",
        "palawan (wo the city of puerto princesa)": "palawan (excluding city of puerto princesa)",
        "pampanga (wo the city of angeles)": "pampanga (excluding city of angeles)", 
        "quezon (wo the city of lucena)": "quezon (excluding city of lucena)",
        "south cotabato (wo the city of gen santos)": "south cotabato (excluding city of general santos)",
        "zambales (wo the city of olongapo)": "zambales (excluding city of olongapo)",
        "zamboanga del sur (wo the city of zamboanga)": "zamboanga del sur (excluding city of zamboanga)"
    }

    def resolve_poverty_domain(loc_raw):
        if pd.isna(loc_raw):
            return ""
            
        loc_str = str(loc_raw).strip()
        loc_c = clean_str(loc_str)

        # Expanded skip keywords for footnotes, notes, regions, and metadata
        skip_keywords = [
            "philippines", "region", "car", "caraga", "mimaropa", 
            "national capital region", "negros island region", "barmm", 
            "bangsamoro", "cordillera", "notes:", "source:", "poverty statistics", "district",
            "p estimates are preliminary", "r updated", "r revised", "caution", "please", "a those", "b those", "c those", "d coefficient"
        ]
        if any(loc_c.startswith(kw) or loc_c == kw for kw in skip_keywords) or loc_c == "maguindanao" or loc_str[0].isdigit() or "district" in loc_c:
            return ""

        # 1. Check Explicit Aliases
        if loc_c in EXACT_ALIAS_MAP_POV: 
            return EXACT_ALIAS_MAP_POV[loc_c]

        # 2. Handle Special Cases
        if "sga" in loc_c or "special geographic area" in loc_c:
            if "special geographic area" in domain_map: 
                return domain_map["special geographic area"]

        # 3. Direct Match in Master Domain Map
        if loc_c in domain_map: 
            return domain_map[loc_c]

        # 4. Strip common prefixes/suffixes
        loc_stripped = loc_c.replace("city of ", "").replace(" city", "").strip()
        if loc_stripped in domain_map: 
            return domain_map[loc_stripped]

        return loc_str

    # Load tab1a
    df = pd.read_excel(poverty_file, sheet_name="tab1a", header=None)
    df_data = df.iloc[7:].copy()
    
    # Extract Region/Province (col 0), 2023 Threshold (col 3), 2023 Family Poverty Incidence (col 6)
    df_poverty = df_data[[0, 3, 6]].copy()
    df_poverty.columns = [
        "raw_location",
        "poverty_threshold_2023",
        "family_poverty_incidence_2023_pct"
    ]

    df_poverty = df_poverty.dropna(subset=["raw_location"])
    df_poverty["clean_domain"] = df_poverty["raw_location"].apply(resolve_poverty_domain)
    
    # Filter out empty or unmapped rows
    df_poverty = df_poverty[df_poverty["clean_domain"] != ""].reset_index(drop=True)

    # Clean numeric columns
    numeric_cols = ["poverty_threshold_2023", "family_poverty_incidence_2023_pct"]
    for c in numeric_cols:
        df_poverty[c] = df_poverty[c].astype(str).str.replace(r'[^\d.]', '', regex=True)
        df_poverty[c] = pd.to_numeric(df_poverty[c], errors='coerce')

    # Aggregate by clean domain and retain only the 3 required columns
    df_staging = df_poverty.groupby("clean_domain")[numeric_cols].mean().reset_index()
    df_staging = df_staging[["clean_domain", "poverty_threshold_2023", "family_poverty_incidence_2023_pct"]]

    # Export
    out_path = STAGING_DIR / "staging_poverty.parquet"
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    df_staging.to_parquet(out_path, index=False)

    print(f"Generated {out_path.name} with {len(df_staging)} domain records.")
    print(df_staging.head(5).to_string())
    return out_path

# =============================================================================
# MODULE 7: Higher Education Enrollment and Graduates Cleaning 
# =============================================================================
def clean_higher_education_dataset(domain_map: dict) -> Path:
    """Cleans CHED Higher Education enrollment, graduate, and faculty data, and aggregates to domain level."""
    print("\n--- Processing Higher Education Data ---")

    higher_edu_file = RAW_DIR / "Higher Education Enrollment and Graduates.xlsx"
    if not higher_edu_file.exists():
        raise FileNotFoundError(f"Higher Education file not found at: {higher_edu_file}")

    def resolve_higher_edu_domain(row):
        muni_raw = str(row.get("City", ""))
        prov_raw = str(row.get("Province", ""))
        hei_raw = str(row.get("Higher Education Institution (HEI)", ""))

        muni_c = clean_str(muni_raw)
        prov_c = clean_str(prov_raw)

        # 1. Check Manila sub-districts if present in city/HEI names
        if muni_c in MANILA_SUBDISTRICTS or any(sub in clean_str(hei_raw) for sub in MANILA_SUBDISTRICTS):
            if "city of manila" in domain_map: return domain_map["city of manila"]
            elif "manila" in domain_map: return domain_map["manila"]

        # 2. Check Explicit Aliases across fields
        for test_val in [muni_c, prov_c]:
            if test_val in EXACT_ALIAS_MAP: return EXACT_ALIAS_MAP[test_val]

        # 3. Try matching City/Municipality directly
        if muni_c in domain_map: return domain_map[muni_c]
        muni_stripped = muni_c.replace("city of ", "").replace(" city", "").strip()
        if muni_stripped in domain_map: return domain_map[muni_stripped]

        # 4. Fallback to Province lookup
        if prov_c in domain_map: return domain_map[prov_c]
        prov_stripped = prov_c.replace("city of ", "").replace(" city", "").strip()
        if prov_stripped in domain_map: return domain_map[prov_stripped]

        return prov_raw.strip()

    # Load data using header row index 10 (11th row)
    df = pd.read_excel(higher_edu_file, header=10)
    
    # Standardize expected column names
    # Expected columns: ['Region', 'Province', 'City', 'Higher Education Institution (HEI)', 'HEI Type', 'AY 2025-26 Enrolment[2]', 'AY 2024-25 Graduate', 'AY 2025-26 Faculty']
    df = df.dropna(subset=["Higher Education Institution (HEI)"])

    # Identify exact metric columns
    col_enrolment = [c for c in df.columns if "enrolment" in str(c).lower()][0]
    col_graduate = [c for c in df.columns if "graduate" in str(c).lower()][0]
    col_faculty = [c for c in df.columns if "faculty" in str(c).lower()][0]

    # Coerce metrics to numeric
    for col in [col_enrolment, col_graduate, col_faculty]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Resolve names using domain map
    df["clean_domain"] = df.apply(resolve_higher_edu_domain, axis=1)

    # Aggregate to domain level (summing enrollees, graduates, and faculty across HEIs per domain)
    df_staging = (
        df.groupby("clean_domain")
        .agg(
            higher_ed_enrolment=(col_enrolment, "sum"),
            higher_ed_graduates=(col_graduate, "sum"),
            higher_ed_faculty=(col_faculty, "sum"),
            total_heis=("Higher Education Institution (HEI)", "count")
        )
        .reset_index()
    )

    # Filter out empty or unmapped domains
    df_staging = df_staging[df_staging["clean_domain"] != ""].reset_index(drop=True)

    # Export to staging directory
    out_path = STAGING_DIR / "staging_higher_education.parquet"
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    df_staging.to_parquet(out_path, index=False)

    print(f"Generated {out_path.name} with {len(df_staging)} domain records.")
    print(df_staging.head(5).to_string())
    return out_path

# =============================================================================
# MODULE 8: Health Facility and Unit Cleaning (Stat_HFProvincial)
# =============================================================================
def clean_health_dataset(domain_map: dict) -> Path:
    """Cleans provincial health facility data (starting from BHS), maps to master domains, and aggregates."""
    print("\n--- Processing Health Facility Data ---")

    health_file = RAW_DIR / "Stat_HFProvincial_2026-07-11.xls"
    if not health_file.exists():
        raise FileNotFoundError(f"Health facility file not found at: {health_file}")

    def resolve_health_domain(prov_raw):
        if pd.isna(prov_raw):
            return ""
            
        prov_str = str(prov_raw).strip()
        prov_c = clean_str(prov_str)

        # 1. Check Explicit Aliases
        if prov_c in EXACT_ALIAS_MAP: 
            return EXACT_ALIAS_MAP[prov_c]

        # 2. Direct Match in Master Domain Map
        if prov_c in domain_map: 
            return domain_map[prov_c]

        # 3. Strip common suffixes/parentheses (e.g. HUC tags like "(HUC)")
        prov_clean_no_huc = re.sub(r"\(.*?\)", "", prov_c).strip()
        if prov_clean_no_huc in domain_map: 
            return domain_map[prov_clean_no_huc]

        prov_stripped = prov_clean_no_huc.replace("city of ", "").replace(" city", "").strip()
        if prov_stripped in domain_map: 
            return domain_map[prov_stripped]

        return prov_str

    # Read legacy .xls file with xlrd, ignoring minor structure warnings
    book = xlrd.open_workbook(health_file, ignore_workbook_corruption=True)
    sheet = book.sheet_by_index(0)
    headers = [sheet.cell_value(0, c) for c in range(sheet.ncols)]
    data = [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(1, sheet.nrows)]
    
    df = pd.DataFrame(data, columns=headers)
    
    # Identify province column and metrics starting from BHS onwards
    province_col = "Province Name" if "Province Name" in df.columns else df.columns[1]
    
    # Select columns starting from BHS up to the rest of the facility counts
    bhs_idx = [i for i, col in enumerate(df.columns) if str(col).strip().upper() == "BHS"][0]
    metric_cols = df.columns[bhs_idx:].tolist()

    df_health = df[[province_col] + metric_cols].copy()
    df_health = df_health.dropna(subset=[province_col])

    # Resolve geographic domains
    df_health["clean_domain"] = df_health[province_col].apply(resolve_health_domain)
    df_health = df_health[df_health["clean_domain"] != ""].reset_index(drop=True)

    # Coerce metric columns to numeric
    for c in metric_cols:
        df_health[c] = df_health[c].astype(str).str.replace(",", "").str.strip()
        df_health[c] = pd.to_numeric(df_health[c], errors="coerce").fillna(0)

    # Aggregate by clean domain
    df_staging = df_health.groupby("clean_domain")[metric_cols].sum().reset_index()

    # Standardize column names to snake_case with health prefix
    df_staging.columns = [
        "clean_domain" if c == "clean_domain" else f"health_{c.lower().replace(' ', '_').replace('-', '_')}"
        for c in df_staging.columns
    ]

    # Export to staging directory
    out_path = STAGING_DIR / "staging_health.parquet"
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    df_staging.to_parquet(out_path, index=False)

    print(f"Generated {out_path.name} with {len(df_staging)} domain records.")
    print(df_staging.head(5).to_string())
    return out_path


# =============================================================================
# MAIN EXECUTION ENTRYPOINT
# =============================================================================
def main():
    print("=== Stage 1: Dataset Standardization & Staging ===")
    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    # Dynamic map based on exact shapefile domain names
    domain_map, raw_shape_domains = load_shapefile_domain_map(SHAPEFILE_PATH)

    # Execute cleaning steps across all datasets
    clean_population_dataset(domain_map)
    clean_deped_dataset(domain_map)
    clean_teaching_personnel_dataset(domain_map)
    clean_income_dataset(domain_map)
    clean_expenditure_dataset(domain_map)
    clean_poverty_dataset(domain_map)
    clean_higher_education_dataset(domain_map)
    clean_health_dataset(domain_map) 

if __name__ == "__main__":
    main()