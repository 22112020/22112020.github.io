import unittest
import tempfile
import shutil
from pathlib import Path
from core.result_finder import ResultFinder

class TestResultFinder(unittest.TestCase):
    def setUp(self):
        # Create a temporary test directory
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_root = self.test_dir / "Togelku"
        self.project_root.mkdir()
        
        # Create pasaran_luna and data_harian directories
        self.pasaran_luna_dir = self.project_root / "pasaran_luna"
        self.data_harian_dir = self.project_root / "data_harian"
        self.pasaran_luna_dir.mkdir()
        self.data_harian_dir.mkdir()

    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.test_dir)

    def test_source_priority_pasaran_luna(self):
        """Test that pasaran_luna is used as primary source."""
        # Create market history in pasaran_luna
        oregon_dir = self.pasaran_luna_dir / "oregon03"
        oregon_dir.mkdir()
        history_file = oregon_dir / "history.md"
        history_file.write_text("""
History Nomor OREGON03
23-07-2026 10:30:00 Kamis 1990 8207
24-07-2026 11:00:00 Kamis 1991 5555
""")
        
        finder = ResultFinder(project_root=str(self.project_root))
        results = finder.get_available_results()
        
        # Should find OREGON03 from pasaran_luna
        self.assertIn("OREGON03", results)
        self.assertEqual(results["OREGON03"]["period"], "1991")
        self.assertEqual(results["OREGON03"]["result"], "5555")

    def test_fallback_to_data_harian(self):
        """Test fallback to data_harian when pasaran_luna is empty."""
        # Create daily file in data_harian
        daily_file = self.data_harian_dir / "24-07-2026-Luna.md"
        daily_file.write_text("""
History Nomor BANGKOK 0130
24-07-2026 09:48:10 Kamis 1453 3152
""")
        
        finder = ResultFinder(project_root=str(self.project_root))
        results = finder.get_available_results()
        
        # Should find BANGKOK 0130 from data_harian (fallback)
        self.assertIn("BANGKOK 0130", results)
        self.assertEqual(results["BANGKOK 0130"]["period"], "1453")
        self.assertEqual(results["BANGKOK 0130"]["result"], "3152")

    def test_no_date_filtering(self):
        """Test that results are not filtered by system date."""
        # Create history with older date
        market_dir = self.pasaran_luna_dir / "singapore"
        market_dir.mkdir()
        history_file = market_dir / "history.md"
        history_file.write_text("""
History Nomor SINGAPORE
22-07-2026 18:45:00 Rabu 1427 8863
""")
        
        finder = ResultFinder(project_root=str(self.project_root))
        results = finder.get_available_results()
        
        # Should include older date (no date filtering)
        self.assertIn("SINGAPORE", results)
        self.assertEqual(results["SINGAPORE"]["period"], "1427")

    def test_data_sanitization(self):
        """Test that UI artifacts are filtered out."""
        # Create file with UI artifacts
        daily_file = self.data_harian_dir / "test.md"
        daily_file.write_text("""
History Nomor TEST
labelthumbnail
24-07-2026 12:00:00 Kamis 1001 9999
Play Now
btn_live
thumbnail
""")
        
        finder = ResultFinder(project_root=str(self.project_root))
        
        # Parse the content
        content = daily_file.read_text(encoding="utf-8")
        sanitized = finder._sanitize_content(content)
        
        # UI artifacts should be removed
        self.assertNotIn("labelthumbnail", sanitized)
        self.assertNotIn("Play Now", sanitized)
        self.assertNotIn("btn_live", sanitized)
        self.assertNotIn("thumbnail", sanitized)
        
        # Valid data should remain
        self.assertIn("History Nomor TEST", sanitized)
        self.assertIn("24-07-2026 12:00:00 Kamis 1001 9999", sanitized)

    def test_latest_result_by_datetime(self):
        """Test that latest result is determined by datetime, not system date."""
        # Create history with multiple entries
        market_dir = self.pasaran_luna_dir / "bangkok0130"
        market_dir.mkdir()
        history_file = market_dir / "history.md"
        history_file.write_text("""
History Nomor BANGKOK 0130
22-07-2026 09:48:10 Rabu 1452 8108
23-07-2026 09:48:10 Kamis 1453 3152
24-07-2026 09:48:10 Jumat 1454 1541
""")
        
        finder = ResultFinder(project_root=str(self.project_root))
        latest = finder.get_latest_result("BANGKOK 0130")
        
        # Should return the newest by datetime (24-07-2026)
        self.assertIsNotNone(latest)
        self.assertEqual(latest["period"], "1454")
        self.assertEqual(latest["result"], "1541")

    def test_content_validation(self):
        """Test that results are validated by content completeness."""
        # Create file with incomplete data
        daily_file = self.data_harian_dir / "incomplete.md"
        daily_file.write_text("""
History Nomor INCOMPLETE
24-07-2026 12:00:00 Kamis  # Missing period and result
24-07-2026 12:00:00 Kamis 1001  # Missing result
24-07-2026 12:00:00 Kamis 1001 9999  # Complete
""")
        
        finder = ResultFinder(project_root=str(self.project_root))
        results = finder.get_available_results()
        
        # Should only include complete records
        self.assertIn("INCOMPLETE", results)
        self.assertEqual(results["INCOMPLETE"]["period"], "1001")
        self.assertEqual(results["INCOMPLETE"]["result"], "9999")

    def test_multiple_sources_combined(self):
        """Test that results from both sources are combined."""
        # Create in pasaran_luna
        market_dir = self.pasaran_luna_dir / "oregon03"
        market_dir.mkdir()
        (market_dir / "history.md").write_text("""
History Nomor OREGON03
24-07-2026 10:00:00 Kamis 1990 8207
""")
        
        # Create in data_harian
        (self.data_harian_dir / "test.md").write_text("""
History Nomor BANGKOK 0130
24-07-2026 09:00:00 Kamis 1453 3152
""")
        
        finder = ResultFinder(project_root=str(self.project_root))
        sections = finder.get_all_sections()
        results = finder.get_available_results()
        
        # Should find sections from both sources
        self.assertIn("OREGON03", sections)
        self.assertIn("BANGKOK 0130", sections)
        
        # Should have results from both sources
        self.assertIn("OREGON03", results)
        self.assertIn("BANGKOK 0130", results)

    def test_empty_sources(self):
        """Test behavior with no data in either source."""
        finder = ResultFinder(project_root=str(self.project_root))
        
        sections = finder.get_all_sections()
        results = finder.get_available_results()
        
        # Should return empty results
        self.assertEqual(sections, [])
        self.assertEqual(results, {})

    def test_project_boundary_restriction(self):
        """Test that ResultFinder only searches within project boundaries."""
        # Create a file outside the Togelku directory
        outside_file = self.test_dir / "outside.md"
        outside_file.write_text("History Nomor OUTSIDE\n24-07-2026 12:00:00 Kamis 9999 1234", encoding="utf-8")
        
        finder = ResultFinder(project_root=str(self.project_root))
        sections = finder.get_all_sections()
        
        # Should not include "OUTSIDE" since it's not in project directories
        self.assertNotIn("OUTSIDE", sections)


if __name__ == "__main__":
    unittest.main()
