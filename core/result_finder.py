#!/usr/bin/env python3
"""ResultFinder - Extract results from History Nomor blocks with source priority.

This module provides a reusable class for finding and extracting lottery results
from "History Nomor" sections in markdown files within the Togelku project.

Key Features:
- Source Priority: pasaran_luna/ (primary), data_harian/ (fallback)
- Data Sanitization: Filters UI artifacts (labelthumbnail, Play Now, etc.)
- Date-Independent: Validates by content, not system date
- UTC+7 Timezone: All datetime operations use Asia/Jakarta timezone

The History Nomor format:
    History Nomor <SECTION>
    <date> <time> <day> <period> <result> [extra ...]

Example:
    History Nomor BANGKOK 0130
    23-07-2026 09:48:10 Kamis 1453 3152 3272 8908
    22-07-2026 09:48:14 Rabu 1452 8108 5159 0443
"""

import re
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Set, Optional

# Luna fixed timezone: Asia/Jakarta (UTC+7)
LUNA_TIMEZONE = timezone(timedelta(hours=7))

# UI artifacts to filter out (data sanitization)
UI_ARTIFACTS = {
    "labelthumbnail",
    "thumbnail", 
    "Play Now",
    "btn_live"
}


class ResultFinder:
    """Find and extract lottery results with source priority and data sanitization."""
    
    def __init__(self, project_root: Optional[str] = None):
        """Initialize ResultFinder with project root directory.
        
        Args:
            project_root: Path to Togelku project root directory
        """
        self.project_root = Path(project_root).expanduser().resolve() if project_root else Path.cwd().resolve()
        if project_root is None:
            for candidate in [Path(__file__).resolve().parents[1], Path(".").resolve()]:
                if (candidate / "core").exists() and (candidate / "data_harian").exists():
                    self.project_root = candidate.resolve()
                    break
        # Look for pasaran_luna and data_harian within project root
        self.pasaran_luna_dir = self.project_root / "pasaran_luna"
        self.data_harian_dir = self.project_root / "data_harian"

    def get_available_results(self) -> Dict[str, Dict[str, str]]:
        """Get all available results from both sources.
        
        Uses source priority: pasaran_luna/ first, data_harian/ fallback.
        If same section exists in both sources, pasaran_luna takes priority.
        
        Returns:
            Dictionary mapping section -> {"period": ..., "result": ...}
            Includes all valid results regardless of date.
        """
        results = {}
        
        # Primary source: pasaran_luna/ (takes priority)
        for section, dt, period, result in self._find_from_pasaran_luna():
            # Keep the newest result for each section
            if section not in results or dt > self._parse_datetime(results[section]["date"], results[section]["time"]):
                results[section] = {"period": period, "result": result, "date": dt.strftime("%d-%m-%Y"), "time": dt.strftime("%H:%M:%S")}
        
        # Fallback source: data_harian/ (add sections not in primary source)
        for section, dt, period, result in self._find_from_data_harian():
            # Only add if section not already in results from primary source
            if section not in results:
                results[section] = {"period": period, "result": result, "date": dt.strftime("%d-%m-%Y"), "time": dt.strftime("%H:%M:%S")}
        
        # Convert to final format (remove date/time from output)
        final_results = {}
        for section, data in results.items():
            final_results[section] = {"period": data["period"], "result": data["result"]}
        
        return final_results

    def get_latest_result(self, section: str) -> Optional[Dict[str, str]]:
        """Get the latest result for a specific section.
        
        Latest means newest valid record by datetime, not system date.
        
        Args:
            section: Section name to search for
            
        Returns:
            Dictionary with {"period": ..., "result": ...} or None if not found
        """
        latest_dt: Optional[datetime] = None
        latest_period: Optional[str] = None
        latest_result: Optional[str] = None
        latest_source: Optional[str] = None
        
        # Search both sources with priority
        for source_func, source_name in [(self._find_from_pasaran_luna, "pasaran_luna"),
                                          (self._find_from_data_harian, "data_harian")]:
            for sec, dt, period, result in source_func():
                if sec and sec.upper() == section.upper():
                    if latest_dt is None or dt > latest_dt:
                        latest_dt = dt
                        latest_period = period
                        latest_result = result
                        latest_source = source_name
        
        if latest_dt and latest_period and latest_result:
            return {"period": latest_period, "result": latest_result, "source": latest_source}
        return None

    def get_all_sections(self) -> List[str]:
        """Get all section names found in History Nomor blocks.
        
        Returns:
            Sorted list of all section names from both sources
        """
        sections: Set[str] = set()
        
        # Search both sources
        for source_func in [self._find_from_pasaran_luna, self._find_from_data_harian]:
            for section, _, _, _ in source_func():
                if section:
                    sections.add(section)
        
        return sorted(sections)

    def parse_history_blocks(self, content: str) -> List[Dict[str, str]]:
        """Parse History Nomor blocks from markdown content.
        
        Args:
            content: Markdown content to parse
            
        Returns:
            List of dictionaries, each containing section, date, time, period, result
        """
        # Apply data sanitization first
        sanitized_content = self._sanitize_content(content)
        
        results = []
        current_section = None
        
        for line in sanitized_content.splitlines():
            line = line.strip()
            
            # Detect a new "History Nomor" block (with or without # prefix)
            m = re.match(r"#?\s*History Nomor\s+(.+)", line, re.IGNORECASE)
            if m:
                current_section = m.group(1).strip().upper()
                continue
                
            if not line or line.startswith("#") or line.startswith("--"):
                continue
                
            parts = line.split()
            if len(parts) < 5:
                continue
                
            date, time, _day = parts[0], parts[1], parts[2]
            period, result = parts[3], parts[4]
            
            if current_section:
                results.append({
                    "section": current_section,
                    "date": date,
                    "time": time,
                    "period": period,
                    "result": result
                })
        
        return results

    def _sanitize_content(self, content: str) -> str:
        """Remove UI artifacts from content.
        
        Filters out:
        - labelthumbnail
        - thumbnail
        - Play Now
        - btn_live
        
        Args:
            content: Raw content to sanitize
            
        Returns:
            Sanitized content with UI artifacts removed
        """
        lines = content.splitlines()
        sanitized_lines = []
        
        for line in lines:
            stripped_line = line.strip()
            # Skip lines that are only UI artifacts
            if stripped_line in UI_ARTIFACTS:
                continue
            # Skip lines that start with UI artifacts
            if any(artifact in stripped_line for artifact in UI_ARTIFACTS):
                continue
            sanitized_lines.append(line)
        
        return "\n".join(sanitized_lines)

    def _find_from_pasaran_luna(self):
        """Find results from pasaran_luna/ (primary source).
        
        Yields:
            Tuple of (section, datetime, period, result) for all valid entries
        """
        if not self.pasaran_luna_dir.exists():
            return
        
        # Find all market directories
        for market_dir in self.pasaran_luna_dir.iterdir():
            if market_dir.is_dir():
                history_file = market_dir / "history.md"
                if history_file.exists():
                    yield from self._extract_from_file(history_file)

    def _find_from_data_harian(self):
        """Find results from data_harian/ (fallback source).
        
        Yields:
            Tuple of (section, datetime, period, result) for all valid entries
        """
        if not self.data_harian_dir.exists():
            return
        
        # Find all markdown files
        for md_file in self.data_harian_dir.glob("*.md"):
            yield from self._extract_from_file(md_file)

    def _extract_from_file(self, file_path: Path):
        """Extract results from a markdown file.
        
        Applies data sanitization and validation.
        
        Yields:
            Tuple of (section, datetime, period, result) for valid entries
        """
        current_section: Optional[str] = None
        
        try:
            with file_path.open(encoding="utf-8") as f:
                for raw in f:
                    line = raw.strip()
                    
                    # Detect a new "History Nomor" block (with or without # prefix)
                    m = re.match(r"#?\s*History Nomor\s+(.+)", line, re.IGNORECASE)
                    if m:
                        current_section = m.group(1).strip().upper()
                        continue
                        
                    if not line or line.startswith("#") or line.startswith("--"):
                        continue
                        
                    parts = line.split()
                    if len(parts) < 5:
                        continue
                        
                    date, time, _day = parts[0], parts[1], parts[2]
                    period, result = parts[3], parts[4]
                    
                    # Validate data completeness:
                    # - section must exist
                    # - period must exist and be numeric
                    # - result must exist and be numeric
                    if not current_section:
                        continue
                    if not period or not period.strip():
                        continue
                    if not result or not result.strip():
                        continue
                    # Ensure period and result are numeric strings
                    if not period.isdigit():
                        continue
                    if not result.isdigit():
                        continue
                    
                    dt = self._parse_datetime(date, time)
                    
                    if current_section:
                        yield current_section, dt, period, result
        
        except Exception as e:
            # Log error but continue processing other files
            print(f"Error processing {file_path}: {e}")

    def _parse_datetime(self, date_str: str, time_str: str) -> datetime:
        """Parse date and time into timezone-aware datetime.
        
        Returns:
            Datetime object in WIB timezone, or datetime.min if parsing fails
        """
        try:
            dt = datetime.strptime(f"{date_str} {time_str}", "%d-%m-%Y %H:%M:%S")
            return dt.replace(tzinfo=LUNA_TIMEZONE)
        except ValueError:
            return datetime.min.replace(tzinfo=LUNA_TIMEZONE)


if __name__ == "__main__":
    # Simple demonstration
    finder = ResultFinder()
    
    print("Luna Result Finder")
    print(f"Timezone: UTC+7 (Asia/Jakarta)")
    print(f"Source Priority: pasaran_luna/ → data_harian/")
    
    print("\nAll sections found:")
    sections = finder.get_all_sections()
    for section in sections:
        print(f"  - {section}")
    
    print(f"\nAvailable results:")
    available_results = finder.get_available_results()
    for section, data in available_results.items():
        print(f"  {section}: Period {data['period']}, Result {data['result']}")
