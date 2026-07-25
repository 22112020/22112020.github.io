#!/usr/bin/env python3
"""Daily Generator - Automatically creates blank daily data templates.

This module is responsible for generating blank daily data files when the
Luna date changes. It creates templates for users to manually paste market data.

Filename format: DD-MM-YYYY-Luna.md
Location: data_harian/
Timezone: Asia/Jakarta (UTC+7)
"""

import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional

# Luna fixed timezone: Asia/Jakarta (UTC+7)
LUNA_TIMEZONE = timezone(timedelta(hours=7))


class DailyGenerator:
    """Generate blank daily data templates for user input."""
    
    def __init__(self, data_dir: str = "data_harian"):
        """Initialize Daily Generator.
        
        Args:
            data_dir: Directory for daily files (relative to project root)
        """
        self.data_dir = Path(data_dir)
        
    def get_today_date(self) -> str:
        """Get current date in Luna timezone (UTC+7).
        
        Returns:
            Date string in DD-MM-YYYY format
        """
        now = datetime.now(LUNA_TIMEZONE)
        return now.strftime("%d-%m-%Y")
    
    def get_template_filename(self, date_str: Optional[str] = None) -> str:
        """Generate template filename for given date.
        
        Args:
            date_str: Date in DD-MM-YYYY format (uses today if None)
            
        Returns:
            Filename in format DD-MM-YYYY-Luna.md
        """
        if date_str is None:
            date_str = self.get_today_date()
        return f"{date_str}-Luna.md"
    
    def get_template_path(self, date_str: Optional[str] = None) -> Path:
        """Get full path to template file.
        
        Args:
            date_str: Date in DD-MM-YYYY format (uses today if None)
            
        Returns:
            Full Path to template file in data_harian/
        """
        filename = self.get_template_filename(date_str)
        return self.data_dir / filename
    
    def generate_if_missing(self, date_str: Optional[str] = None) -> bool:
        """Generate blank template if it doesn't exist.
        
        Args:
            date_str: Date in DD-MM-YYYY format (uses today if None)
            
        Returns:
            True if file was created, False if it already existed
        """
        template_path = self.get_template_path(date_str)
        
        # Ensure data_harian directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Only create if file doesn't exist
        if not template_path.exists():
            # Create blank file
            template_path.touch()
            return True
        
        return False
    
    def generate_today(self) -> bool:
        """Generate blank template for today's date.
        
        Returns:
            True if file was created, False if it already existed
        """
        return self.generate_if_missing()
    
    def is_template_exists(self, date_str: Optional[str] = None) -> bool:
        """Check if template exists for given date.
        
        Args:
            date_str: Date in DD-MM-YYYY format (uses today if None)
            
        Returns:
            True if template file exists
        """
        template_path = self.get_template_path(date_str)
        return template_path.exists()


if __name__ == "__main__":
    # Simple demonstration
    generator = DailyGenerator()
    
    print("Luna Daily Generator")
    print(f"Timezone: UTC+7 (Asia/Jakarta)")
    print(f"Today's date: {generator.get_today_date()}")
    
    created = generator.generate_today()
    if created:
        print(f"✅ Created blank template for today")
    else:
        print(f"ℹ️  Template for today already exists")
    
    # Show today's template path
    today_path = generator.get_template_path()
    print(f"Template location: {today_path.absolute()}")
