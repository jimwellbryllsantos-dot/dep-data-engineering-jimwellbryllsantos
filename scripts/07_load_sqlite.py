from __future__ import annotations

import argparse
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_PARQUET = BASE_DIR / "data" / "processed" / "final" / "master_dataset.parquet"
DEFAULT_CSV = BASE_DIR / "data" / "processed" / "final" / "master_dataset.csv"
DEFAULT_DB = BASE_DIR / "data" / "processed" / "final" / "poi_working.db"
TABLE_NAME = "master_dataset"


REQUIRED_COLUMNS = {
    "clean_domain",
    "total_population",
    "basic_schools_per_100k",
    "basic_student_teacher_ratio",
    "hospitals_per_100k",
    "family_poverty_incidence_2023_pct",
    "2023_all_income_groups",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load master_dataset.parquet/csv into a local SQLite database."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Optional source dataset. Defaults to master_dataset.parquet, then CSV.",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help=f"SQLite database path. Default: {DEFAULT_DB}",
    )
    return parser.parse_args()


def resolve_source(source_arg: Path | None) -> Path:
    if source_arg is not None:
        source = source_arg
        if not source.exists():
            raise FileNotFoundError(f"Source dataset not found: {source}")
        return source

    if DEFAULT_PARQUET.exists():
        return DEFAULT_PARQUET
    if DEFAULT_CSV.exists():
        return DEFAULT_CSV

    raise FileNotFoundError(
        "Working dataset not found. Expected either:\n"
        f"  - {DEFAULT_PARQUET}\n"
        f"  - {DEFAULT_CSV}"
    )


def load_source(source: Path) -> pd.DataFrame:
    if source.suffix.lower() == ".parquet":
        return pd.read_parquet(source)
    if source.suffix.lower() == ".csv":
        return pd.read_csv(source)
    raise ValueError("Source must be a .parquet or .csv file.")


def validate_dataset(df: pd.DataFrame) -> None:
    missing = sorted(REQUIRED_COLUMNS.difference(df.columns))
    if missing:
        raise ValueError(
            "The working dataset is missing columns required by the SQL milestone:\n"
            + "\n".join(f"  - {col}" for col in missing)
        )

    if df.empty:
        raise ValueError("The working dataset is empty.")

    if df["clean_domain"].duplicated().any():
        duplicates = int(df["clean_domain"].duplicated().sum())
        raise ValueError(
            f"'clean_domain' is not unique. Found {duplicates} duplicate rows."
        )


def main() -> None:
    args = parse_args()
    source = resolve_source(args.source)
    db_path = args.db
    db_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Loading working dataset: {source}")
    df = load_source(source)
    validate_dataset(df)

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")

        # Rebuild the table so the database always reflects the current working dataset.
        df.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)

        # Reviewer-friendly index on the analytical key.
        conn.execute(
            f'CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_clean_domain '
            f'ON {TABLE_NAME} (clean_domain);'
        )

        # Record enough metadata to verify what was loaded and when.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS load_metadata (
                source_file TEXT NOT NULL,
                row_count INTEGER NOT NULL,
                column_count INTEGER NOT NULL,
                loaded_at_utc TEXT NOT NULL
            )
            """
        )
        conn.execute("DELETE FROM load_metadata")
        conn.execute(
            """
            INSERT INTO load_metadata (
                source_file, row_count, column_count, loaded_at_utc
            ) VALUES (?, ?, ?, ?)
            """,
            (
                str(source.resolve()),
                int(df.shape[0]),
                int(df.shape[1]),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()

        db_row_count = conn.execute(
            f"SELECT COUNT(*) FROM {TABLE_NAME}"
        ).fetchone()[0]

    if db_row_count != len(df):
        raise RuntimeError(
            f"Database row-count check failed: source={len(df)}, database={db_row_count}"
        )

    print("\nDatabase load completed successfully.")
    print(f"  • Table      : {TABLE_NAME}")
    print(f"  • Rows       : {db_row_count}")
    print(f"  • Columns    : {len(df.columns)}")
    print(f"  • SQLite DB  : {db_path.resolve()}")


if __name__ == "__main__":
    main()
