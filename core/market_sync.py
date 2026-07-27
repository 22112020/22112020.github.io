#!/usr/bin/env python3
"""Market Sync - Synchronize data from data_harian to pasaran_luna.

This module implements the Auto Market Sync System that transforms raw user
input in data_harian/ into structured market histories in pasaran_luna/.

Key Features:
- Reads only from data_harian/ (source of truth)
- Creates normalized market folders in pasaran_luna/
- Append-only: never overwrites historical data
- Maintains index.json for fast lookup
- Supports complete rebuild from data_harian/
- Uses UTC+7 timezone for all operations
"""

import re
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple, Optional, Set
import json

# Luna fixed timezone: Asia/Jakarta (UTC+7)
LUNA_TIMEZONE = timezone(timedelta(hours=7))

# UI artifacts to filter out (data sanitization)
UI_ARTIFACTS = {
    "labelthumbnail",
    "thumbnail", 
    "Play Now",
    "btn_live"
}


class MarketSync:
    """Synchronize market data from data_harian to pasaran_luna."""
    
    def __init__(self, project_root: Optional[str] = None):
        """Initialize Market Sync.
        
        Args:
            project_root: Path to Togelku project root directory
        """
        self.project_root = Path(project_root).expanduser().resolve() if project_root else Path.cwd().resolve()
        self.data_harian_dir = self.project_root / "data_harian"
        self.trash_dir = self.project_root / "trash_dashboard"
        self.pasaran_luna_dir = self.project_root / "pasaran_luna"
        self.index_file = self.pasaran_luna_dir / "index.json"
        self.orphan_slots = self._load_orphan_slots()

    def _load_orphan_slots(self) -> List[Dict]:
        """Load orphan market slot configuration."""
        config_file = self.project_root / "config" / "orphan_markets.json"
        if not config_file.exists():
            return []
        try:
            with config_file.open(encoding="utf-8") as f:
                data = json.load(f)
            return data.get("slots", [])
        except Exception:
            return []

    def sync_all(self) -> Dict[str, int]:
        """Process all daily files and sync to pasaran_luna.
        
        Returns:
            Dictionary with sync statistics (markets_updated, records_added, etc.)
        """
        stats = {
            'files_processed': 0,
            'markets_updated': 0,
            'records_added': 0,
            'records_skipped': 0
        }
        
        # Ensure pasaran_luna directory exists
        self.pasaran_luna_dir.mkdir(parents=True, exist_ok=True)
        
        # Collect files from data_harian
        sources = []
        if self.data_harian_dir.exists():
            sources.append(('data_harian', self.data_harian_dir))
        
        # Collect files from trash_dashboard
        if self.trash_dir.exists():
            sources.append(('trash_dashboard', self.trash_dir))
        
        for source_name, source_dir in sources:
            daily_files = sorted(
                [f for f in source_dir.glob("*.md") if self._extract_date_from_filename(f.name)],
                key=lambda f: self._extract_date_from_filename(f.name)
            )
            
            for daily_file in daily_files:
                stats['files_processed'] += 1
                file_stats = self._process_daily_file(daily_file)
                stats['markets_updated'] += file_stats['markets_updated']
                stats['records_added'] += file_stats['records_added']
                stats['records_skipped'] += file_stats['records_skipped']
        
        # Update index.json
        self._update_index()
        
        return stats

    def _process_daily_file(self, file_path: Path) -> Dict[str, int]:
        """Process a single daily file.
        
        Args:
            file_path: Path to daily markdown file
            
        Returns:
            Dictionary with processing statistics
        """
        stats = {
            'markets_updated': 0,
            'records_added': 0,
            'records_skipped': 0
        }
        
        try:
            content = file_path.read_text(encoding="utf-8")
            sanitized_content = self._sanitize_content(content)
            
            # Extract named market entries (from sanitized content)
            market_entries = self._extract_market_entries(sanitized_content, file_path.name)
            
            # Extract orphan market entries (from raw content, needs UI markers for positioning)
            orphan_entries = self._extract_orphan_entries(content, file_path.name)
            
            # Process both sets of entries
            all_entries = market_entries + orphan_entries
            
            # Process each market entry
            for entry in all_entries:
                market_name, result, period, file_date = entry
                
                # Normalize market name
                normalized_name = self._normalize_market_name(market_name)
                
                # Create market directory if missing
                market_dir = self.pasaran_luna_dir / normalized_name
                market_dir.mkdir(exist_ok=True)
                
                # Append to history file
                history_file = market_dir / "history.md"
                
                # Check if this record already exists
                if self._record_exists(history_file, normalized_name, file_date, period):
                    stats['records_skipped'] += 1
                    continue
                
                # Append new record
                self._append_to_history(history_file, normalized_name, file_date, period, result)
                stats['records_added'] += 1
                
                if stats['records_added'] > 0:
                    stats['markets_updated'] += 1
        
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
        
        return stats

    def _sanitize_content(self, content: str) -> str:
        """Remove UI artifacts from content.
        
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

    def _extract_market_entries(self, content: str, filename: str) -> List[Tuple[str, str, str, str]]:
        """Extract market entries from daily file content.
        
        Args:
            content: Sanitized content to parse
            
        Returns:
            List of tuples: (market_name, result, period, file_date)
        """
        entries = []
        
        # Extract date from filename (used as default date for all entries)
        file_date = self._extract_date_from_filename(filename)
        
        # Pattern: [MARKET NAME] POOL
        #          <result>
        #          [PERIODE : <period>]
        lines = content.splitlines()
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Skip empty lines and headers
            if not line or line.startswith("#") or line.startswith("[") or line.startswith("Play"):
                continue
            
            # Look for POOL pattern
            if "POOL" in line.upper():
                # Extract market name (before POOL)
                market_name = line.split("POOL")[0].strip().upper()
                
                # Look for result in next lines
                result_line = ""
                period = ""
                
                # Check next few lines for result
                for j in range(i+1, min(i+5, len(lines))):
                    next_line = lines[j].strip()
                    if next_line and next_line.isdigit() and len(next_line) == 4:
                        result_line = next_line
                        break
                
                # Look for period in [PERIODE : XXX] format
                for j in range(i+1, min(i+5, len(lines))):
                    next_line = lines[j].strip()
                    if "PERIODE" in next_line.upper():
                        period_match = re.search(r'PERIODE\s*:\s*(\d+)', next_line, re.IGNORECASE)
                        if period_match:
                            period = period_match.group(1)
                            break
                
                # Only add if we have both result and period
                if market_name and result_line and period:
                    entries.append((market_name, result_line, period, file_date))
        
        return entries

    def _extract_orphan_entries(self, content: str, filename: str) -> List[Tuple[str, str, str, str]]:
        """Extract orphan (banner) market entries using position-based slot mapping.
        
        Orphan entries appear as interstitial results between named POOL markets.
        They are identified by their position relative to the preceding POOL market,
        not by market name. The position-to-market mapping is in config/orphan_markets.json.
        
        Args:
            content: Raw file content (with UI markers for position detection)
            filename: Filename for date extraction
            
        Returns:
            List of tuples: (market_name, result, period="0000", file_date)
        """
        entries = []
        file_date = self._extract_date_from_filename(filename)
        if not file_date or not self.orphan_slots:
            return entries
        
        lines = content.splitlines()
        stripped = [l.strip() for l in lines]
        
        # Build map: after_market -> list of consecutive orphan results
        orphan_results = {}
        
        i = 0
        while i < len(stripped):
            line = stripped[i]
            
            # Detect named POOL market (but not UI artifact lines)
            if "POOL" in line.upper() and line not in ("labelthumbnail", "thumbnail", "btn_live"):
                market_header = line.upper()
                
                # Skip past: market's own result, [PERIODE], Play Now
                j = i + 1
                skipped = 0
                while j < len(stripped) and skipped < 3:
                    l = stripped[j]
                    if l.isdigit() and len(l) in (4, 5):
                        skipped += 1
                    elif l.upper().startswith("[PERIODE"):
                        skipped += 1
                    elif l == "Play Now":
                        skipped += 1
                    j += 1
                
                # Collect consecutive orphan results after this market
                orphans = []
                k = j
                while k < len(stripped):
                    l = stripped[k]
                    
                    # Stop at next POOL market
                    if "POOL" in l.upper() and l not in ("labelthumbnail", "thumbnail", "btn_live"):
                        break
                    
                    # Pattern: blank -> DIGIT -> blank (labelthumbnail type)
                    if (k + 2 < len(stripped) 
                        and stripped[k] == "" 
                        and stripped[k+1].isdigit() and len(stripped[k+1]) in (4, 5)
                        and stripped[k+2] == ""):
                        orphans.append(stripped[k+1])
                        k += 3
                        continue
                    
                    # Pattern: DIGIT -> TIME -> btn_live (thumbnail type)
                    if (k + 2 < len(stripped)
                          and stripped[k].isdigit() and len(stripped[k]) in (4, 5)
                          and ":" in stripped[k+1]
                          and stripped[k+2] == "btn_live"):
                        orphans.append(stripped[k])
                        k += 3
                        continue
                    
                    k += 1
                
                if orphans:
                    orphan_results[market_header] = orphans
            
            i += 1
        
        # Map orphan results to market names using slot config
        for slot in self.orphan_slots:
            after = slot["after_market"].upper()
            idx = slot["orphan_index"]
            market = slot["market"]
            
            if after in orphan_results and idx < len(orphan_results[after]):
                result = orphan_results[after][idx]
                entries.append((market, result, "0000", file_date))
        
        return entries

    def _normalize_market_name(self, market_name: str) -> str:
        """Normalize market name to consistent format.
        
        Args:
            market_name: Raw market name
            
        Returns:
            Normalized market name (lowercase, no spaces)
        """
        # Remove spaces and convert to lowercase
        normalized = market_name.replace(" ", "").lower()
        return normalized

    def _record_exists(self, history_file: Path, market_name: str, date: str, period: str) -> bool:
        """Check if a record already exists in history.
        
        Args:
            history_file: Path to history.md file
            market_name: Market name
            date: Date string (DD-MM-YYYY)
            period: Period number
            
        Returns:
            True if record exists, False otherwise
        """
        if not history_file.exists():
            return False
        
        try:
            content = history_file.read_text(encoding="utf-8")
            # Look for exact match of date + period
            search_pattern = f"{date}.*{period}"
            if re.search(search_pattern, content):
                return True
            return False
        except Exception:
            return False

    def _append_to_history(self, history_file: Path, market_name: str, date: str, period: str, result: str):
        """Append a new record to market history.
        
        Args:
            history_file: Path to history.md file
            market_name: Market name
            date: Date string (DD-MM-YYYY)
            period: Period number
            result: Result value
        """
        # Get current time in UTC+7
        now = datetime.now(LUNA_TIMEZONE)
        time_str = now.strftime("%H:%M:%S")
        day_str = now.strftime("%A")
        
        # Format: DATE TIME DAY PERIOD RESULT
        record_line = f"{date} {time_str} {day_str} {period} {result}\n"
        
        # Create header if file doesn't exist
        if not history_file.exists():
            header = f"History Nomor {market_name.upper()}\n\n"
            history_file.write_text(header, encoding="utf-8")
        
        # Append record
        with history_file.open("a", encoding="utf-8") as f:
            f.write(record_line)

    def _extract_date_from_filename(self, filename: str) -> Optional[str]:
        """Extract date from filename (DD-MM-YYYY format).
        
        Args:
            filename: Filename string
            
        Returns:
            Date string in DD-MM-YYYY format, or None if not found
        """
        # Look for DD-MM-YYYY pattern
        date_match = re.search(r'(\d{2}-\d{2}-\d{4})', filename)
        if date_match:
            return date_match.group(1)
        return None

    def _update_index(self):
        """Update the index.json file with current market data."""
        index_data = {
            "markets": {},
            "last_sync": datetime.now(LUNA_TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Scan all market directories
        if self.pasaran_luna_dir.exists():
            for market_dir in self.pasaran_luna_dir.iterdir():
                if market_dir.is_dir():
                    market_name = market_dir.name.upper()
                    history_file = market_dir / "history.md"
                    
                    if history_file.exists():
                        # Get latest record
                        latest_period, latest_result = self._get_latest_record(history_file)
                        
                        index_data["markets"][market_name] = {
                            "name": market_name,
                            "latest_period": latest_period,
                            "latest_result": latest_result,
                            "last_updated": datetime.now(LUNA_TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
                        }
        
        # Write index.json
        with self.index_file.open("w", encoding="utf-8") as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)

    def _get_latest_record(self, history_file: Path) -> Tuple[str, str]:
        """Get the latest period and result from a history file.
        
        Args:
            history_file: Path to history.md file
            
        Returns:
            Tuple of (latest_period, latest_result)
        """
        try:
            content = history_file.read_text(encoding="utf-8")
            lines = content.splitlines()
            
            # Find last data line (skip header and empty lines)
            for line in reversed(lines):
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split()
                    if len(parts) >= 5:
                        period = parts[3]
                        result = parts[4]
                        return period, result
            
            return "", ""
        except Exception:
            return "", ""

    def rebuild_all(self) -> Dict[str, int]:
        """Complete rebuild from data_harian.
        
        Deletes existing pasaran_luna and reconstructs from scratch.
        
        Returns:
            Dictionary with rebuild statistics
        """
        # Delete existing pasaran_luna
        if self.pasaran_luna_dir.exists():
            # Remove all contents
            for item in self.pasaran_luna_dir.iterdir():
                if item.is_dir():
                    # Remove directory tree
                    for sub_item in item.iterdir():
                        if sub_item.is_file():
                            sub_item.unlink()
                        elif sub_item.is_dir():
                            # Shouldn't have nested dirs, but handle just in case
                            for sub_sub_item in sub_item.iterdir():
                                sub_sub_item.unlink()
                            sub_item.rmdir()
                    item.rmdir()
                elif item.is_file():
                    item.unlink()
        
        # Rebuild from data_harian
        return self.sync_all()


if __name__ == "__main__":
    # Simple demonstration
    sync = MarketSync()
    
    print("Luna Market Sync")
    print(f"Timezone: UTC+7 (Asia/Jakarta)")
    print(f"Source: {sync.data_harian_dir}")
    print(f"Target: {sync.pasaran_luna_dir}")
    
    stats = sync.sync_all()
    print(f"\nSync completed:")
    print(f"  Files processed: {stats['files_processed']}")
    print(f"  Markets updated: {stats['markets_updated']}")
    print(f"  Records added: {stats['records_added']}")
    print(f"  Records skipped: {stats['records_skipped']}")
