import unittest
from engines.base_engine import (
    BaseEngine, PredictionResult, PredictionError, 
    InvalidInputError, AlgorithmError
)


class ConcreteEngineForTesting(BaseEngine):
    """Concrete implementation for testing BaseEngine."""
    
    def predict(self, input_data):
        # Simple implementation for testing
        result = PredictionResult("test", "TEST01", "9999")
        result.set_prediction(
            main_digits=["1", "2", "3", "4", "5"],
            backup_digits=["0"],
            confidence=0.75,
            method="test_method"
        )
        result.set_analysis({
            "test_analysis": True,
            "value": 42
        })
        return result


class TestPredictionResult(unittest.TestCase):
    """Test PredictionResult class."""

    def test_init(self):
        """Test PredictionResult initialization."""
        result = PredictionResult("oregon", "OREGON03", "1991")
        
        self.assertEqual(result.engine, "oregon")
        self.assertEqual(result.market, "OREGON03")
        self.assertEqual(result.target_period, "1991")
        self.assertEqual(result.prediction, {})
        self.assertEqual(result.analysis, {})
        self.assertIn("generated_at", result.metadata)
        self.assertEqual(result.metadata["timezone"], "Asia/Jakarta")

    def test_set_prediction(self):
        """Test setting prediction data."""
        result = PredictionResult("test", "TEST", "1234")
        
        result.set_prediction(
            main_digits=["1", "2", "3", "4", "5"],
            backup_digits=["0"],
            confidence=0.95,
            method="frequency"
        )
        
        self.assertEqual(result.prediction["main"], ["1", "2", "3", "4", "5"])
        self.assertEqual(result.prediction["backup"], ["0"])
        self.assertEqual(result.prediction["confidence"], 0.95)
        self.assertEqual(result.prediction["method"], "frequency")

    def test_set_analysis(self):
        """Test setting analysis data."""
        result = PredictionResult("test", "TEST", "1234")
        
        analysis_data = {
            "digit_frequency": {"1": 5, "2": 3},
            "source_count": 3
        }
        result.set_analysis(analysis_data)
        
        self.assertEqual(result.analysis["digit_frequency"], {"1": 5, "2": 3})
        self.assertEqual(result.analysis["source_count"], 3)

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = PredictionResult("oregon", "OREGON03", "1991")
        result.set_prediction(
            main_digits=["2", "4", "7", "8", "0"],
            backup_digits=["3"],
            confidence=0.88,
            method="frequency_analysis"
        )
        result.set_analysis({"test": "data"})
        
        result_dict = result.to_dict()
        
        self.assertIn("engine", result_dict)
        self.assertIn("market", result_dict)
        self.assertIn("target_period", result_dict)
        self.assertIn("prediction", result_dict)
        self.assertIn("analysis", result_dict)
        self.assertIn("metadata", result_dict)
        
        self.assertEqual(result_dict["engine"], "oregon")
        self.assertEqual(result_dict["market"], "OREGON03")
        self.assertEqual(result_dict["target_period"], "1991")
        self.assertEqual(result_dict["prediction"]["main"], ["2", "4", "7", "8", "0"])

    def test_metadata_has_utc7(self):
        """Test metadata contains UTC+7 timezone."""
        result = PredictionResult("test", "TEST", "1234")
        
        self.assertEqual(result.metadata["timezone"], "Asia/Jakarta")
        self.assertIn("generated_at", result.metadata)


class TestBaseEngine(unittest.TestCase):
    """Test BaseEngine class."""

    def test_abstract_predict_raises(self):
        """Test that BaseEngine.predict is abstract."""
        with self.assertRaises(TypeError):
            BaseEngine().predict({})  # Cannot instantiate abstract class

    def test_validate_input_valid(self):
        """Test input validation with valid data."""
        engine = ConcreteEngineForTesting()
        
        valid_input = {
            "market": "OREGON03",
            "data": {
                "latest": {"date": "24-07-2026", "time": "11:00:00", "day": "Friday", 
                          "period": "1990", "result": "8207"},
                "history": [],
                "stats": {"total_records": 1}
            },
            "rules": {"some_rule": True},
            "metadata": {}
        }
        
        self.assertTrue(engine.validate_input(valid_input))

    def test_validate_input_missing_keys(self):
        """Test input validation with missing required keys."""
        engine = ConcreteEngineForTesting()
        
        invalid_input = {
            "market": "OREGON03",
            "data": {}
            # Missing "rules" and "metadata"
        }
        
        self.assertFalse(engine.validate_input(invalid_input))

    def test_validate_input_missing_data_subkeys(self):
        """Test input validation with missing data subkeys."""
        engine = ConcreteEngineForTesting()
        
        invalid_input = {
            "market": "OREGON03",
            "data": {
                "latest": {},
                # Missing "history" and "stats"
            },
            "rules": {},
            "metadata": {}
        }
        
        self.assertFalse(engine.validate_input(invalid_input))

    def test_cleanup_default(self):
        """Test default cleanup does nothing."""
        engine = ConcreteEngineForTesting()
        # Should not raise any exception
        engine.cleanup()

    def test_concrete_engine_predict_returns_prediction(self):
        """Test concrete engine predict returns valid PredictionResult."""
        engine = ConcreteEngineForTesting()
        input_data = {
            "market": "TEST01",
            "data": {},
            "rules": {},
            "metadata": {}
        }
        
        result = engine.predict(input_data)
        
        self.assertIsInstance(result, PredictionResult)
        result_dict = result.to_dict()
        self.assertIn("prediction", result_dict)
        self.assertIn("analysis", result_dict)


class TestPredictionErrors(unittest.TestCase):
    """Test prediction error classes."""

    def test_prediction_error(self):
        """Test PredictionError base class."""
        with self.assertRaises(PredictionError):
            raise PredictionError("Test error")

    def test_invalid_input_error(self):
        """Test InvalidInputError."""
        with self.assertRaises(InvalidInputError):
            raise InvalidInputError("Invalid input")

    def test_algorithm_error(self):
        """Test AlgorithmError."""
        with self.assertRaises(AlgorithmError):
            raise AlgorithmError("Algorithm failed")


if __name__ == "__main__":
    unittest.main()
