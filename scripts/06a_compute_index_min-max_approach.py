import sys
from pathlib import Path
import numpy as np
import pandas as pd

# ==========================================
# 1. PATH CONFIGURATION
# ==========================================
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_PARQUET = (
    BASE_DIR / "data" / "processed" / "final" / "master_dataset.parquet"
)
OUTPUT_DIR = BASE_DIR / "data" / "processed" / "final"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================
def _get_series(
    df: pd.DataFrame, candidates: list[str], default: float = 0.0
) -> pd.Series:
  """Safely retrieves a numeric column across potential naming variations."""
  for col in candidates:
    if col in df.columns:
      return pd.to_numeric(df[col], errors="coerce").fillna(default)
  return pd.Series(default, index=df.index, dtype=np.float64)


def min_max_scale(series: pd.Series, invert: bool = False) -> pd.Series:
  """Transforms a numeric series into a [0, 1] scale using Min-Max Normalization.

  Formula: (X - Min) / (Max - Min) Maps the absolute lowest observed value to
  0.0 and highest value strictly to 1.0, preserving relative magnitude
  distances between observations. If invert=True, inverts the scale (lowest raw
  value receives 1.0).
  """
  if series.empty or series.nunique() <= 1:
    return pd.Series(0.5, index=series.index)

  min_val, max_val = series.min(), series.max()
  if max_val == min_val:
    return pd.Series(0.5, index=series.index)

  scaled = (series - min_val) / (max_val - min_val)
  return (1.0 - scaled) if invert else scaled


