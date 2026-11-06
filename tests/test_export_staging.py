"""
tests/test_export_staging.py
Member 5: Gabriel Dolar
Automated check for corrupted export roundtrips and staging.
"""

import gc
import os
import shutil
import time
import unittest
import numpy as np
import pandas as pd
from src.export_staging import StagingExporter


def safe_remove_dir(dir_path: str) -> None:
    """Helper to safely remove directories on Windows with file handles."""
    gc.collect()
    if os.path.exists(dir_path):
        for _ in range(3):
            try:
                shutil.rmtree(dir_path)
                break
            except PermissionError:
                time.sleep(0.2)
        else:
            shutil.rmtree(dir_path, ignore_errors=True)


class TestExportStaging(unittest.TestCase):

    def setUp(self):
        self.output_dir = ".test_outputs"
        self.staging_dir = ".test_staging"
        self.exporter = StagingExporter(output_dir=self.output_dir, staging_dir=self.staging_dir)
        self.exporter.prepare_staging()
        self.sample_df = pd.DataFrame({
            "country": ["Philippines", "Indonesia"],
            "continent": ["Asia", "Asia"],
            "year": [2007, 2007],
            "lifeExp": [71.64, 70.65],
            "pop": [91077287, 223547000],
            "gdpPercap": [3190.481586, 3540.651564]
        })

    def tearDown(self):
        safe_remove_dir(self.staging_dir)
        safe_remove_dir(self.output_dir)

    def _write_baseline_files(self):
        """Helper to create valid exported baseline files in staging."""
        csv_path = os.path.join(self.staging_dir, "canonical.csv")
        xlsx_path = os.path.join(self.staging_dir, "canonical.xlsx")
        json_path = os.path.join(self.staging_dir, "canonical.json")
        parquet_path = os.path.join(self.staging_dir, "canonical.parquet")

        self.sample_df.to_csv(csv_path, index=False)
        self.sample_df.to_excel(xlsx_path, sheet_name="observations", index=False)
        self.sample_df.to_json(json_path, orient="records")
        self.sample_df.to_parquet(parquet_path, index=False)

    def test_valid_exports_pass_validation(self):
        """Ensure verification succeeds when all exported files are valid."""
        self._write_baseline_files()
        passed = self.exporter.verify_roundtrip_exports(self.sample_df)
        self.assertTrue(passed, "Valid export files failed verification!")

    def test_corrupted_life_exp_fails_validation(self):
        """Ensure verification fails if lifeExp is modified."""
        self._write_baseline_files()
        json_path = os.path.join(self.staging_dir, "canonical.json")

        corrupted_df = self.sample_df.copy()
        corrupted_df.loc[0, "lifeExp"] = 999.99
        corrupted_df.to_json(json_path, orient="records")

        passed = self.exporter.verify_roundtrip_exports(self.sample_df)
        self.assertFalse(passed, "Verification failed to detect corrupted lifeExp!")

    def test_corrupted_country_fails_validation(self):
        """Ensure verification fails if text column 'country' is modified."""
        self._write_baseline_files()
        csv_path = os.path.join(self.staging_dir, "canonical.csv")

        corrupted_df = self.sample_df.copy()
        corrupted_df.loc[0, "country"] = "Corrupted Country"
        corrupted_df.to_csv(csv_path, index=False)

        passed = self.exporter.verify_roundtrip_exports(self.sample_df)
        self.assertFalse(passed, "Verification failed to detect corrupted country string!")

    def test_corrupted_population_fails_validation(self):
        """Ensure verification fails if integer column 'pop' is modified."""
        self._write_baseline_files()
        parquet_path = os.path.join(self.staging_dir, "canonical.parquet")

        corrupted_df = self.sample_df.copy()
        corrupted_df.loc[0, "pop"] = 99999999
        corrupted_df.to_parquet(parquet_path, index=False)

        passed = self.exporter.verify_roundtrip_exports(self.sample_df)
        self.assertFalse(passed, "Verification failed to detect corrupted population integer!")

    def test_blank_value_fails_validation(self):
        """Ensure verification fails if a blank/NaN value is introduced."""
        self._write_baseline_files()
        csv_path = os.path.join(self.staging_dir, "canonical.csv")

        corrupted_df = self.sample_df.copy()
        corrupted_df.loc[0, "country"] = np.nan
        corrupted_df.to_csv(csv_path, index=False)

        passed = self.exporter.verify_roundtrip_exports(self.sample_df)
        self.assertFalse(passed, "Verification failed to detect blank/NaN values!")


if __name__ == "__main__":
    unittest.main()