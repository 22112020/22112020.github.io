import unittest
from unittest.mock import Mock, patch
from core.executor import Executor, ExecutionError, EngineNotFoundError, DataLoadingError, InvalidInputError
from engines.base_engine import BaseEngine, PredictionResult


class ConcreteTestEngine(BaseEngine):
    """Concrete engine for testing."""
    
    def predict(self, input_data):
        result = PredictionResult("test", "TEST01", "9999")
        result.set_prediction(
            main_digits=["1", "2", "3", "4", "5"],
            backup_digits=["0"],
            confidence=0.75,
            method="test"
        )
        return result


class TestExecutor(unittest.TestCase):
    """Test Executor class."""

    def setUp(self):
        self.executor = Executor()

    def test_get_available_engines(self):
        """Test getting available engines."""
        # Mock the registry
        with patch.object(self.executor.registry, 'list_engines', return_value=['oregon', 'toto_macau']):
            engines = self.executor.get_available_engines()
            self.assertEqual(engines, ['oregon', 'toto_macau'])

    def test_execute_success(self):
        """Test successful execution."""
        # Mock dependencies
        with patch.object(self.executor.data_loader, 'load_market') as mock_load, \
             patch.object(self.executor.registry, 'get_engine') as mock_get:
            
            # Setup mocks
            mock_load.return_value = {
                "name": "TEST01",
                "latest": {"result": "1234", "period": "9999"},
                "history": [],
                "stats": {}
            }
            
            mock_engine = ConcreteTestEngine()
            mock_get.return_value = mock_engine
            
            # Execute
            result = self.executor.execute("test", "TEST01")
            
            # Verify
            self.assertIsInstance(result, PredictionResult)
            self.assertEqual(result.engine, "test")
            self.assertEqual(result.market, "TEST01")

    def test_execute_invalid_engine_name(self):
        """Test execution with invalid engine name."""
        with self.assertRaises(InvalidInputError):
            self.executor.execute("", "TEST01")

    def test_execute_invalid_market_name(self):
        """Test execution with invalid market name."""
        with self.assertRaises(InvalidInputError):
            self.executor.execute("test", "")

    def test_execute_data_loading_failure(self):
        """Test execution when data loading fails."""
        with patch.object(self.executor.data_loader, 'load_market', side_effect=ValueError("No data")):
            with self.assertRaises(DataLoadingError):
                self.executor.execute("test", "TEST01")

    def test_execute_engine_not_found(self):
        """Test execution when engine is not found."""
        with patch.object(self.executor.data_loader, 'load_market', return_value={}), \
             patch.object(self.executor.registry, 'get_engine', side_effect=Exception("Not found")):
            
            with self.assertRaises(EngineNotFoundError):
                self.executor.execute("nonexistent", "TEST01")

    def test_execute_multiple_success(self):
        """Test multiple execution with success."""
        with patch.object(self.executor.data_loader, 'load_market', return_value={
            "name": "TEST", "latest": {}, "history": [], "stats": {}
        }), patch.object(self.executor.registry, 'get_engine', return_value=ConcreteTestEngine()):
            
            results = self.executor.execute_multiple([
                ("test", "TEST01"),
                ("test", "TEST02")
            ])
            
            self.assertEqual(len(results), 2)
            self.assertIsInstance(results[0], PredictionResult)
            self.assertIsInstance(results[1], PredictionResult)

    def test_execute_multiple_with_failure(self):
        """Test multiple execution with partial failure."""
        # Mock to fail first request, succeed second
        def mock_load_market(market_name):
            if market_name == "FAIL":
                raise ValueError("No data")
            return {"name": market_name, "latest": {}, "history": [], "stats": {}}
        
        with patch.object(self.executor.data_loader, 'load_market', side_effect=mock_load_market), \
             patch.object(self.executor.registry, 'get_engine', return_value=ConcreteTestEngine()):
            
            results = self.executor.execute_multiple([
                ("test", "FAIL"),
                ("test", "SUCCESS")
            ])
            
            self.assertEqual(len(results), 2)
            # First should be error result
            self.assertEqual(results[0].prediction["method"], "error")
            self.assertTrue(results[0].metadata.get("error", False))
            # Second should be successful
            self.assertEqual(results[1].prediction["method"], "test")

    def test_error_result_creation(self):
        """Test error result creation."""
        error_result = self.executor._create_error_result(
            "test", "TEST01", "Test error message"
        )
        
        self.assertEqual(error_result.engine, "test")
        self.assertEqual(error_result.market, "TEST01")
        self.assertEqual(error_result.target_period, "ERROR")
        self.assertEqual(error_result.prediction["method"], "error")
        self.assertEqual(error_result.prediction["confidence"], 0.0)
        self.assertTrue(error_result.metadata["error"])
        self.assertEqual(error_result.metadata["error_message"], "Test error message")

    def test_prepare_engine_input(self):
        """Test engine input preparation."""
        market_data = {
            "name": "TEST01",
            "latest": {"result": "1234"},
            "history": []
        }
        
        engine_input = self.executor._prepare_engine_input(market_data, "test_engine")
        
        self.assertEqual(engine_input["market"], "TEST01")
        self.assertEqual(engine_input["data"], market_data)
        self.assertEqual(engine_input["metadata"]["engine"], "test_engine")


class TestExecutorErrors(unittest.TestCase):
    """Test Executor error classes."""

    def test_execution_error(self):
        """Test ExecutionError."""
        with self.assertRaises(ExecutionError):
            raise ExecutionError("Test execution error")

    def test_engine_not_found_error(self):
        """Test EngineNotFoundError."""
        with self.assertRaises(EngineNotFoundError):
            raise EngineNotFoundError("Engine not found")

    def test_data_loading_error(self):
        """Test DataLoadingError."""
        with self.assertRaises(DataLoadingError):
            raise DataLoadingError("Data loading failed")

    def test_invalid_input_error(self):
        """Test InvalidInputError."""
        with self.assertRaises(InvalidInputError):
            raise InvalidInputError("Invalid input")


if __name__ == "__main__":
    unittest.main()
