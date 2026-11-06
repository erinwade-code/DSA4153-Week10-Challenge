"""
tests/test_export_staging.py
Member 5: Gabriel Dolar
Automated check for corrupted export roundtrips and staging.
"""

import os
import shutil
import unittest
import pandas as pd
from src.export_staging import StagingExporter


class TestExportStaging(unittest.TestCase):

    def setUp(self):
        self.exporter = StagingExporter(output_dir="test_outputs", staging_dir=".test_staging")
        self.exporter.prepare_staging()
        self.sample_df = pd.DataFrame({
            "country": ["Philippines"],
            "continent": ["Asia"],
            "year": [2007],
            "lifeExp": [71.64],
            "pop": [91077287],
            "gdpPercap": [3190.481586]
        })

    def tearDown(self):
        if os.path.exists(".test_staging"):
            shutil.rmtree(".test_staging")
        if os.path.exists("test_outputs"):
            shutil.rmtree("test_outputs")

    def test_corrupted_export_fails_validation(self):
        """Ensure verification fails if exported files are modified or corrupted."""
        csv_path = os.path.join(".test_staging", "canonical.csv")
        xlsx_path = os.path.join(".test_staging", "canonical.xlsx")
        json_path = os.path.join(".test_staging", "canonical.json")
        parquet_path = os.path.join(".test_staging", "canonical.parquet")

        # Save valid baseline files
        self.sample_df.to_csv(csv_path, index=False)
        self.sample_df.to_excel(xlsx_path, sheet_name="observations", index=False)
        self.sample_df.to_json(json_path, orient="records")
        self.sample_df.to_parquet(parquet_path, index=False)

        # Deliberately corrupt JSON values
        corrupted_df = self.sample_df.copy()
        corrupted_df.loc[0, "lifeExp"] = 999.99
        corrupted_df.to_json(json_path, orient="records")

        # Assertion must return False
        passed = self.exporter.verify_roundtrip_exports(self.sample_df)
        self.assertFalse(passed, "Verification failed to detect corrupted export file!")


if __name__ == "__main__":
    unittest.main()