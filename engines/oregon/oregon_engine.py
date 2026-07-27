#!/usr/bin/env python3
"""Oregon Engine - Complete prediction engine for Oregon markets.

This engine implements the Oregon prediction algorithm as specified in rules/oregon_rules.md.
It follows the frequency analysis with history elimination approach.
"""

from typing import Dict, Any, List, Optional
from engines.base_engine import BaseEngine, PredictionResult
from core.data_loader import DataLoader


class OregonEngine(BaseEngine):
    """Oregon prediction engine with complete algorithm implementation."""

    def __init__(self):
        super().__init__()
        self.data_loader = DataLoader()

    def predict(self, input_data: Dict[str, Any]) -> PredictionResult:
        """Generate prediction for Oregon market using full algorithm.
        
        Args:
            input_data: Dictionary containing market data and rules
                Expected structure:
                {
                    "market": "OREGON03",
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
            raise ValueError("Invalid input data for Oregon engine")

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
        result = PredictionResult("oregon", market_name, target_period)
        
        # Step 1: Collect source results from other Oregon markets
        # Rule: Source = Semua Oregon - Oregon Target
        source_results = self._get_source_results(market_name)
        
        # Step 2: Split digits and calculate frequency
        digit_frequency = self._calculate_digit_frequency(source_results)
        
        # Step 3: Rank digits by frequency
        ranked_digits = self._rank_digits(digit_frequency)
        
        # Step 4: Select main digits (top 5)
        main_digits = ranked_digits[:5]
        
        # Step 5: Apply history elimination
        eliminated_digits = self._apply_history_elimination(main_digits, history)
        
        # If elimination removed main digits, substitute
        final_main = self._substitute_eliminated_digits(main_digits, eliminated_digits, ranked_digits)
        
        # Step 6: Select backup digit — must be different from all main digits
        backup_digits = self._select_backup_digit(final_main, ranked_digits)
        
        # Set prediction
        result.set_prediction(
            main_digits=final_main,
            backup_digits=backup_digits,
            confidence=self._calculate_confidence(digit_frequency, history),
            method="oregon_frequency_with_elimination"
        )
        
        # Add analysis data
        analysis = {
            "digit_frequency": digit_frequency,
            "source_data": {
                "target": market_name,
                "sources": self._get_source_names(market_name),
                "source_results": source_results,
                "latest_result": latest_result,
                "history_count": len(history)
            },
            "algorithm": "frequency_analysis_with_elimination",
            "elimination": {
                "eliminated": eliminated_digits,
                "depth": 7
            }
        }
        result.set_analysis(analysis)
        
        return result

    def _get_source_results(self, market_name: str) -> List[str]:
        """Get latest results from source Oregon markets.
        
        Rule: Source = Semua Oregon - Oregon Target
        Example: Target OREGON03 → Sources: OREGON06, OREGON09, OREGON12
        
        Args:
            market_name: Target market name (e.g. "OREGON03")
            
        Returns:
            List of 4-digit result strings from source markets
        """
        all_oregon = ["OREGON03", "OREGON06", "OREGON09", "OREGON12"]
        normalized_target = market_name.replace(" ", "").upper()
        
        sources = [m for m in all_oregon if m != normalized_target]
        
        results = []
        for source in sources:
            try:
                market_data = self.data_loader.load_market(source)
                if market_data and "latest" in market_data:
                    results.append(market_data["latest"]["result"])
            except Exception:
                pass
        
        return results

    def _get_source_names(self, market_name: str) -> List[str]:
        """Get source market names for a given target.

        Rule: Source = Semua Oregon - Oregon Target

        Args:
            market_name: Target market name (e.g. "OREGON03")

        Returns:
            List of source market names
        """
        all_oregon = ["OREGON03", "OREGON06", "OREGON09", "OREGON12"]
        normalized_target = market_name.replace(" ", "").upper()
        return [m for m in all_oregon if m != normalized_target]

    def _calculate_digit_frequency(self, source_results: List[str]) -> Dict[str, int]:
        """Calculate frequency of each digit across source results.
        
        Args:
            source_results: List of 4-digit results from source markets
            
        Returns:
            Dictionary of digit → count
        """
        frequency = {str(i): 0 for i in range(10)}
        
        for result in source_results:
            for digit in result:
                frequency[digit] += 1
        
        return frequency

    def _rank_digits(self, frequency: Dict[str, int]) -> List[str]:
        """Rank digits by frequency (descending) and value (ascending for ties).
        
        Args:
            frequency: Dictionary of digit → count
            
        Returns:
            List of digits sorted by frequency and value
        """
        # Sort by frequency (descending), then by digit value (ascending)
        return sorted(frequency.keys(), 
                     key=lambda d: (-frequency[d], int(d)))

    def _apply_history_elimination(self, main_digits: List[str], 
                                   history: List[Dict]) -> List[str]:
        """Eliminate digits that appear in target market history.
        
        Args:
            main_digits: Selected main digits
            history: Target market history records
            
        Returns:
            List of digits to eliminate
        """
        eliminated = []
        
        # Check last 7 days of history
        for record in history[:7]:  # Last 7 records
            result = record.get("result", "")
            for digit in result:
                if digit in main_digits and digit not in eliminated:
                    eliminated.append(digit)
        
        return eliminated

    def _substitute_eliminated_digits(self, main_digits: List[str], 
                                      eliminated: List[str], 
                                      ranked_digits: List[str]) -> List[str]:
        """Substitute eliminated digits with next available.
        
        Args:
            main_digits: Original main digits
            eliminated: Digits to remove
            ranked_digits: All ranked digits
            
        Returns:
            Final main digits with substitutions
        """
        final = [d for d in main_digits if d not in eliminated]
        
        # Substitute from remaining ranked digits
        for digit in eliminated:
            for substitute in ranked_digits:
                if substitute not in final and substitute not in eliminated:
                    final.append(substitute)
                    break
            if len(final) >= 5:
                break
        
        return final[:5]  # Ensure exactly 5 digits

    def _select_backup_digit(self, main_digits: List[str],
                             ranked_digits: List[str]) -> List[str]:
        """Select backup digit that is different from all main digits.
        
        Args:
            main_digits: Final main digits (after elimination)
            ranked_digits: All digits ranked by frequency
            
        Returns:
            List with single backup digit (always different from main)
        """
        for digit in ranked_digits:
            if digit not in main_digits:
                return [digit]
        return ["3"]  # Fallback — should never reach here with 10 digits

    def _calculate_confidence(self, frequency: Dict[str, int], 
                             history: List[Dict]) -> float:
        """Calculate prediction confidence score.
        
        Args:
            frequency: Digit frequency distribution
            history: Target market history
            
        Returns:
            Confidence score (0.0 - 1.0)
        """
        # Data completeness: 30%
        data_score = min(1.0, len(history) / 10.0) * 0.3
        
        # Pattern consistency: 40%
        # Higher frequency difference = more consistent
        freq_values = list(frequency.values())
        if freq_values:
            pattern_score = (max(freq_values) - min(freq_values)) / 10.0 * 0.4
        else:
            pattern_score = 0.0
        
        # Rule compliance: 30%
        # All main digits have frequency > 0
        rule_score = 0.3 if all(v > 0 for v in frequency.values()) else 0.0
        
        confidence = data_score + pattern_score + rule_score
        return round(confidence, 2)


if __name__ == "__main__":
    print("Oregon Engine - Complete Implementation")
    print("Follows rules/oregon_rules.md specification")
