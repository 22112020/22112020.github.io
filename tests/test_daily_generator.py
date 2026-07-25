import unittest
import tempfile
import shutil
from pathlib import Path
from core.daily_generator import DailyGenerator

class TestDailyGenerator(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = Path(tempfile.mkdtemp())
        self.data_dir = self.test_dir / "data_harian"
        self.data_dir.mkdir()

    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.test_dir)

    def test_today_date_format(self):
        """Test that today's date is in correct format."""
        generator = DailyGenerator(data_dir=str(self.data_dir))
        today_date = generator.get_today_date()
        
        # Should be in DD-MM-YYYY format
        self.assertEqual(len(today_date), 10)
        self.assertTrue(today_date.count('-') == 2)
        
        # Should be able to parse as date
        day, month, year = today_date.split('-')
        self.assertEqual(len(day), 2)
        self.assertEqual(len(month), 2)
        self.assertEqual(len(year), 4)

    def test_template_filename_format(self):
        """Test template filename generation."""
        generator = DailyGenerator(data_dir=str(self.data_dir))
        
        # Test with specific date
        filename = generator.get_template_filename("24-07-2026")
        self.assertEqual(filename, "24-07-2026-Luna.md")
        
        # Test with today's date
        today_filename = generator.get_template_filename()
        self.assertTrue(today_filename.endswith("-Luna.md"))

    def test_template_path_generation(self):
        """Test template path generation."""
        generator = DailyGenerator(data_dir=str(self.data_dir))
        path = generator.get_template_path("25-07-2026")
        
        expected = self.data_dir / "25-07-2026-Luna.md"
        self.assertEqual(path, expected)

    def test_generate_blank_template(self):
        """Test creating a blank template file."""
        generator = DailyGenerator(data_dir=str(self.data_dir))
        
        # Generate template for a specific date
        created = generator.generate_if_missing("26-07-2026")
        
        # Should return True (file was created)
        self.assertTrue(created)
        
        # File should exist
        template_path = self.data_dir / "26-07-2026-Luna.md"
        self.assertTrue(template_path.exists())
        
        # File should be empty (blank template)
        self.assertEqual(template_path.stat().st_size, 0)

    def test_no_overwrite_existing(self):
        """Test that existing files are not overwritten."""
        generator = DailyGenerator(data_dir=str(self.data_dir))
        
        # Create a template file manually
        template_path = self.data_dir / "27-07-2026-Luna.md"
        template_path.write_text("Some existing content", encoding="utf-8")
        
        # Try to generate again
        created = generator.generate_if_missing("27-07-2026")
        
        # Should return False (file already existed)
        self.assertFalse(created)
        
        # Content should be preserved
        content = template_path.read_text(encoding="utf-8")
        self.assertEqual(content, "Some existing content")

    def test_generate_today(self):
        """Test generating template for today's date."""
        generator = DailyGenerator(data_dir=str(self.data_dir))
        
        # Get today's date
        today_date = generator.get_today_date()
        
        # Generate today's template
        created = generator.generate_today()
        
        # File should exist
        template_path = self.data_dir / f"{today_date}-Luna.md"
        self.assertTrue(template_path.exists())

    def test_template_exists_check(self):
        """Test checking if template exists."""
        generator = DailyGenerator(data_dir=str(self.data_dir))
        
        # Check non-existent template
        self.assertFalse(generator.is_template_exists("30-07-2026"))
        
        # Create a template
        template_path = self.data_dir / "30-07-2026-Luna.md"
        template_path.touch()
        
        # Check existing template
        self.assertTrue(generator.is_template_exists("30-07-2026"))

    def test_data_directory_creation(self):
        """Test that data directory is created if missing."""
        # Use a non-existent directory
        non_existent_dir = self.test_dir / "non_existent_data"
        generator = DailyGenerator(data_dir=str(non_existent_dir))
        
        # Generate template (should create directory)
        created = generator.generate_if_missing("31-07-2026")
        
        # Should create the file
        self.assertTrue(created)
        
        # Directory should be created
        self.assertTrue(non_existent_dir.exists())
        
        # File should exist
        template_path = non_existent_dir / "31-07-2026-Luna.md"
        self.assertTrue(template_path.exists())

    def test_multiple_dates(self):
        """Test generating templates for multiple dates."""
        generator = DailyGenerator(data_dir=str(self.data_dir))
        
        dates = ["01-08-2026", "02-08-2026", "03-08-2026"]
        
        for date in dates:
            created = generator.generate_if_missing(date)
            self.assertTrue(created)
            
            template_path = self.data_dir / f"{date}-Luna.md"
            self.assertTrue(template_path.exists())
        
        # Try to generate again (should return False)
        for date in dates:
            created = generator.generate_if_missing(date)
            self.assertFalse(created)


if __name__ == "__main__":
    unittest.main()
