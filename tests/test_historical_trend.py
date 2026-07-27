import unittest
from engines.historical_trend.historical_trend_engine import HistoricalTrendEngine
from engines.base_engine import PredictionResult


class TestHistoricalTrendEngine(unittest.TestCase):
    def setUp(self):
        self.engine = HistoricalTrendEngine()

    def _make_history(self, results: list) -> list:
        return [
            {"date": f"{i+1:02d}-07-2026", "time": "12:00:00", "day": "Monday", "period": str(100+i), "result": r}
            for i, r in enumerate(results)
        ]

    def test_engine_name(self):
        self.assertEqual(self.engine.engine_name, "historical_trend")

    def test_predict_with_history(self):
        input_data = {
            "market": "OREGON03",
            "data": {
                "latest": {"date": "25-07-2026", "time": "11:00:00", "day": "Saturday", "period": "2000", "result": "1234"},
                "history": self._make_history(["1234", "5678", "9012", "3456", "7890",
                                                "1357", "2468", "9876", "5432", "1010"]),
                "stats": {"total_records": 10, "first_record": "01-07-2026", "last_record": "25-07-2026"}
            },
            "rules": {},
            "metadata": {}
        }

        result = self.engine.predict(input_data)

        self.assertIsInstance(result, PredictionResult)
        self.assertEqual(result.engine, "historical_trend")
        self.assertEqual(result.market, "OREGON03")
        self.assertEqual(result.target_period, "2001")

        self.assertIn("main", result.prediction)
        self.assertIn("backup", result.prediction)
        self.assertIn("confidence", result.prediction)
        self.assertIn("method", result.prediction)

        self.assertEqual(len(result.prediction["main"]), 5)
        self.assertTrue(all(d.isdigit() for d in result.prediction["main"]))

        self.assertEqual(len(result.prediction["backup"]), 1)
        self.assertTrue(result.prediction["backup"][0].isdigit())

        self.assertGreaterEqual(result.prediction["confidence"], 0.0)
        self.assertLessEqual(result.prediction["confidence"], 1.0)
        self.assertEqual(result.prediction["method"], "historical_trend_analysis")

    def test_predict_empty_history(self):
        input_data = {
            "market": "UNKNOWN",
            "data": {
                "latest": {"date": "25-07-2026", "time": "11:00:00", "day": "Saturday", "period": "1", "result": "0000"},
                "history": [],
                "stats": {"total_records": 0, "first_record": None, "last_record": None}
            },
            "rules": {},
            "metadata": {}
        }

        result = self.engine.predict(input_data)
        self.assertEqual(len(result.prediction["main"]), 5)
        self.assertEqual(result.prediction["confidence"], 0.1)
        self.assertEqual(result.prediction["method"], "insufficient_data")

    def test_predict_invalid_input(self):
        with self.assertRaises(ValueError):
            self.engine.predict({"market": "X", "data": {"latest": {}}, "rules": {}, "metadata": {}})

    def test_positional_frequency(self):
        history = self._make_history(["1234", "5678", "9012"])
        pos_freq = self.engine._calc_positional_frequency(history)
        self.assertIn("0", pos_freq)
        self.assertIn("1", pos_freq)
        self.assertIn("2", pos_freq)
        self.assertIn("3", pos_freq)
        self.assertEqual(sum(pos_freq["0"].values()), 3)
        self.assertEqual(sum(pos_freq["1"].values()), 3)

    def test_trend_calculation(self):
        overall = {"0": 5, "1": 10, "2": 5}
        recent = {"0": 3, "1": 2, "2": 5}
        trend = self.engine._calc_trend(overall, recent)
        self.assertIn("0", trend)
        self.assertIn("1", trend)
        self.assertIn("2", trend)

    def test_cleanup(self):
        self.engine.cleanup()

    def test_rankings_stable(self):
        """Same input should produce same output (deterministic)."""
        input_data = {
            "market": "OREGON06",
            "data": {
                "latest": {"date": "25-07-2026", "time": "11:00:00", "day": "Saturday", "period": "150", "result": "1122"},
                "history": self._make_history(["1122", "3344", "5566", "7788", "9900"]),
                "stats": {"total_records": 5, "first_record": "01-07-2026", "last_record": "25-07-2026"}
            },
            "rules": {},
            "metadata": {}
        }

        r1 = self.engine.predict(input_data)
        r2 = self.engine.predict(input_data)

        self.assertEqual(r1.prediction["main"], r2.prediction["main"])
        self.assertEqual(r1.prediction["backup"], r2.prediction["backup"])


if __name__ == "__main__":
    unittest.main()
