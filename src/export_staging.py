"""
src/export_staging.py
Member 5: Gabriel Dolar
Handles staging export directories, canonical export validation/reloading,
and safe execution context.
"""

import os
import shutil
import pandas as pd
import numpy as np


class StagingExporter:
    """Manages staging output execution and round-trip export verification."""

    def __init__(self, output_dir: str = "outputs", staging_dir: str = ".staging_outputs"):
        self.output_dir = output_dir
        self.staging_dir = staging_dir

    def prepare_staging(self) -> None:
        """Creates or cleans the staging directory to prevent dirty writes."""
        if os.path.exists(self.staging_dir):
            shutil.rmtree(self.staging_dir, ignore_errors=True)
        os.makedirs(self.staging_dir, exist_ok=True)

    def publish_staging(self) -> None:
        """Promotes staging outputs to final output directory upon validation success."""
        os.makedirs(self.output_dir, exist_ok=True)
        for item in os.listdir(self.staging_dir):
            src_path = os.path.join(self.staging_dir, item)
            dst_path = os.path.join(self.output_dir, item)
            if os.path.isdir(src_path):
                if os.path.exists(dst_path):
                    shutil.rmtree(dst_path, ignore_errors=True)
                shutil.copytree(src_path, dst_path)
            else:
                shutil.copy2(src_path, dst_path)
        shutil.rmtree(self.staging_dir, ignore_errors=True)

    def verify_roundtrip_exports(
        self, canonical_df: pd.DataFrame, abs_tol: float = 1e-8
    ) -> bool:
        """
        Reloads exported canonical files (.csv, .xlsx, .json, .parquet),
        reapplies schema, and compares all 6 columns with pre-export canonical table.
        """
        export_files = {
            "csv": os.path.join(self.staging_dir, "canonical.csv"),
            "xlsx": os.path.join(self.staging_dir, "canonical.xlsx"),
            "json": os.path.join(self.staging_dir, "canonical.json"),
            "parquet": os.path.join(self.staging_dir, "canonical.parquet"),
        }

        canonical_cols = ["country", "continent", "year", "lifeExp", "pop", "gdpPercap"]
        canonical_sorted = canonical_df.sort_values(by=["country", "year"]).reset_index(drop=True)

        for fmt, filepath in export_files.items():
            if not os.path.exists(filepath):
                return False

            if fmt == "csv":
                reloaded = pd.read_csv(filepath)
            elif fmt == "xlsx":
                reloaded = pd.read_excel(filepath, sheet_name="observations")
            elif fmt == "json":
                reloaded = pd.read_json(filepath, orient="records")
            elif fmt == "parquet":
                reloaded = pd.read_parquet(filepath)

            # 1. Verify schema column presence and order
            if list(reloaded.columns) != canonical_cols:
                return False

            # 2. Check row count equality
            if len(reloaded) != len(canonical_sorted):
                return False

            # 3. Check for unauthorized missing/NaN values across ALL columns
            if reloaded[canonical_cols].isna().any().any():
                return False

            # Re-apply schema & types
            reloaded["year"] = reloaded["year"].astype(int)
            reloaded["pop"] = reloaded["pop"].astype(int)
            reloaded["lifeExp"] = reloaded["lifeExp"].astype(float)
            reloaded["gdpPercap"] = reloaded["gdpPercap"].astype(float)

            # Sort by keys to align rows before comparison
            reloaded_sorted = reloaded.sort_values(by=["country", "year"]).reset_index(drop=True)

            # 4. Exact text matching (country, continent)
            for col in ["country", "continent"]:
                if not (reloaded_sorted[col].astype(str) == canonical_sorted[col].astype(str)).all():
                    return False

            # 5. Exact integer matching (year, pop)
            for col in ["year", "pop"]:
                if not (reloaded_sorted[col].values == canonical_sorted[col].values).all():
                    return False

            # 6. Floating-point numerical matching within tolerance (lifeExp, gdpPercap)
            diff_life = np.abs(reloaded_sorted["lifeExp"].values - canonical_sorted["lifeExp"].values)
            diff_gdp = np.abs(reloaded_sorted["gdpPercap"].values - canonical_sorted["gdpPercap"].values)

            if np.max(diff_life) > abs_tol or np.max(diff_gdp) > abs_tol:
                return False

        return True