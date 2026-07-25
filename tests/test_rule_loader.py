import unittest
import tempfile
import shutil
from pathlib import Path
from core.rule_loader import RuleLoader, Rule

class TestRuleLoader(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for rules
        self.test_dir = Path(tempfile.mkdtemp())
        self.rules_path = self.test_dir / "rules"
        self.rules_path.mkdir()

    def tearDown(self):
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)

    def test_load_no_rules(self):
        """Test loader with an empty directory."""
        loader = RuleLoader(rules_dir=str(self.rules_path))
        rules = loader.load_all()
        self.assertEqual(len(rules), 0)

    def test_load_single_rule(self):
        """Test loading a single rule with sections."""
        rule_content = (
            "# Test Rule\n\n"
            "## Section 1\n"
            "Content 1\n\n"
            "## Section 2\n"
            "Content 2"
        )
        rule_file = self.rules_path / "test_rule.md"
        rule_file.write_text(rule_content, encoding="utf-8")

        loader = RuleLoader(rules_dir=str(self.rules_path))
        rules = loader.load_all()

        self.assertIn("Test Rule", rules)
        rule = rules["Test Rule"]
        self.assertEqual(rule.filename, "test_rule.md")
        self.assertEqual(rule.get_section("Section 1"), "Content 1")
        self.assertEqual(rule.get_section("Section 2"), "Content 2")

    def test_load_rule_no_sections(self):
        """Test loading a rule without H2 headers."""
        rule_content = "Just some plain text content"
        rule_file = self.rules_path / "plain.md"
        rule_file.write_text(rule_content, encoding="utf-8")

        loader = RuleLoader(rules_dir=str(self.rules_path))
        rules = loader.load_all()

        self.assertIn("plain", rules)
        self.assertEqual(rules["plain"].get_section("General"), "Just some plain text content")

    def test_get_rule(self):
        """Test the get_rule method."""
        rule_content = "# My Rule\n## S1\nC1"
        (self.rules_path / "my_rule.md").write_text(rule_content, encoding="utf-8")

        loader = RuleLoader(rules_dir=str(self.rules_path))
        loader.load_all()
        
        rule = loader.get_rule("My Rule")
        self.assertIsNotNone(rule)
        self.assertEqual(rule.name, "My Rule")
        
        self.assertIsNone(loader.get_rule("Non Existent"))

    def test_invalid_directory(self):
        """Test loader with a non-existent directory."""
        loader = RuleLoader(rules_dir="non_existent_folder_123")
        rules = loader.load_all()
        self.assertEqual(rules, {})

if __name__ == "__main__":
    unittest.main()
