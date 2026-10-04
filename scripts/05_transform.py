import re
import sys
from pathlib import Path
import geopandas as gpd
import numpy as np
import pandas as pd

# ==========================================
# 1. PATH CONFIGURATION & DIRECTORIES
# ==========================================
BASE_DIR = Path(__file__).resolve().parent.parent
REF_DIR = BASE_DIR / "data" / "processed"
STAGING_DIR = REF_DIR / "staging"
OUTPUT_DIR = REF_DIR / "final"
SHAPEFILE_PATH = REF_DIR / "Domains.shp"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ==========================================
# 2. DOMAIN & DATA HELPER UTILITIES
# ==========================================
def clean_str(val: str) -> str:
  """Standardizes string values for consistent master key alignment."""
  if pd.isna(val):
    return ""
  val = str(val).lower().strip()
  val = re.sub(r"\s+", " ", val)
  return val


def load_master_domains(filepath: Path) -> pd.DataFrame:
  """Loads authoritative master domains AND calculates land area (sq km) directly

  from the spatial shapefile geometry.
  """
  target_path = filepath
  if not target_path.exists():
    spatial_files = (
        list(REF_DIR.glob("*.shp"))
        + list(REF_DIR.glob("*.geojson"))
        + list(REF_DIR.glob("*.gpkg"))
    )
    if not spatial_files:
      print(f"CRITICAL ERROR: Domain shapefile not found at {filepath}")
      sys.exit(1)
    target_path = spatial_files[0]

  gdf = gpd.read_file(target_path)

  # Autodetect domain column name
  domain_col = None
  for col in [
      "DOMAIN",
      "clean_domain",
      "domain",
      "ADM2_EN",
      "ADM1_EN",
      "NAME_1",
      "NAME_2",
  ]:
    if col in gdf.columns:
      domain_col = col
      break
  if not domain_col:
    domain_col = gdf.columns[0]

  # --- SPATIAL AREA CALCULATION ---
  # Reproject geometry to EPSG:3123 (PRS92 / Philippines Zone 3 or UTM 51N) or EPSG:3857 for accurate meter measurements
  try:
    gdf_projected = gdf.to_crs(epsg=3123)
  except Exception:
    # Fallback projection if 3123 CRS definition is missing locally
    gdf_projected = gdf.to_crs(epsg=3857)

  # Calculate geometry area in sq meters and convert to sq kilometers
  gdf["land_area_sqkm"] = gdf_projected.geometry.area / 1_000_000.0

  df_master = pd.DataFrame()
  df_master["clean_domain"] = (
      gdf.dropna(subset=[domain_col])[domain_col].astype(str).apply(clean_str)
  )
  df_master["land_area_sqkm"] = gdf["land_area_sqkm"].values

  # Deduplicate while preserving non-zero land area
  df_master = (
      df_master.groupby("clean_domain", as_index=False)
      .agg({"land_area_sqkm": "sum"})
      .reset_index(drop=True)
  )

  print(
      f"Loaded {len(df_master)} master domains from {target_path.name} with"
      " land area (sq km) calculated."
  )
  return df_master


def _sum_columns(
    df: pd.DataFrame, keywords: list[str], exact_cols: list[str] = None
) -> pd.Series:
  """Dynamically finds and sums numeric columns matching exact names or keyword patterns."""
  matched_cols = set()

  if exact_cols:
    matched_cols.update([c for c in exact_cols if c in df.columns])

  if keywords:
    for col in df.columns:
      col_lower = col.lower()
      if any(kw in col_lower for kw in keywords):
        matched_cols.add(col)

  if not matched_cols:
    return pd.Series(0.0, index=df.index, dtype=np.float64)

  return (
      df[list(matched_cols)]
      .apply(pd.to_numeric, errors="coerce")
      .fillna(0.0)
      .sum(axis=1)
  )


def _get_series(
    df: pd.DataFrame, candidates: list[str], default: float = 0.0
) -> pd.Series:
  """Safely retrieves a single numeric series across potential naming variations."""
  for col in candidates:
    if col in df.columns:
      return pd.to_numeric(df[col], errors="coerce").fillna(default)
  return pd.Series(default, index=df.index, dtype=np.float64)