# ==========================================
# 3. COMPUTE INDEX SCORES & RANKS
# ==========================================
def compute_provincial_index_scores_minmax() -> Path:
  print(
      "\n--- Step 6a: Computing Multi-Sector Sub-Index Scores & Ranks"
      " (Min-Max Normalized) ---"
  )
  if not INPUT_PARQUET.exists():
    raise FileNotFoundError(f"Master dataset not found at: {INPUT_PARQUET}")

  df_master = pd.read_parquet(INPUT_PARQUET)
  df_out = pd.DataFrame()

  # 1. Preserve Domain Identifiers
  id_cols = [
      c
      for c in [
          "clean_domain",
          "domain",
          "psgc_code",
          "region",
          "province",
          "land_area_sqkm",
      ]
      if c in df_master.columns
  ]
  if not id_cols:
    id_cols = (
        ["clean_domain"]
        if "clean_domain" in df_master.columns
        else [df_master.columns[0]]
    )

  for col in id_cols:
    df_out[col] = df_master[col].fillna("").astype(str)

  # 2. Retrieve Spatial & Per-Capita Indicators
  # Infrastructure Indicators
  road_density_spatial = _get_series(
      df_master,
      [
          "road_density_per_sqkm",
          "osm_road_density_per_sqkm",
          "road_density_sqkm",
      ],
  )
  road_density_capita = _get_series(
      df_master,
      [
          "road_density_km_per_100k",
          "road_density_km_per_10k",
          "total_road_km_per_100k",
          "osm_road_density_km_per_100k",
      ],
  )
  primary_road_ratio = _get_series(
      df_master, ["primary_road_ratio", "osm_primary_road_ratio"]
  )
  bridges_spatial = _get_series(
      df_master, ["bridges_per_100sqkm", "osm_bridges_per_100sqkm"]
  )
  bridges_capita = _get_series(
      df_master, ["bridges_per_100k", "osm_bridges_per_100k"]
  )
  segment_length = _get_series(
      df_master, ["osm_avg_segment_length_m", "avg_segment_length_m"]
  )

  # Economic Indicators
  income_per_capita = _get_series(
      df_master,
      [
          "mean_per_capita_income",
          "per_capita_income",
          "income_per_capita",
          "mean_income",
          "annual_per_capita_income",
          "2023_all_income_groups",
      ],
  )
  poverty_pct = _get_series(
      df_master,
      [
          "poverty_incidence_pct",
          "poverty_incidence",
          "poverty_rate",
          "poverty_pct",
          "family_poverty_incidence_2023_pct",
          "poverty_threshold_2023",
      ],
  )
  expenditure_per_capita = _get_series(
      df_master,
      [
          "mean_per_capita_expenditure",
          "per_capita_expenditure",
          "expenditure_per_capita",
          "mean_expenditure",
          "2023_exp_all_income_groups",
      ],
  )

  # Education Indicators
  basic_student_teacher_ratio = _get_series(
      df_master,
      ["basic_student_teacher_ratio", "student_teacher_ratio"],
  )
  schools_spatial = _get_series(
      df_master,
      ["basic_schools_per_10sqkm", "schools_per_10sqkm"],
  )
  schools_capita = _get_series(
      df_master,
      ["basic_schools_per_100k", "schools_per_100k", "schools_per_10k"],
  )
  hei_spatial = _get_series(df_master, ["hei_per_100sqkm"])
  hei_capita = _get_series(df_master, ["hei_per_100k"])
  hei_student_faculty_ratio = _get_series(
      df_master,
      ["higher_ed_student_faculty_ratio", "hei_student_faculty_ratio"],
  )
  hei_graduates_capita = _get_series(
      df_master,
      ["higher_ed_graduates_per_100k", "graduates_per_100k"],
  )

  # Health Indicators
  hospitals_spatial = _get_series(
      df_master,
      ["hospitals_per_100sqkm", "hospital_per_100sqkm"],
  )
  hospitals_capita = _get_series(
      df_master,
      ["hospitals_per_100k", "hospital_per_100k"],
  )
  primary_health_spatial = _get_series(
      df_master,
      ["primary_health_per_100sqkm", "aggregated_primary_health_per_100sqkm"],
  )
  primary_health_capita = _get_series(
      df_master,
      [
          "primary_health_per_100k",
          "primary_health_per_10k",
          "aggregated_primary_health_per_100k",
          "aggregated_primary_health_per_10k",
      ],
  )

  # 3. Calculate Min-Max Based Sector Sub-Indices (0-100 Scale)
  # Infrastructure Sub-Index
  df_out["score_infrastructure"] = (
      0.25 * min_max_scale(road_density_spatial)
      + 0.20 * min_max_scale(road_density_capita)
      + 0.25 * min_max_scale(primary_road_ratio)
      + 0.15 * min_max_scale(bridges_spatial)
      + 0.15 * min_max_scale(segment_length, invert=True)
  ) * 100.0

  # Economic Sub-Index
  df_out["score_economic"] = (
      0.60 * min_max_scale(income_per_capita)
      + 0.20 * min_max_scale(poverty_pct, invert=True)
      + 0.20 * min_max_scale(expenditure_per_capita)
  ) * 100.0

  # Education Sub-Index
  df_out["score_education"] = (
      0.25 * min_max_scale(basic_student_teacher_ratio, invert=True)
      + 0.15 * min_max_scale(schools_spatial)
      + 0.10 * min_max_scale(schools_capita)
      + 0.10 * min_max_scale(hei_spatial)
      + 0.15 * min_max_scale(hei_capita)
      + 0.15 * min_max_scale(hei_student_faculty_ratio, invert=True)
      + 0.10 * min_max_scale(hei_graduates_capita)
  ) * 100.0

  # Health Sub-Index
  df_out["score_health"] = (
      0.30 * min_max_scale(hospitals_spatial)
      + 0.30 * min_max_scale(hospitals_capita)
      + 0.20 * min_max_scale(primary_health_spatial)
      + 0.20 * min_max_scale(primary_health_capita)
  ) * 100.0

  # 4. Compute Overall Composite Development Score
  df_out["overall_composite_score"] = (
      0.25 * df_out["score_infrastructure"]
      + 0.40 * df_out["score_economic"]
      + 0.25 * df_out["score_education"]
      + 0.10 * df_out["score_health"]
  )

  # 5. Compute Ranks (Rank 1 = Highest Score / Best Performance)
  df_out["rank_infrastructure"] = (
      df_out["score_infrastructure"]
      .rank(ascending=False, method="min")
      .astype(int)
  )
  df_out["rank_economic"] = (
      df_out["score_economic"].rank(ascending=False, method="min").astype(int)
  )
  df_out["rank_education"] = (
      df_out["score_education"].rank(ascending=False, method="min").astype(int)
  )
  df_out["rank_health"] = (
      df_out["score_health"].rank(ascending=False, method="min").astype(int)
  )
  df_out["rank_overall"] = (
      df_out["overall_composite_score"]
      .rank(ascending=False, method="min")
      .astype(int)
  )

  # Sort output by overall rank
  df_out = df_out.sort_values(by="rank_overall").reset_index(drop=True)

  # 6. Export Streamlined Analytical Datasets
  out_parquet = OUTPUT_DIR / "analytical_master_dataset_minmax.parquet"
  out_csv = OUTPUT_DIR / "analytical_master_dataset_minmax.csv"

  df_out.to_parquet(out_parquet, index=False)
  df_out.to_csv(out_csv, index=False)

  print("Step 6a complete! Min-Max analytical dataset exported.")
  print(f"   • Parquet: {out_parquet.resolve()}")
  print(f"   • CSV    : {out_csv.resolve()}")
  print(f"   • Columns: {list(df_out.columns)}\n")
  print(df_out.head(10).to_string())

  return out_parquet


if __name__ == "__main__":
  compute_provincial_index_scores_minmax()