from pathlib import Path
import re
import geopandas as gpd
import pandas as pd

# Files
ADM3_SHP = "data/raw/shape/phl_admbnda_adm3_psa_namria_20231106_2023-11-08.shp"
OUTPUT_SHP = "data/processed/Domains.shp"

# -------------------------------------------------------------------
# 1. DEFINE THE MASTER DOMAINS & THEIR HUC MAPPINGS
# -------------------------------------------------------------------
HUC_DOMAINS = {
    # NCR
    "City of Manila": ["manila"],
    "City of Mandaluyong": ["mandaluyong"],
    "City of San Juan": ["san juan"],
    "Quezon City": ["quezon city"],
    "City of Marikina": ["marikina"],
    "City of Pasig": ["pasig"],
    "City of Caloocan": ["caloocan"],
    "City of Malabon": ["malabon"],
    "City of Navotas": ["navotas"],
    "City of Valenzuela": ["valenzuela"],
    "City of Las Piñas": ["las piñas", "las pinas"],
    "City of Muntinlupa": ["muntinlupa"],
    "City of Parañaque": ["parañaque", "paranaque"],
    "Pasay City": ["pasay"],
    "City of Makati": ["makati"],
    "Pateros": ["pateros"],
    "City of Taguig": ["taguig"],
    # Regional HUCs / ICCs / Special Cities
    "City of Baguio": ["baguio"],
    "City of Angeles": ["angeles"],
    "City of Olongapo": ["olongapo"],
    "City of Lucena": ["lucena"],
    "City of Puerto Princesa": ["puerto princesa"],
    "City of Iloilo": ["iloilo city"],
    "City of Bacolod": ["bacolod"],
    "City of Cebu": ["cebu city"],
    "City of Lapu-Lapu (Opon)": ["lapu-lapu", "lapu lapu", "opon"],
    "City of Mandaue": ["mandaue"],
    "City of Tacloban": ["tacloban"],
    "City of Zamboanga": ["zamboanga city"],
    "Isabela City": ["isabela city"],
    "City of Iligan": ["iligan"],
    "City of Cagayan de Oro": ["cagayan de oro"],
    "City of Davao": ["davao city"],
    "City of General Santos (Dadiangas)": ["general santos", "gensan"],
    "City of Butuan": ["butuan"],
    "Cotabato City": ["cotabato city"],
}

PROVINCE_EXCLUSION_MAP = {
    "benguet": "Benguet (Excluding City of Baguio)",
    "pampanga": "Pampanga (Excluding City of Angeles)",
    "zambales": "Zambales (Excluding City of Olongapo)",
    "quezon": "Quezon (Excluding City of Lucena)",
    "palawan": "Palawan (Excluding City of Puerto Princesa)",
    "iloilo": "Iloilo (Excluding City of Iloilo)",
    "negros occidental": "Negros Occidental (Excluding City of Bacolod)",
    "cebu": "Cebu (Excluding the Cities of Cebu  Lapu-Lapu and Mandaue)",
    "leyte": "Leyte (Excluding City of Tacloban)",
    "zamboanga del sur": "Zamboanga Del Sur (Excluding City of Zamboanga)",
    "lanao del norte": "Lanao Del Norte (Excluding City of Iligan)",
    "misamis oriental": "Misamis Oriental (Excluding City of Cagayan de Oro)",
    "davao del sur": "Davao Del Sur (Excluding City of Davao)",
    "south cotabato": "South Cotabato (Excluding City of General Santos)",
    "agusan del norte": "Agusan Del Norte (Excluding City of Butuan)",
}


def clean_text(text):
    """Normalize string for robust matching."""
    if not text or pd.isna(text):
        return ""
    text = str(text).lower()
    text = re.sub(
        r"\(.*?\)", "", text
    )  # Remove parenthetical info like (Capital)
    text = (
        text.replace("city of ", "")
        .replace(" city", "")
        .replace(".", "")
        .replace(",", "")
        .strip()
    )
    return text


def map_row_to_domain(row, mun_col, prov_col):
    mun_raw = str(row[mun_col])
    prov_raw = str(row[prov_col])

    mun_clean = clean_text(mun_raw)
    prov_clean = clean_text(prov_raw)

    # STEP 1: Check if this municipality/city is an HUC/ICC
    for domain_name, aliases in HUC_DOMAINS.items():
        for alias in aliases:
            if clean_text(alias) == mun_clean or alias in mun_raw.lower():
                if (
                    alias == "isabela city"
                    and "basilan" not in prov_raw.lower()
                ):
                    continue
                return domain_name

    # STEP 2: Check if parent province has an "Excluding..." category
    for prov_key, domain_name in PROVINCE_EXCLUSION_MAP.items():
        if prov_key in prov_clean:
            return domain_name

    # STEP 3: Fallback to the standard Province Name as listed in shapefile
    return prov_raw.strip()


# -------------------------------------------------------------------
# 2. EXECUTE DISSOLVE PROCESS
# -------------------------------------------------------------------
def process_adm3_to_domains():
    print(f"Loading ADM3 shapefile: {ADM3_SHP}...")
    gdf = gpd.read_file(ADM3_SHP)

    # Automatically detect Municipality and Province columns
    mun_col = next(
        (c for c in ["adm3_name", "ADM3_EN", "ADM3_PCODE"] if c in gdf.columns),
        gdf.columns[0],
    )
    prov_col = next(
        (c for c in ["ADM2_EN", "adm2_name", "ADM2_PCODE"] if c in gdf.columns),
        gdf.columns[1],
    )

    print(f"Using Municipality Column: '{mun_col}', Province Column: '{prov_col}'")

    # Tag each ADM3 feature to its Domain by passing column names as args
    gdf["DOMAIN"] = gdf.apply(
        map_row_to_domain, axis=1, args=(mun_col, prov_col)
    )

    # Dissolve boundaries by DOMAIN
    print("Dissolving ADM3 boundaries to Domain polygons...")
    gdf_domain = gdf.dissolve(by="DOMAIN", as_index=False)

    # Keep only target column and geometry
    gdf_domain = gdf_domain[["DOMAIN", "geometry"]]

    # Save output
    Path(OUTPUT_SHP).parent.mkdir(parents=True, exist_ok=True)
    gdf_domain.to_file(OUTPUT_SHP)

    print(
        f"\n Success! Saved Domain Shapefile with {len(gdf_domain)} features to: {OUTPUT_SHP}"
    )


if __name__ == "__main__":
    process_adm3_to_domains()