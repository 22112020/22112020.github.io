#!/usr/bin/env python3
"""DataLoader - Load and prepare market data for analysis engines.

This module provides read-only access to market data with lazy loading support.
It serves as the data preparation layer between raw data sources and prediction engines.

Key Features:
- Read-only access to data_harian and pasaran_luna
- Lazy loading of historical data
- Source priority: pasaran_luna (primary), data_harian (fallback)
- Data validation and formatting
- UTC+7 timezone compliance

The DataLoader never modifies any data sources.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta
from core.result_finder import ResultFinder


def _resolve_project_root(project_root: Optional[str] = None) -> Path:
    """Resolve project root from explicit input or current workspace."""
    if project_root:
        return Path(project_root).expanduser().resolve()

    current = Path.cwd().resolve()
    if (current / "core").exists() and (current / "data_harian").exists():
        return current

    for candidate in [Path(__file__).resolve().parents[1], Path(".").resolve()]:
        if (candidate / "core").exists() and (candidate / "data_harian").exists():
            return candidate

    return current

# Luna fixed timezone: Asia/Jakarta (UTC+7)
LUNA_TIMEZONE = timezone(timedelta(hours=7))


class DataLoader:
    """Load and prepare market data for analysis engines."""

    def __init__(self, project_root: Optional[str] = None):
        """Initialize DataLoader with project root directory.
        
        Args:
            project_root: Path to Togelku project root directory
        """
        self.project_root = _resolve_project_root(project_root)
        self.result_finder = ResultFinder(project_root=str(self.project_root))

    def load_market(self, market_name: str) -> Dict[str, Any]:
        """Load data for a specific market.
        
        Args:
            market_name: Name of market to load (e.g., 'OREGON03')
            
        Returns:
            Dictionary containing market data structure
            
        Raises:
            ValueError: If market data cannot be loaded
        """
        # Normalize market name for directory lookup
        normalized_name = market_name.replace(" ", "").upper()
        
        # Get latest result using ResultFinder
        latest_result = self.result_finder.get_latest_result(normalized_name)
        
        # If normalized name fails, try original name (with spaces)
        if not latest_result:
            latest_result = self.result_finder.get_latest_result(market_name.upper())
        
        if not latest_result:
            raise ValueError(f"No data available for market: {market_name}")
        
        # Load history with lazy loading (default limit: 100 records)
        history = self._lazy_load_history(normalized_name, limit=100)
        
        # Get statistics
        stats = self._calculate_stats(history)
        
        return {
            "name": market_name,
            "source": latest_result.get("source", "unknown"),
            "latest": latest_result,
            "history": history,
            "stats": stats,
            "metadata": self._generate_metadata()
        }

    def load_all_markets(self) -> Dict[str, Any]:
        """Load data for all available markets.
        
        Returns:
            Dictionary containing all markets with metadata
        """
        # Get all available sections from ResultFinder
        all_sections = self.result_finder.get_all_sections()
        
        markets_data = {}
        
        for section in all_sections:
            try:
                market_data = self.load_market(section)
                markets_data[section] = market_data
            except ValueError:
                # Skip markets with no data
                continue
        
        return {
            "markets": markets_data,
            "count": len(markets_data),
            "generated_at": self._generate_metadata()["generated_at"]
        }

    def _lazy_load_history(self, market_name: str, limit: int = 100) -> List[Dict[str, str]]:
        """Load historical data on-demand with limit.
        
        Args:
            market_name: Name of market
            limit: Maximum number of records to load
            
        Returns:
            List of historical records (newest first)
        """
        history = []
        
        try:
            normalized_dir = market_name.replace(" ", "").lower()
            history_file = self.project_root / "pasaran_luna" / normalized_dir / "history.md"
            
            if history_file.exists():
                content = history_file.read_text(encoding="utf-8")
                lines = content.splitlines()
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith("#") or line.startswith("--"):
                        continue
                    parts = line.split()
                    if len(parts) >= 5 and parts[3].isdigit() and parts[4].isdigit():
                        record = {
                            "date": parts[0],
                            "time": parts[1],
                            "day": parts[2],
                            "period": parts[3],
                            "result": parts[4]
                        }
                        history.append(record)
                history = history[:limit]
        except Exception:
            pass
        
        return history

    def _parse_history_lines(self, history_lines: List[str]) -> List[Dict[str, str]]:
        """Parse history lines into structured format.
        
        Args:
            history_lines: List of history line strings
            
        Returns:
            List of parsed history records
        """
        parsed_history = []
        
        for line in history_lines:
            try:
                # Parse line format: DATE TIME DAY PERIOD RESULT
                parts = line.strip().split()
                if len(parts) >= 5:
                    record = {
                        "date": parts[0],
                        "time": parts[1],
                        "day": parts[2],
                        "period": parts[3],
                        "result": parts[4]
                    }
                    parsed_history.append(record)
            except (IndexError, ValueError):
                # Skip invalid lines
                continue
        
        return parsed_history

    def _calculate_stats(self, history: List[Dict[str, str]]) -> Dict[str, Any]:
        """Calculate statistics for history data.
        
        Args:
            history: List of history records
            
        Returns:
            Dictionary of calculated statistics
        """
        if not history:
            return {
                "total_records": 0,
                "first_record": None,
                "last_record": None
            }
        
        return {
            "total_records": len(history),
            "first_record": history[-1]["date"],  # Oldest record
            "last_record": history[0]["date"]    # Newest record
        }

    def _generate_metadata(self) -> Dict[str, str]:
        """Generate UTC+7 timestamp metadata.
        
        Returns:
            Dictionary containing metadata
        """
        now = datetime.now(LUNA_TIMEZONE)
        return {
            "generated_at": now.strftime("%d-%m-%Y %H:%M:%S"),
            "timezone": "Asia/Jakarta",
            "version": "1.0"
        }


if __name__ == "__main__":
    # Simple demonstration
    loader = DataLoader()
    
    print("Luna Data Loader")
    print(f"Timezone: UTC+7 (Asia/Jakarta)")
    print(f"Project Root: {loader.project_root}")
    
    # Load all markets
    all_data = loader.load_all_markets()
    print(f"\nLoaded {all_data['count']} markets")
    
    for market_name, market_data in all_data['markets'].items():
        print(f"  - {market_name}: {market_data['stats']['total_records']} records")
