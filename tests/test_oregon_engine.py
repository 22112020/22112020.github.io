import unittest
from engines.oregon.oregon_engine import OregonEngine
from engines.base_engine import PredictionResult


class TestOregonEngine(unittest.TestCase):
    """Test OregonEngine implementation."""

    def setUp(self):
        self.engine = OregonEngine()

    def test_engine_name(self):
        """Test engine name is correctly set."""
        self.assertEqual(self.engine.engine_name, "oregon")

    def test_predict_valid_input(self):
        """Test prediction with valid input."""
        input_data = {
            "market": "OREGON03",
            "data": {
                "latest": {
                    "date": "24-07-2026",
                    "time": "11:04:38",
                    "day": "Friday",
                    "period": "1990",
                    "result": "8207"
                },
                "history": [
                    {
                        "date": "23-07-2026",
                        "time": "11:04:38",
                        "day": "Thursday",
                        "period": "1989",
                        "result": "5555"
                    }
                ],
                "stats": {
                    "total_records": 2,
                    "first_record": "23-07-2026",
                    "last_record": "24-07-2026"
                }
            },
            "rules": {},
            "metadata": {}
        }
        
        result = self.engine.predict(input_data)
        
        # Verify result structure
        self.assertIsInstance(result, PredictionResult)
        self.assertEqual(result.engine, "oregon")
        self.assertEqual(result.market, "OREGON03")
        self.assertEqual(result.target_period, "1991")
        
        # Verify prediction structure
        self.assertIn("main", result.prediction)
        self.assertIn("backup", result.prediction)
        self.assertIn("confidence", result.prediction)
        self.assertIn("method", result.prediction)
        
        # Verify main digits (5 digits)
        self.assertEqual(len(result.prediction["main"]), 5)
        self.assertTrue(all(d.isdigit() for d in result.prediction["main"]))
        
        # Verify backup digit (1 digit)
        self.assertEqual(len(result.prediction["backup"]), 1)
        self.assertTrue(result.prediction["backup"][0].isdigit())
        
        # Verify confidence is reasonable
        self.assertGreaterEqual(result.prediction["confidence"], 0.0)
        self.assertLessEqual(result.prediction["confidence"], 1.0)
        
        # Verify method
        self.assertEqual(result.prediction["method"], "oregon_frequency_with_elimination")

    def test_predict_invalid_input(self):
        """Test prediction with invalid input."""
        invalid_input = {
            "market": "OREGON03",
            "data": {
                "latest": {},
                # Missing required fields
            },
            "rules": {},
            "metadata": {}
        }
        
        with self.assertRaises(ValueError):
            self.engine.predict(invalid_input)

    def test_cleanup(self):
        """Test cleanup does nothing."""
        # Should not raise exception
        self.engine.cleanup()


if __name__ == "__main__":
    unittest.main()
