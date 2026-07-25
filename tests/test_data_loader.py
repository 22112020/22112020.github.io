import unittest
import shutil
from pathlib import Path
from core.data_loader import DataLoader

class TestDataLoader(unittest.TestCase):
    def setUp(self):
        # Create test directory structure
        self.test_dir = Path("/mnt/d/Alfian/Togelku/tests/.temp_data_loader")
        self.project_root = self.test_dir / "Togelku"
        self.project_root.mkdir(parents=True, exist_ok=True)
        
        # Create data directories
        self.data_harian_dir = self.project_root / "data_harian"
        self.pasaran_luna_dir = self.project_root / "pasaran_luna"
        self.data_harian_dir.mkdir(exist_ok=True)
        self.pasaran_luna_dir.mkdir(exist_ok=True)

    def tearDown(self):
        # Clean up test directory
        if self.project_root.exists():
            shutil.rmtree(self.project_root)

    def test_valid_data_loading(self):
        """Test loading valid market data."""
        # Create market directory and history file
        oregon_dir = self.pasaran_luna_dir / "oregon03"
        oregon_dir.mkdir(exist_ok=True)
        
        history_file = oregon_dir / "history.md"
        history_file.write_text("""History Nomor OREGON03

24-07-2026 11:04:38 Friday 1990 8207
23-07-2026 11:04:38 Thursday 1989 5555
""")
        
        # Load market data
        loader = DataLoader(project_root=str(self.project_root))
        market_data = loader.load_market("OREGON03")
        
        # Verify structure
        self.assertEqual(market_data["name"], "OREGON03")
        self.assertEqual(market_data["latest"]["result"], "8207")
        self.assertEqual(market_data["latest"]["period"], "1990")
        self.assertEqual(len(market_data["history"]), 2)
        self.assertEqual(market_data["stats"]["total_records"], 2)
        self.assertEqual(market_data["stats"]["last_record"], "24-07-2026")

    def test_empty_market(self):
        """Test behavior with empty market directory."""
        # Create empty market directory
        empty_dir = self.pasaran_luna_dir / "empty"
        empty_dir.mkdir(exist_ok=True)
        
        # Try to load non-existent market
        loader = DataLoader(project_root=str(self.project_root))
        
        with self.assertRaises(ValueError):
            loader.load_market("EMPTY")

    def test_missing_history(self):
        """Test behavior with missing history file."""
        # Create market directory without history file
        missing_dir = self.pasaran_luna_dir / "missing"
        missing_dir.mkdir(exist_ok=True)
        
        # Try to load market with no history
        loader = DataLoader(project_root=str(self.project_root))
        
        with self.assertRaises(ValueError):
            loader.load_market("MISSING")

    def test_invalid_history_line(self):
        """Test handling of invalid history lines."""
        # Create market with invalid history lines
        invalid_dir = self.pasaran_luna_dir / "invalid"
        invalid_dir.mkdir(exist_ok=True)
        
        history_file = invalid_dir / "history.md"
        history_file.write_text("""History Nomor INVALID

24-07-2026 11:04:38 Friday 1990 8207
INVALID LINE WITH WRONG FORMAT
23-07-2026 11:04:38 Thursday 1989 5555
""")
        
        # Load market data
        loader = DataLoader(project_root=str(self.project_root))
        market_data = loader.load_market("INVALID")
        
        # Should skip invalid line and load valid ones
        self.assertEqual(len(market_data["history"]), 2)
        self.assertEqual(market_data["history"][0]["result"], "8207")
        self.assertEqual(market_data["history"][1]["result"], "5555")

    def test_multiple_markets(self):
        """Test loading multiple markets."""
        # Create multiple market directories
        markets = ["OREGON03", "BANGKOK0130", "SINGAPORE"]
        
        for market in markets:
            market_dir = self.pasaran_luna_dir / market.lower().replace(" ", "")
            market_dir.mkdir(exist_ok=True)
            
            history_file = market_dir / "history.md"
            history_file.write_text(f"""History Nomor {market}

24-07-2026 11:04:38 Friday 1990 8207
""")
        
        # Load all markets
        loader = DataLoader(project_root=str(self.project_root))
        all_data = loader.load_all_markets()
        
        # Verify all markets loaded
        self.assertEqual(all_data["count"], 3)
        self.assertIn("OREGON03", all_data["markets"])
        self.assertIn("BANGKOK0130", all_data["markets"])
        self.assertIn("SINGAPORE", all_data["markets"])

    def test_source_priority(self):
        """Test source priority (pasaran_luna over data_harian)."""
        # Create market in both sources
        market_dir = self.pasaran_luna_dir / "priority"
        market_dir.mkdir(exist_ok=True)
        
        history_file = market_dir / "history.md"
        history_file.write_text("""History Nomor PRIORITY

24-07-2026 11:04:38 Friday 1990 8207
""")
        
        # Create daily file with different data
        daily_file = self.data_harian_dir / "24-07-2026-Luna.md"
        daily_file.write_text("""PRIORITY POOL
9999
[PERIODE : 1990]
""")
        
        # Load market data
        loader = DataLoader(project_root=str(self.project_root))
        market_data = loader.load_market("PRIORITY")
        
        # Should use pasaran_luna data (8207), not data_harian (9999)
        self.assertEqual(market_data["latest"]["result"], "8207")
        self.assertEqual(market_data["source"], "pasaran_luna")

    def test_lazy_loading(self):
        """Test lazy loading of history data."""
        # Create market with extensive history
        market_dir = self.pasaran_luna_dir / "lazy"
        market_dir.mkdir(exist_ok=True)
        
        history_file = market_dir / "history.md"
        history_lines = ["History Nomor LAZY"]
        
        # Add 150 history lines
        for i in range(150):
            period = 1990 + i
            result = f"{i:04d}"
            history_lines.append(f"24-07-2026 11:04:38 Friday {period} {result}")
        
        history_file.write_text("\n".join(history_lines))
        
        # Load market data
        loader = DataLoader(project_root=str(self.project_root))
        market_data = loader.load_market("LAZY")
        
        # Should load only 100 records (default limit)
        self.assertEqual(len(market_data["history"]), 100)
        self.assertEqual(market_data["stats"]["total_records"], 100)

    def test_metadata_generation(self):
        """Test UTC+7 metadata generation."""
        # Create minimal market
        market_dir = self.pasaran_luna_dir / "meta"
        market_dir.mkdir(exist_ok=True)
        
        history_file = market_dir / "history.md"
        history_file.write_text("""History Nomor META

24-07-2026 11:04:38 Friday 1990 8207
""")
        
        # Load market data
        loader = DataLoader(project_root=str(self.project_root))
        market_data = loader.load_market("META")
        
        # Verify metadata
        metadata = market_data["metadata"]
        self.assertIn("generated_at", metadata)
        self.assertEqual(metadata["timezone"], "Asia/Jakarta")
        self.assertEqual(metadata["version"], "1.0")
        
        # Verify timestamp format
        import re
        timestamp_pattern = r"\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2}"
        self.assertTrue(re.match(timestamp_pattern, metadata["generated_at"]))


if __name__ == "__main__":
    unittest.main()