# ==========================================
# 3. CONSOLIDATION & MERGE LOGIC
# ==========================================
def combine_all_staging_files(df_master: pd.DataFrame) -> pd.DataFrame:
  """Merges all staged datasets onto master domains."""
  staging_files = {
      "Population": STAGING_DIR / "staging_population.parquet",
      "Education Basic": STAGING_DIR / "staging_education_basic.parquet",
      "Education Personnel": STAGING_DIR
      / "staging_education_personnel.parquet",
      "Income": STAGING_DIR / "staging_income.parquet",
      "Expenditure": STAGING_DIR / "staging_expenditure.parquet",
      "Poverty": STAGING_DIR / "staging_poverty.parquet",
      "Higher Education": STAGING_DIR / "staging_higher_education.parquet",
      "Health Facilities": STAGING_DIR / "staging_health.parquet",
      "OSM Infrastructure": STAGING_DIR / "staging_infrastructure.parquet",
  }

  df_combined = df_master.copy()

  print("\n--- Merging Staging Files onto Master Domain List ---")
  for name, file_path in staging_files.items():
    if not file_path.exists():
      print(
          f"WARNING: Staging file for {name} missing at {file_path.name}."
          " Skipping."
      )
      continue

    df_stage = pd.read_parquet(file_path)
    df_stage["clean_domain"] = (
        df_stage["clean_domain"].astype(str).apply(clean_str)
    )

    # Drop duplicate columns before merging (except clean_domain)
    duplicate_cols = [
        c
        for c in df_stage.columns
        if c in df_combined.columns and c != "clean_domain"
    ]
    if duplicate_cols:
      df_stage = df_stage.drop(columns=duplicate_cols)

    df_combined = pd.merge(df_combined, df_stage, on="clean_domain", how="left")
    print(
        f"  • Merged {name:20s} | Shape after merge: {df_combined.shape}"
    )

  return df_combined


