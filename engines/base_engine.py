#!/usr/bin/env python3
"""BaseEngine - Abstract base class for prediction engines.

This module defines the abstract base class that all prediction engines must implement.
It enforces the contract between the executor and engines, ensuring consistent behavior
and output format across all engine implementations.

Key Features:
- Abstract base class with required methods
- PredictionResult contract enforcement
- No market-specific logic
- No file access
- No direct RuleLoader access
- Type hints for all methods
- UTC+7 timezone compliance
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta

# Luna fixed timezone: Asia/Jakarta (UTC+7)
LUNA_TIMEZONE = timezone(timedelta(hours=7))


class PredictionResult:
    """Standardized prediction result contract."""

    def __init__(self, engine: str, market: str, target_period: str):
        """Initialize prediction result.
        
        Args:
            engine: Engine identifier
            market: Target market name
            target_period: Target period for prediction
        """
        self.engine = engine
        self.market = market
        self.target_period = target_period
        self.prediction: Dict[str, Any] = {}
        self.analysis: Dict[str, Any] = {}
        self.metadata: Dict[str, str] = self._generate_metadata()

    def _generate_metadata(self) -> Dict[str, str]:
        """Generate UTC+7 timestamp metadata."""
        now = datetime.now(LUNA_TIMEZONE)
        return {
            "generated_at": now.strftime("%d-%m-%Y %H:%M:%S"),
            "timezone": "Asia/Jakarta",
            "version": "1.0"
        }

    def set_prediction(self, main_digits: List[str], backup_digits: List[str], 
                      confidence: float, method: str) -> None:
        """Set prediction data.
        
        Args:
            main_digits: List of 5 main digits
            backup_digits: List of 1 backup digit
            confidence: Confidence score (0.0-1.0)
            method: Algorithm method used
        """
        self.prediction = {
            "main": main_digits,
            "backup": backup_digits,
            "confidence": confidence,
            "method": method
        }

    def set_analysis(self, analysis_data: Dict[str, Any]) -> None:
        """Set analysis data.
        
        Args:
            analysis_data: Dictionary containing analysis results
        """
        self.analysis = analysis_data

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format.
        
        Returns:
            Dictionary representation of prediction result
        """
        return {
            "engine": self.engine,
            "market": self.market,
            "target_period": self.target_period,
            "prediction": self.prediction,
            "analysis": self.analysis,
            "metadata": self.metadata
        }


class BaseEngine(ABC):
    """Abstract base class for prediction engines."""

    def __init__(self):
        """Initialize base engine."""
        self.engine_name = self.__class__.__name__.replace("Engine", "").lower()

    @abstractmethod
    def predict(self, input_data: Dict[str, Any]) -> PredictionResult:
        """Generate prediction from input data.
        
        Args:
            input_data: Dictionary containing market data and rules
                Expected structure:
                {
                    "market": "MARKET_NAME",
                    "data": {
                        "latest": {"date": "", "time": "", "day": "", "period": "", "result": ""},
                        "history": [{"date": "", "time": "", "day": "", "period": "", "result": ""}],
                        "stats": {"total_records": 0, "first_record": "", "last_record": ""}
                    },
                    "rules": {},
                    "metadata": {}
                }
            
        Returns:
            PredictionResult containing prediction and analysis
            
        Raises:
            PredictionError: If prediction cannot be generated
        """
        pass

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data structure.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_keys = ["market", "data", "rules", "metadata"]
        
        for key in required_keys:
            if key not in input_data:
                return False
        
        # Check data structure
        data = input_data.get("data", {})
        if "latest" not in data or "history" not in data or "stats" not in data:
            return False
        
        return True

    def cleanup(self) -> None:
        """Clean up resources.
        
        This method should be called after prediction to release resources.
        """
        pass


class PredictionError(Exception):
    """Base exception for prediction failures."""
    pass


class InvalidInputError(PredictionError):
    """Raised when input data is invalid."""
    pass


class AlgorithmError(PredictionError):
    """Raised when prediction algorithm fails."""
    pass


if __name__ == "__main__":
    print("BaseEngine - Abstract base class for prediction engines")
    print("Implement predict() method in concrete engine classes")
