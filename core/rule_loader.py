from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class Rule:
    """Represents a parsed analysis rule."""
    def __init__(self, name: str, filename: str, content: str, sections: Dict[str, str]):
        self.name = name
        self.filename = filename
        self.content = content
        self.sections = sections

    def __repr__(self):
        return f"Rule(name='{self.name}', filename='{self.filename}')"

    def get_section(self, section_name: str) -> Optional[str]:
        """Retrieve content of a specific section."""
        return self.sections.get(section_name)

class RuleLoader:
    """Loads and parses markdown rules from the rules directory."""
    def __init__(self, rules_dir: str = "rules"):
        self.rules_dir = Path(rules_dir)
        self.rules: Dict[str, Rule] = {}

    def load_all(self) -> Dict[str, Rule]:
        """Scans the rules directory and loads all .md files."""
        if not self.rules_dir.exists() or not self.rules_dir.is_dir():
            logger.error(f"Rules directory not found: {self.rules_dir}")
            return {}

        for file in self.rules_dir.glob("*.md"):
            try:
                content = file.read_text(encoding="utf-8")
                rule_name = file.stem
                sections = self._parse_markdown(content)
                
                # Use the first H1 header as the rule name if available
                lines = content.splitlines()
                for line in lines:
                    if line.startswith("# "):
                        rule_name = line[2:].strip()
                        break

                self.rules[rule_name] = Rule(
                    name=rule_name,
                    filename=file.name,
                    content=content,
                    sections=sections
                )
                logger.info(f"Loaded rule: {rule_name} from {file.name}")
            except Exception as e:
                logger.error(f"Failed to load rule {file.name}: {e}")

        return self.rules

    def get_rule(self, rule_name: str) -> Optional[Rule]:
        """Returns a rule by its name."""
        return self.rules.get(rule_name)

    def _parse_markdown(self, content: str) -> Dict[str, str]:
        """
        Simple markdown parser that splits content by H2 (##) headers.
        """
        sections = {}
        current_section = "Header"
        current_content = []

        for line in content.splitlines():
            if line.startswith("## "):
                # Save previous section
                if current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                
                # Start new section
                current_section = line[3:].strip()
                current_content = []
            else:
                current_content.append(line)

        # Save the last section
        if current_content:
            sections[current_section] = "\n".join(current_content).strip()
        
        # If there's only the default "Header" section, rename it to "General"
        if list(sections.keys()) == ["Header"]:
            content = sections.pop("Header")
            sections["General"] = content

        return sections

if __name__ == "__main__":
    # Simple test run
    loader = RuleLoader()
    loaded_rules = loader.load_all()
    print(f"Loaded {len(loaded_rules)} rules.")
    for name, rule in loaded_rules.items():
        print(f"- {name} (Sections: {list(rule.sections.keys())})")
