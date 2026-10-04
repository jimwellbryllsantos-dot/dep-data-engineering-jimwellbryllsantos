import re
import sys
from pathlib import Path
import pandas as pd
import geopandas as gpd
import networkx as nx

# Try importing osmnx; fall back to networkx if osmnx is unavailable
try:
    import osmnx as ox
    HAS_OSMNX = True
except ImportError:
    HAS_OSMNX = False

# ==========================================
# 1. CONFIGURATION & PATHS
# ==========================================
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_OSM_DIR = BASE_DIR / "data" / "raw" / "osm"
REF_DIR = BASE_DIR / "data" / "processed"
STAGING_DIR = REF_DIR / "staging"
SHAPEFILE_PATH = REF_DIR / "Domains.shp"

LGU_NAME_COLUMN = "DOMAIN"


def clean_str(val: str) -> str:
    """Standardizes domain strings for consistent matching across modules."""
    if pd.isna(val):
        return ""
    val = str(val).lower().strip()
    val = re.sub(r"\s+", " ", val)
    return val


def get_safe_filename(domain_name: str) -> str:
    """Replicates the exact filename sanitization from the OSMnx ingestion script."""
    return (
        domain_name.lower()
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace(".", "")
        .replace(",", "")
        .replace("/", "_")
    ) + ".graphml"


def parse_highway_type(val) -> str:
    """Unwraps OSM highway tags (which can be string or list) into a standardized category."""
    if isinstance(val, list):
        val = val[0] if len(val) > 0 else ""
    val_str = str(val).lower().strip() if pd.notna(val) else "unclassified"
    
    if "primary" in val_str:
        return "primary"
    elif "secondary" in val_str:
        return "secondary"
    elif "tertiary" in val_str:
        return "tertiary"
    elif "motorway" in val_str or "trunk" in val_str:
        return "trunk_motorway"
    elif "residential" in val_str or "living_street" in val_str:
        return "residential"
    else:
        return "other"


def process_single_graphml(graphml_path: Path) -> dict:
    """Reads a .graphml file and computes summary road network and facility metrics."""
    try:
        if HAS_OSMNX:
            G = ox.load_graphml(graphml_path)
        else:
            G = nx.read_graphml(graphml_path)
    except Exception as e:
        print(f"Error reading {graphml_path.name}: {e}")
        return {}

    # Extract nodes and edges summary
    nodes_count = G.number_of_nodes()
    edges_count = G.number_of_edges()

    if edges_count == 0:
        return {
            "osm_nodes_count": nodes_count,
            "osm_edges_count": 0,
            "osm_total_road_km": 0.0,
            "osm_bridges_count": 0,
            "osm_primary_road_km": 0.0,
            "osm_secondary_road_km": 0.0,
            "osm_tertiary_road_km": 0.0,
            "osm_trunk_motorway_km": 0.0,
            "osm_residential_road_km": 0.0,
            "osm_other_road_km": 0.0,
            "osm_avg_segment_length_m": 0.0,
        }

    # Extract edge attributes into a pandas DataFrame for vectorized calculations
    if HAS_OSMNX:
        # Convert graph edges directly to GeoDataFrame
        gdf_edges = ox.graph_to_gdfs(G, nodes=False, edges=True)
        df_edges = pd.DataFrame(gdf_edges)
    else:
        # Fallback: Extract edge data manually via NetworkX
        edge_data = []
        for u, v, k, d in G.edges(keys=True, data=True):
            edge_data.append(d)
        df_edges = pd.DataFrame(edge_data)

    # 1. Total Road Network Length
    if "length" in df_edges.columns:
        df_edges["length_m"] = pd.to_numeric(df_edges["length"], errors="coerce").fillna(0.0)
    else:
        df_edges["length_m"] = 0.0

    total_road_km = df_edges["length_m"].sum() / 1000.0
    avg_segment_len = df_edges["length_m"].mean() if len(df_edges) > 0 else 0.0

    # 2. Bridge Counts
    if "bridge" in df_edges.columns:
        is_bridge = df_edges["bridge"].astype(str).str.lower().isin(["yes", "true", "1"])
        bridges_count = is_bridge.sum()
    else:
        bridges_count = 0

    # 3. Road Length Breakdown by Functional Classification
    if "highway" in df_edges.columns:
        df_edges["highway_cat"] = df_edges["highway"].apply(parse_highway_type)
        highway_lengths = (
            df_edges.groupby("highway_cat")["length_m"].sum() / 1000.0
        ).to_dict()
    else:
        highway_lengths = {}

    return {
        "osm_nodes_count": nodes_count,
        "osm_edges_count": edges_count,
        "osm_total_road_km": round(total_road_km, 3),
        "osm_bridges_count": int(bridges_count),
        "osm_primary_road_km": round(highway_lengths.get("primary", 0.0), 3),
        "osm_secondary_road_km": round(highway_lengths.get("secondary", 0.0), 3),
        "osm_tertiary_road_km": round(highway_lengths.get("tertiary", 0.0), 3),
        "osm_trunk_motorway_km": round(highway_lengths.get("trunk_motorway", 0.0), 3),
        "osm_residential_road_km": round(highway_lengths.get("residential", 0.0), 3),
        "osm_other_road_km": round(highway_lengths.get("other", 0.0), 3),
        "osm_avg_segment_length_m": round(avg_segment_len, 2),
    }


