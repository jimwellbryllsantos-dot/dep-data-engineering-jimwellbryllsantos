from pathlib import Path
import time
import geopandas as gpd
import osmnx as ox

# ==========================================
# 1. CONFIGURATION & PARAMETERS
# ==========================================

# INPUT / OUTPUT PATHS
NAMRIA_SHP_PATH = "data/processed/Domains.shp"  # Updated Path
GRAPHML_OUTPUT_DIR = Path("data/raw/osm")
RAW_API_CACHE_DIR = Path("data/raw/osm_overpass_cache")

GRAPHML_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
RAW_API_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# SHAPEFILE ATTRIBUTE CONTROL
LGU_NAME_COLUMN = "DOMAIN"  # match the processed domain attribute

# OVERPASS API PARAMETERS
NETWORK_TYPE = "drive"
RETAIN_ALL = True

# NETWORK & RESILIENCE SETTINGS
MAX_RETRIES = 3
RETRY_DELAY = 120
ox.settings.requests_timeout = 4800  # Increased to 1hr20mins for large combined domains (e.g., provincial remainder polygons)
ox.settings.user_agent = (
    "PhilippineInfrastructureResearch/1.0 (jimwellbryllsantos@gmail.com)"
)

# RAW RESPONSE RETENTION
ox.settings.use_cache = True
ox.settings.cache_folder = RAW_API_CACHE_DIR


# ==========================================
# 2. BATCH EXTRACTION WITH RETRY LOGIC
# ==========================================


def run_osm_ingestion():
    print(f"--- 1. Loading Domain Boundaries: {NAMRIA_SHP_PATH} ---")
    if not Path(NAMRIA_SHP_PATH).exists():
        print(f"Error: File not found at '{NAMRIA_SHP_PATH}'.")
        return

    gdf_domains = gpd.read_file(NAMRIA_SHP_PATH)
    print(f"Loaded {len(gdf_domains)} domain polygons.")

    if LGU_NAME_COLUMN not in gdf_domains.columns:
        print(
            f"Error: Column '{LGU_NAME_COLUMN}' missing. Available columns: {list(gdf_domains.columns)}"
        )
        return

    # Ensure EPSG:4326 WGS 84 spatial reference for OSMnx
    if gdf_domains.crs is None or gdf_domains.crs.to_string() != "EPSG:4326":
        print("Reprojecting geometries to EPSG:4326 (WGS 84)...")
        gdf_domains = gdf_domains.to_crs(epsg=4326)

    print("\n--- 2. Executing Overpass API Extraction ---")

    successful_count = 0
    skipped_count = 0

    for idx, row in gdf_domains.iterrows():
        domain_name = str(row[LGU_NAME_COLUMN])
        polygon = row["geometry"]

        # Sanitize filename for 113 domains (handles parenthetical domain names safely)
        safe_filename = (
            domain_name.lower()
            .replace(" ", "_")
            .replace("(", "")
            .replace(")", "")
            .replace(".", "")
            .replace(",", "")
            .replace("/", "_")
        )
        file_path = GRAPHML_OUTPUT_DIR / f"{safe_filename}.graphml"

        # RESUME CHECK: Skip if already extracted
        if file_path.exists():
            print(
                f"[{idx+1}/{len(gdf_domains)}] Skipping {domain_name}: Output already exists."
            )
            successful_count += 1
            continue

        # RETRY LOOP
        success = False
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                print(
                    f"[{idx+1}/{len(gdf_domains)}] Extracting network for: {domain_name} (Attempt {attempt}/{MAX_RETRIES})..."
                )

                # Query Overpass by domain polygon
                G = ox.graph_from_polygon(
                    polygon, network_type=NETWORK_TYPE, retain_all=RETAIN_ALL
                )

                # Export GraphML
                ox.save_graphml(G, filepath=file_path)
                print(f"   Saved: {file_path}")

                successful_count += 1
                success = True
                break

            except Exception as e:
                print(f"   Attempt {attempt} failed for '{domain_name}': {e}")
                if attempt < MAX_RETRIES:
                    print(
                        f"   ⏳ Waiting {RETRY_DELAY} seconds before retrying..."
                    )
                    time.sleep(RETRY_DELAY)

        if not success:
            print(
                f"Failed to extract '{domain_name}' after {MAX_RETRIES} attempts. Moving to next domain.\n"
            )
            skipped_count += 1

    print("\n--- 3. Ingestion Summary ---")
    print(f"• Successfully available: {successful_count} / {len(gdf_domains)}")
    print(f"• Failed domains:         {skipped_count}")
    print(f"• GraphML Directory:      {GRAPHML_OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    run_osm_ingestion()