# ==========================================
# 4. FEATURE ENGINEERING & AGGREGATION LOGIC
# ==========================================
def engineer_per_capita_and_spatial_features(df: pd.DataFrame) -> pd.DataFrame:
  """Computes both spatial density (per sq km) and per-capita rates across

  infrastructure, health, and education sectors.
  """
  print("\n--- Computing Spatial & Per-Capita Rates/Densities ---")
  df_feat = df.copy()

  # Retrieve denominators safely
  pop_series = _get_series(
      df_feat, ["total_population", "population", "pop", "pop_total"]
  )
  pop_safe = pop_series.replace(0, np.nan)

  area_series = _get_series(df_feat, ["land_area_sqkm"])
  area_safe = area_series.replace(0, np.nan)

  # 1. Infrastructure Features (Per Capita + Spatial Density)
  total_road_km = _get_series(
      df_feat, ["osm_total_road_km", "total_road_km", "road_km"]
  )
  primary_road_km = _get_series(
      df_feat, ["osm_primary_road_km", "primary_road_km"]
  )
  bridges_count = _sum_columns(
      df_feat,
      keywords=["bridge"],
      exact_cols=["osm_bridges_count", "bridges_count"],
  )

  # Per Capita
  df_feat["road_density_km_per_100k"] = (total_road_km / pop_safe) * 100_000
  df_feat["primary_road_ratio"] = primary_road_km / total_road_km.replace(
      0, np.nan
  )
  df_feat["bridges_per_100k"] = (bridges_count / pop_safe) * 100_000

  # Spatial Density
  df_feat["road_density_per_sqkm"] = total_road_km / area_safe
  df_feat["bridges_per_100sqkm"] = (bridges_count / area_safe) * 100.0

  # 2. Education Features
  deped_teacher_cols = [
      "Master Teacher IV",
      "Master Teacher III",
      "Master Teacher II",
      "Master Teacher I",
      "Teacher III",
      "Teacher II",
      "Teacher I",
      "SPED Teacher V",
      "SPED Teacher IV",
      "SPED Teacher III",
      "SPED Teacher II",
      "SPED Teacher I",
      "Instructor III",
      "Instructor II",
      "Instructor I",
      "Special Science Teacher I",
  ]

  basic_teachers_total = _sum_columns(
      df_feat, keywords=[], exact_cols=deped_teacher_cols
  )
  basic_enrolment_total = _get_series(df_feat, ["total_enrollment"])
  basic_schools_count = _get_series(df_feat, ["total_schools"])

  df_feat["basic_teachers_total"] = basic_teachers_total
  df_feat["basic_enrolment_total"] = basic_enrolment_total
  df_feat["basic_schools_count"] = basic_schools_count

  # Education Rates
  df_feat["basic_schools_per_100k"] = (basic_schools_count / pop_safe) * 100_000
  df_feat["basic_schools_per_10sqkm"] = (basic_schools_count / area_safe) * 10.0
  df_feat["basic_student_teacher_ratio"] = (
      basic_enrolment_total / basic_teachers_total.replace(0, np.nan)
  )

  # Higher Education
  hei_count = _get_series(df_feat, ["total_heis"])
  hei_faculty_total = _get_series(df_feat, ["higher_ed_faculty"])
  hei_enrolment_total = _get_series(df_feat, ["higher_ed_enrolment"])
  hei_graduates_total = _get_series(df_feat, ["higher_ed_graduates"])

  df_feat["hei_count"] = hei_count
  df_feat["hei_faculty_total"] = hei_faculty_total
  df_feat["hei_enrolment_total"] = hei_enrolment_total
  df_feat["hei_graduates_total"] = hei_graduates_total

  df_feat["hei_per_100k"] = (hei_count / pop_safe) * 100_000
  df_feat["hei_per_100sqkm"] = (hei_count / area_safe) * 100.0
  df_feat["higher_ed_student_faculty_ratio"] = (
      hei_enrolment_total / hei_faculty_total.replace(0, np.nan)
  )
  df_feat["higher_ed_graduates_per_100k"] = (
      hei_graduates_total / pop_safe
  ) * 100_000

  # 3. Health Facilities Features (Per Capita + Spatial Density)
  rhu_count = _sum_columns(
      df_feat, keywords=["rhu", "rural_health"], exact_cols=["rhu_count"]
  )
  bhs_count = _sum_columns(
      df_feat, keywords=["bhs", "barangay_health"], exact_cols=["bhs_count"]
  )
  birthing_count = _sum_columns(
      df_feat,
      keywords=["birthing", "maternity"],
      exact_cols=["birthing_home_count"],
  )
  hospital_count = _sum_columns(
      df_feat, keywords=["hospital"], exact_cols=["hospital_count"]
  )
  infirmary_count = _sum_columns(
      df_feat, keywords=["infirmary"], exact_cols=["infirmary_count"]
  )
  cho_count = _sum_columns(
      df_feat, keywords=["cho", "city_health"], exact_cols=["cho_count"]
  )

  primary_care_total = rhu_count + bhs_count + birthing_count + cho_count
  total_health_facilities = primary_care_total + hospital_count + infirmary_count

  df_feat["aggregated_primary_health_total"] = primary_care_total
  df_feat["aggregated_all_health_facilities_total"] = total_health_facilities

  # Health Per Capita
  df_feat["primary_health_per_100k"] = (primary_care_total / pop_safe) * 100_000
  df_feat["hospitals_per_100k"] = (hospital_count / pop_safe) * 100_000

  # Health Spatial Density
  df_feat["hospitals_per_100sqkm"] = (hospital_count / area_safe) * 100.0
  df_feat["primary_health_per_100sqkm"] = (
      primary_care_total / area_safe
  ) * 100.0

  # Clean missing/infinite rates
  rate_cols = [
      "land_area_sqkm",
      "road_density_km_per_100k",
      "road_density_per_sqkm",
      "primary_road_ratio",
      "bridges_per_100k",
      "bridges_per_100sqkm",
      "basic_schools_per_100k",
      "basic_schools_per_10sqkm",
      "basic_student_teacher_ratio",
      "hei_per_100k",
      "hei_per_100sqkm",
      "higher_ed_student_faculty_ratio",
      "higher_ed_graduates_per_100k",
      "primary_health_per_100k",
      "primary_health_per_100sqkm",
      "hospitals_per_100k",
      "hospitals_per_100sqkm",
  ]
  for col in rate_cols:
    df_feat[col] = (
        df_feat[col].replace([np.inf, -np.inf], np.nan).fillna(0.0)
    )

  print("  • Successfully computed spatial density and per-capita metrics.")
  return df_feat