def clean_osm_infrastructure_dataset(domain_map: dict = None) -> Path:
    """
    Reads shapefile master domains, summarizes corresponding .graphml files,
    and exports staging_infrastructure.parquet.
    """
    print("\n--- Processing & Summarizing OSM GraphML Infrastructure Data ---")

    # 1. Load Master Domains from Shapefile
    target_shp = SHAPEFILE_PATH
    if not target_shp.exists():
        spatial_files = list(REF_DIR.glob("*.shp")) + list(REF_DIR.glob("*.geojson"))
        if not spatial_files:
            raise FileNotFoundError(f"Master Shapefile not found at {SHAPEFILE_PATH}")
        target_shp = spatial_files[0]

    gdf_domains = gpd.read_file(target_shp)
    
    # Identify domain column name
    domain_col = LGU_NAME_COLUMN if LGU_NAME_COLUMN in gdf_domains.columns else None
    if not domain_col:
        for c in ["clean_domain", "domain", "ADM2_EN", "NAME_1", "NAME_2"]:
            if c in gdf_domains.columns:
                domain_col = c
                break
    if not domain_col:
        domain_col = gdf_domains.columns[0]

    raw_domains = gdf_domains[domain_col].dropna().astype(str).tolist()
    print(f"Loaded {len(raw_domains)} master domains from shapefile: {target_shp.name}")

    # 2. Iterate Over Master Domains and Parse GraphML Files
    records = []
    found_files_count = 0

    for raw_domain in raw_domains:
        clean_domain_name = clean_str(raw_domain)
        safe_fname = get_safe_filename(raw_domain)
        graphml_file = RAW_OSM_DIR / safe_fname

        domain_metrics = {
            "clean_domain": clean_domain_name,
            "osm_nodes_count": 0,
            "osm_edges_count": 0,
            "osm_total_road_km": 0.0,
            "osm_bridges_count": 0,
            "osm_primary_road_km": 0.0,
            "osm_secondary_road_km": 0.0,
            "osm_tertiary_road_km": 0.0,
            "osm_trunk_motorway_km": 0.0,
            "osm_residential_road_km": 0.0,
            "osm_other_road_km": 0.0,
            "osm_avg_segment_length_m": 0.0,
        }

        if graphml_file.exists():
            found_files_count += 1
            extracted_data = process_single_graphml(graphml_file)
            domain_metrics.update(extracted_data)
        else:
            print(f"ℹGraphML missing for domain '{raw_domain}' ({safe_fname}). Filled with zeroes.")

        records.append(domain_metrics)

    df_staging = pd.DataFrame(records)

    # 3. Export to Parquet Staging
    out_path = STAGING_DIR / "staging_infrastructure.parquet"
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    df_staging.to_parquet(out_path, index=False)

    print(f"\nProcessing complete:")
    print(f"   • GraphML Files Processed : {found_files_count} / {len(raw_domains)}")
    print(f"   • Staging Dataset Exported: {out_path.name} ({len(df_staging)} domain records)")
    print("\nSample Output:")
    print(df_staging.head(5).to_string())

    return out_path


if __name__ == "__main__":
    clean_osm_infrastructure_dataset()