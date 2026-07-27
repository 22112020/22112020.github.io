import unittest
import shutil
from pathlib import Path
from core.registry import LunaRegistry, RegistryError, EngineLoadError

PROJECT_ROOT = Path(__file__).resolve().parent.parent

class TestLunaRegistry(unittest.TestCase):
    """Test LunaRegistry class."""

    def setUp(self):
        # Use actual engines directory in the project
        self.engines_dir = PROJECT_ROOT / "engines"
        self.engines_dir.mkdir(exist_ok=True)
        
        # Create valid test engine
        self.test_engine_dir = self.engines_dir / "test_engine"
        self.test_engine_dir.mkdir(exist_ok=True)
        
        # Create valid engine module
        self.engine_module = self.test_engine_dir / "test_engine.py"
        self.engine_module.write_text("""
from engines.base_engine import BaseEngine, PredictionResult

class Test_engineEngine(BaseEngine):
    def predict(self, input_data):
        result = PredictionResult("test_engine", "TEST", "9999")
        result.set_prediction(["1","2","3","4","5"], ["0"], 0.75, "test")
        return result
""")
        
        # Create manifest.json with required fields
        self.manifest = self.test_engine_dir / "manifest.json"
        self.manifest.write_text('''{
  "name": "test_engine",
  "version": "1.0",
  "type": "test",
  "rule": "test_rule",
  "module": "test_engine.test_engine",
  "class": "Test_engineEngine"
}''')
        
        # Create invalid engine (missing required fields)
        self.invalid_engine_dir = self.engines_dir / "invalid_engine"
        self.invalid_engine_dir.mkdir(exist_ok=True)
        self.invalid_manifest = self.invalid_engine_dir / "manifest.json"
        self.invalid_manifest.write_text('''{
  "name": "invalid_engine",
  "version": "1.0"
}''')

    def tearDown(self):
        # Clean up test engines
        if self.test_engine_dir.exists():
            shutil.rmtree(self.test_engine_dir)
        if self.invalid_engine_dir.exists():
            shutil.rmtree(self.invalid_engine_dir)

    def test_scan_engines(self):
        """Test scanning engines directory."""
        registry = LunaRegistry()
        manifests = registry.scan()
        
        # Should find both valid and invalid manifests
        names = [m.get("name") for m in manifests]
        self.assertIn("test_engine", names)
        self.assertIn("invalid_engine", names)

    def test_list_engines(self):
        """Test listing available engines."""
        registry = LunaRegistry()
        engines = registry.list_engines()
        
        # Should list engines with valid manifests
        self.assertIn("test_engine", engines)

    def test_get_engine_success(self):
        """Test getting valid engine instance."""
        registry = LunaRegistry()
        engine = registry.get_engine("test_engine")
        
        # Should return engine instance
        self.assertIsNotNone(engine)
        self.assertEqual(engine.engine_name, "test_engine")

    def test_get_engine_nonexistent(self):
        """Test getting nonexistent engine."""
        registry = LunaRegistry()
        
        with self.assertRaises(EngineLoadError):
            registry.get_engine("nonexistent_engine_xyz")

    def test_get_engine_invalid_name(self):
        """Test getting engine with invalid name."""
        registry = LunaRegistry()
        
        with self.assertRaises(EngineLoadError):
            registry.get_engine("")

    def test_get_engine_missing_manifest(self):
        """Test getting engine with missing manifest."""
        registry = LunaRegistry()
        
        with self.assertRaises(EngineLoadError):
            registry.get_engine("missing_manifest_engine")

    def test_get_engine_invalid_manifest(self):
        """Test getting engine with invalid manifest (missing required fields)."""
        registry = LunaRegistry()
        
        with self.assertRaises(EngineLoadError):
            registry.get_engine("invalid_engine")

    def test_engine_caching(self):
        """Test engine instance caching."""
        registry = LunaRegistry()
        
        # Get engine twice
        engine1 = registry.get_engine("test_engine")
        engine2 = registry.get_engine("test_engine")
        
        # Should return same instance
        self.assertIs(engine1, engine2)

    def test_clear_cache(self):
        """Test cache clearing."""
        registry = LunaRegistry()
        
        # Get engine and cache it
        engine1 = registry.get_engine("test_engine")
        
        # Clear cache
        registry.clear_cache()
        
        # Get engine again
        engine2 = registry.get_engine("test_engine")
        
        # Should be different instance after cache clear
        self.assertIsNot(engine1, engine2)

    def test_manifest_validation(self):
        """Test manifest validation."""
        registry = LunaRegistry()
        
        # Test with invalid manifest (wrong name)
        invalid_dir = self.engines_dir / "wrong_name"
        invalid_dir.mkdir(exist_ok=True)
        (invalid_dir / "manifest.json").write_text('''{
  "name": "different_name",
  "module": "wrong_name.wrong_name_engine",
  "class": "WrongNameEngine"
}''')
        
        with self.assertRaises(EngineLoadError):
            registry.get_engine("wrong_name")
        
        # Clean up
        shutil.rmtree(invalid_dir)


class TestRegistryErrors(unittest.TestCase):
    """Test registry error classes."""

    def test_registry_error(self):
        """Test RegistryError base class."""
        with self.assertRaises(RegistryError):
            raise RegistryError("Test registry error")

    def test_engine_load_error(self):
        """Test EngineLoadError."""
        with self.assertRaises(EngineLoadError):
            raise EngineLoadError("Engine load failed")


if __name__ == "__main__":
    unittest.main()
