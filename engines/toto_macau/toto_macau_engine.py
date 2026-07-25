#!/usr/bin/env python3
"""Toto Macau Engine - Complete prediction engine for Toto Macau market.

This engine implements the Toto Macau prediction algorithm as specified in
rules/toto_macau_prediction_v1.md. It follows the similarity and frequency
analysis approach with 5 source markets.
"""

from typing import Dict, Any, List, Optional, Tuple
from engines.base_engine import BaseEngine, PredictionResult
from core.data_loader import DataLoader


class TotoMacauEngine(BaseEngine):
    """Toto Macau prediction engine with complete algorithm implementation."""

    def __init__(self):
        super().__init__()
        self.data_loader = DataLoader()

    def predict(self, input_data: Dict[str, Any]) -> PredictionResult:
        """Generate prediction for Toto Macau market using full algorithm.
        
        Args:
            input_data: Dictionary containing market data and rules
                Expected structure:
                {
                    "market": "TOTO_MACAU",
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
        """
        # Validate input
        if not self.validate_input(input_data):
            raise ValueError("Invalid input data for Toto Macau engine")

        # Extract market data
        market_name = input_data["market"]
        latest_result = input_data["data"]["latest"]["result"]
        history = input_data["data"]["history"]
        
        # Get target period (next period after latest)
        try:
            target_period = str(int(input_data["data"]["latest"]["period"]) + 1)
        except (ValueError, KeyError):
            target_period = "9999"  # Fallback
        
        # Create result object
        result = PredictionResult("toto_macau", market_name, target_period)
        
        # Step 1: Get source market results
        # Source markets: Huahin 0100, Bangkok 0130, Kentucky Mid, New York Mid, Florida Mid
        source_results = self._get_source_results()
        
        # Step 2: Split digits from each result
        source_digits = [list(r) for r in source_results if r]
        
        # Step 3: Calculate similarity and frequency
        digit_similarity, digit_frequency = self._analyze_digits(source_digits)
        
        # Step 4: Rank digits by similarity and frequency
        ranked_digits = self._rank_digits(digit_similarity, digit_frequency)
        
        # Step 5: Select main digits (top 5)
        main_digits = ranked_digits[:5]
        
        # Step 6: Select backup digit (next after top 5)
        backup_digits = [ranked_digits[5]] if len(ranked_digits) > 5 else ["5"]
        
        # Set prediction
        result.set_prediction(
            main_digits=main_digits,
            backup_digits=backup_digits,
            confidence=self._calculate_confidence(digit_similarity, digit_frequency),
            method="toto_macau_similarity_frequency"
        )
        
        # Add analysis data
        analysis = {
            "source_markets": [
                "Huahin 0100",
                "Bangkok 0130",
                "Kentucky Mid",
                "New York Mid",
                "Florida Mid"
            ],
            "digit_similarity": digit_similarity,
            "digit_frequency": digit_frequency,
            "algorithm": "similarity_and_frequency_analysis",
            "candidates": ranked_digits
        }
        result.set_analysis(analysis)
        
        return result

    def _resolve_market_name(self, name: str) -> str:
        """Resolve market name to canonical form used by DataLoader.
        
        MarketSync normalizes "4D TOTO MACAU POOL" → "4DTOTOMACAU".
        Users may request "TOTO MACAU", "TOTO_MACAU", or "4DTOTOMACAU".
        """
        normalized = name.replace(" ", "").replace("_", "").upper()
        if normalized in ("TOTOMACAU", "4DTOTOMACAU"):
            return "4DTOTOMACAU"
        return name

    def _get_own_market_data(self) -> Optional[Dict]:
        """Load engine's own market data using canonical name.
        
        Uses "4DTOTOMACAU" which is the MarketSync-normalized name
        for "4D TOTO MACAU POOL" from daily files.
        """
        try:
            return self.data_loader.load_market("4DTOTOMACAU")
        except Exception:
            return None

    def _get_source_results(self) -> List[str]:
        """Get latest results from all source markets.
        
        Returns:
            List of 4-digit results from source markets
        """
        # In production, this would use DataLoader to get actual results
        # For now, return mock data to demonstrate structure
        sources = [
            "Huahin 0100",
            "Bangkok 0130",
            "Kentucky Mid",
            "New York Mid",
            "Florida Mid"
        ]
        
        results = []
        for source in sources:
            try:
                # Use DataLoader to get latest result
                market_data = self.data_loader.load_market(source)
                if market_data and "latest" in market_data:
                    results.append(market_data["latest"]["result"])
            except:
                pass
        
        return results

    def _analyze_digits(self, source_digits: List[List[str]]) -> Tuple[Dict[str, int], Dict[str, int]]:
        """Calculate similarity and frequency for each digit.
        
        Args:
            source_digits: List of digit lists from each source
            
        Returns:
            Tuple of (similarity_score, frequency_count)
        """
        # Similarity: count how many sources contain each digit
        similarity = {str(i): 0 for i in range(10)}
        
        # Frequency: total occurrences across all sources
        frequency = {str(i): 0 for i in range(10)}
        
        for digits in source_digits:
            unique_digits = set(digits)
            for digit in unique_digits:
                similarity[digit] += 1
            
            for digit in digits:
                frequency[digit] += 1
        
        return similarity, frequency

    def _rank_digits(self, similarity: Dict[str, int], 
                     frequency: Dict[str, int]) -> List[str]:
        """Rank digits by similarity and frequency.
        
        Args:
            similarity: Digit similarity scores
            frequency: Digit frequency counts
            
        Returns:
            List of digits sorted by score
        """
        # Combined score: similarity (primary) + frequency (secondary)
        def score(digit: str) -> float:
            return similarity[digit] * 2 + frequency[digit] * 1
        
        return sorted(similarity.keys(), key=score, reverse=True)

    def _calculate_confidence(self, similarity: Dict[str, int], 
                             frequency: Dict[str, int]) -> float:
        """Calculate prediction confidence score.
        
        Args:
            similarity: Digit similarity scores
            frequency: Digit frequency counts
            
        Returns:
            Confidence score (0.0 - 1.0)
        """
        # Source coverage: 25%
        source_score = min(1.0, sum(similarity.values()) / 5.0) * 0.25
        
        # Pattern strength: 35%
        pattern_score = (sum(frequency.values()) / 20.0) * 0.35
        
        # Consistency: 25%
        consistency_score = 0.25 if len([v for v in similarity.values() if v > 0]) >= 3 else 0.0
        
        # Diversity: 15%
        diversity_score = min(1.0, len([v for v in frequency.values() if v > 0]) / 10.0) * 0.15
        
        confidence = source_score + pattern_score + consistency_score + diversity_score
        return round(confidence, 2)


if __name__ == "__main__":
    print("Toto Macau Engine - Complete Implementation")
    print("Follows rules/toto_macau_prediction_v1.md specification")