# ==========================================
# 5. TRANSFORMATION & TYPE-CASTING LOGIC
# ==========================================
def transform_datatypes(df: pd.DataFrame) -> pd.DataFrame:
  """Ensures exact data types, fills logical missing values, and casts counts vs rates."""
  print("\n--- Transforming Column Data Types & Handling Nulls ---")
  df_transformed = df.copy()

  df_transformed["clean_domain"] = df_transformed["clean_domain"].astype(str)

  float_keywords = [
      "pct",
      "incidence",
      "rate",
      "threshold",
      "mean",
      "avg",
      "per_capita",
      "km",
      "sqkm",
      "length",
      "ratio",
      "density",
      "per_10k",
      "per_100k",
      "per_1k",
      "per_100sqkm",
      "per_10sqkm",
      "per_sqkm",
  ]

  count_keywords = [
      "count",
      "total",
      "enrolment",
      "enrollment",
      "graduates",
      "faculty",
      "personnel",
      "bhs",
      "rhu",
      "hospital",
      "cho",
      "infirmary",
      "birthing",
      "clinic",
      "license",
      "government",
      "private",
      "nodes",
      "edges",
      "bridges",
      "schools",
      "facilities",
      "population",
      "teachers",
      "students",
  ]

  for col in df_transformed.columns:
    if col == "clean_domain":
      continue

    col_lower = col.lower()

    if any(kw in col_lower for kw in float_keywords):
      df_transformed[col] = pd.to_numeric(
          df_transformed[col], errors="coerce"
      ).astype(np.float64)
      df_transformed[col] = (
          df_transformed[col].replace([np.inf, -np.inf], np.nan).fillna(0.0)
      )

    elif any(kw in col_lower for kw in count_keywords):
      df_transformed[col] = (
          pd.to_numeric(df_transformed[col], errors="coerce")
          .fillna(0)
          .astype(np.int64)
      )

    else:
      if pd.api.types.is_numeric_dtype(df_transformed[col]):
        df_transformed[col] = (
            pd.to_numeric(df_transformed[col], errors="coerce")
            .replace([np.inf, -np.inf], np.nan)
            .fillna(0.0)
        )

  return df_transformed


# ==========================================
# 6. INTEGRITY & VALIDATION SUITE
# ==========================================
def validate_master_dataset(
    df_master: pd.DataFrame, df_final: pd.DataFrame
) -> bool:
  """Runs data integrity checks on master dataset."""
  print("\n==================================================")
  print("         MASTER DATASET VALIDATION REPORT          ")
  print("==================================================")

  is_valid = True

  # 1. Row count
  expected_rows = len(df_master)
  actual_rows = len(df_final)
  print(
      f"1. Row Count Check       : Actual {actual_rows} / Expected"
      f" {expected_rows}"
  )
  if actual_rows != expected_rows:
    print("   FAIL: Row count mismatch!")
    is_valid = False
  else:
    print("   PASS: Exact row count match.")

  # 2. Key Uniqueness
  duplicate_domains = df_final["clean_domain"].duplicated().sum()
  print(
      f"2. Domain Uniqueness     : {duplicate_domains} duplicate keys found"
  )
  if duplicate_domains > 0:
    print("   FAIL: Primary key 'clean_domain' contains duplicates!")
    is_valid = False
  else:
    print("   PASS: 'clean_domain' is unique.")

  # 3. Area Null Check
  zero_area_count = (df_final["land_area_sqkm"] <= 0).sum()
  print(f"3. Spatial Area Check    : {zero_area_count} domains with zero/invalid area")
  if zero_area_count > 0:
    print("   WARNING: Some domains have zero land area!")

  # 4. Infinite Values Check
  numeric_df = df_final.select_dtypes(include=[np.number])
  inf_count = np.isinf(numeric_df.values).sum()
  print(f"4. Infinite Values Check : {inf_count} infinite values found")
  if inf_count > 0:
    print("   FAIL: Numeric columns contain infinite values!")
    is_valid = False
  else:
    print("   PASS: Zero infinite values.")

  print("--------------------------------------------------")
  return is_valid


# ==========================================
# 7. MAIN EXECUTION PIPELINE
# ==========================================
def main():
  print("=== Step 5: Master Dataset Consolidation & Spatial Feature Engineering ===")

  df_master = load_master_domains(SHAPEFILE_PATH)
  df_combined = combine_all_staging_files(df_master)
  df_featured = engineer_per_capita_and_spatial_features(df_combined)
  df_final = transform_datatypes(df_featured)

  is_valid = validate_master_dataset(df_master, df_final)

  out_parquet = OUTPUT_DIR / "master_dataset.parquet"
  out_csv = OUTPUT_DIR / "master_dataset.csv"

  for col in df_final.select_dtypes(include=["object"]).columns:
    df_final[col] = df_final[col].fillna("").astype(str)

  df_final.to_parquet(out_parquet, index=False)
  df_final.to_csv(out_csv, index=False)

  print("\nMASTER DATASET EXPORTED SUCCESSFULLY:")
  print(f"   • Parquet: {out_parquet.resolve()}")
  print(f"   • CSV    : {out_csv.resolve()}")
  print(
      f"   • Dimensions: {df_final.shape[0]} rows × {df_final.shape[1]} columns"
  )
  print(df_final.head(10).to_string())

  if not is_valid:
    print(
        "\nVERIFICATION ALERT: Validation checks raised warnings or errors."
    )
    sys.exit(1)
  else:
    print("\nPIPELINE COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
  main()