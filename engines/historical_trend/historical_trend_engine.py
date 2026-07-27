from typing import Dict, Any, List, Tuple
from engines.base_engine import BaseEngine, PredictionResult


class HistoricalTrendEngine(BaseEngine):
    def __init__(self):
        super().__init__()
        self.engine_name = "historical_trend"

    def predict(self, input_data: Dict[str, Any]) -> PredictionResult:
        if not self.validate_input(input_data):
            raise ValueError("Invalid input data for HistoricalTrendEngine")

        market_name = input_data["market"]
        history = input_data["data"]["history"]

        try:
            target_period = str(int(input_data["data"]["latest"]["period"]) + 1)
        except (ValueError, KeyError):
            target_period = "9999"

        result = PredictionResult("historical_trend", market_name, target_period)

        if not history:
            result.set_prediction(
                main_digits=["4", "6", "9", "1", "3"],
                backup_digits=["8"],
                confidence=0.1,
                method="insufficient_data"
            )
            result.set_analysis({"error": "No historical data available", "history_count": 0})
            return result

        overall_freq = self._calc_digit_frequency(history)
        positional_freq = self._calc_positional_frequency(history)
        recent_history = history[:min(10, len(history))]
        recent_freq = self._calc_digit_frequency(recent_history)
        trend = self._calc_trend(overall_freq, recent_freq)
        ranked = self._rank_digits(overall_freq, positional_freq, trend, len(history))

        main_digits = ranked[:5]
        backup_digits = [ranked[5]] if len(ranked) > 5 else ["8"]

        result.set_prediction(
            main_digits=main_digits,
            backup_digits=backup_digits,
            confidence=self._calc_confidence(overall_freq, positional_freq, trend, len(history)),
            method="historical_trend_analysis"
        )

        result.set_analysis({
            "digit_frequency": overall_freq,
            "positional_frequency": positional_freq,
            "recent_frequency": recent_freq,
            "trend_scores": trend,
            "ranked_candidates": ranked,
            "history_count": len(history),
        })

        return result

    def _calc_digit_frequency(self, history: List[Dict]) -> Dict[str, int]:
        freq = {str(i): 0 for i in range(10)}
        for record in history:
            for digit in record.get("result", ""):
                if digit in freq:
                    freq[digit] += 1
        return freq

    def _calc_positional_frequency(self, history: List[Dict]) -> Dict[str, Dict[str, int]]:
        pos_freq = {str(p): {str(i): 0 for i in range(10)} for p in range(4)}
        for record in history:
            result = record.get("result", "")
            for pos, digit in enumerate(result):
                if pos < 4 and digit in pos_freq[str(pos)]:
                    pos_freq[str(pos)][digit] += 1
        return pos_freq

    def _calc_trend(self, overall: Dict[str, int], recent: Dict[str, int]) -> Dict[str, float]:
        trend = {}
        for d in range(10):
            d_str = str(d)
            overall_count = overall.get(d_str, 0)
            recent_count = recent.get(d_str, 0)
            overall_avg = overall_count / max(1, sum(overall.values())) * 100 if sum(overall.values()) > 0 else 0
            recent_avg = recent_count / max(1, sum(recent.values())) * 100 if sum(recent.values()) > 0 else 0
            if overall_avg > 0:
                trend[d_str] = round(recent_avg / overall_avg, 2)
            else:
                trend[d_str] = 0.0
        return trend

    def _rank_digits(self, overall_freq: Dict[str, int],
                     positional_freq: Dict[str, Dict[str, int]],
                     trend: Dict[str, float],
                     total_records: int) -> List[str]:
        total_digits = sum(overall_freq.values()) or 1
        scores = {}
        for d in range(10):
            d_str = str(d)
            freq_score = overall_freq.get(d_str, 0) / total_digits
            pos_score = 0
            for p in range(4):
                pos_total = sum(positional_freq.get(str(p), {}).values()) or 1
                pos_score += positional_freq.get(str(p), {}).get(d_str, 0) / pos_total
            pos_score /= 4
            trend_score = min(trend.get(d_str, 0), 3.0) / 3.0
            scores[d_str] = freq_score * 0.3 + pos_score * 0.4 + trend_score * 0.3
        return sorted(scores.keys(), key=lambda d: (-scores[d], int(d)))

    def _calc_confidence(self, overall_freq: Dict[str, int],
                         positional_freq: Dict[str, Dict[str, int]],
                         trend: Dict[str, float],
                         total_records: int) -> float:
        data_score = min(1.0, total_records / 20.0) * 0.3
        freq_values = [v for v in overall_freq.values() if v > 0]
        diversity = len(freq_values) / 10.0
        trend_strength = sum(abs(t) for t in trend.values() if t != 0) / max(1, len([t for t in trend.values() if t != 0]))
        pattern_score = min(1.0, diversity * 0.5 + trend_strength * 0.3) * 0.4
        pos_scores = []
        for p in range(4):
            p_vals = list(positional_freq.get(str(p), {}).values())
            if p_vals:
                pos_scores.append((max(p_vals) - min(p_vals)) / max(1, sum(p_vals)))
        pos_score = (sum(pos_scores) / max(1, len(pos_scores))) * 0.3 if pos_scores else 0.0
        return round(data_score + pattern_score + pos_score, 2)


if __name__ == "__main__":
    print("HistoricalTrendEngine v1.0")
