#!/usr/bin/env python3
"""LunaRegistry - Engine discovery and instantiation.

This module provides the engine registry that discovers and loads prediction engines
from the engines/ directory. It serves as the central engine management component
in the Luna Core architecture.

Key Features:
- Dynamic engine discovery from engines/ directory
- Engine instantiation with validation
- Error handling for invalid engines
- No market logic
- No data access
- Read-only operation
"""

from pathlib import Path
import json
import importlib
from typing import List, Dict, Any, Optional
from engines.base_engine import BaseEngine


class LunaRegistry:
    """Manage engine discovery and instantiation."""

    def __init__(self, engine_path: str = "engines"):
        """Initialize LunaRegistry with engine path.
        
        Args:
            engine_path: Path to engines directory
        """
        self.engine_path = Path(engine_path)
        self._engines_cache: Dict[str, BaseEngine] = {}

    def scan(self) -> List[Dict[str, Any]]:
        """Scan engines directory and return manifest data.
        
        This method maintains backward compatibility with existing code.
        
        Returns:
            List of engine manifests
        """
        result = []

        if not self.engine_path.exists():
            return result

        for folder in self.engine_path.iterdir():
            if folder.is_dir():
                manifest = folder / "manifest.json"

                if manifest.exists():
                    try:
                        data = json.loads(manifest.read_text(encoding="utf-8"))
                        result.append(data)
                    except (json.JSONDecodeError, IOError):
                        # Skip invalid manifests
                        continue

        return result

    def list_engines(self) -> List[str]:
        """List available engine names.
        
        Returns:
            List of engine names that can be instantiated
        """
        engines = []
        
        if not self.engine_path.exists():
            return engines

        for folder in self.engine_path.iterdir():
            if folder.is_dir():
                # Check for manifest.json
                manifest = folder / "manifest.json"
                if manifest.exists():
                    engines.append(folder.name)

        return engines

    def get_engine(self, engine_name: str) -> BaseEngine:
        """Get engine instance by name.
        
        Args:
            engine_name: Name of engine to instantiate
            
        Returns:
            Engine instance
            
        Raises:
            EngineLoadError: If engine cannot be loaded
        """
        # Check cache first
        if engine_name in self._engines_cache:
            return self._engines_cache[engine_name]

        # Validate engine name
        if not engine_name or not isinstance(engine_name, str):
            raise EngineLoadError(f"Invalid engine name: {engine_name}")

        # Load and validate manifest
        manifest = self._load_engine_manifest(engine_name)
        
        # Import module using manifest specification
        module_path = f"engines.{manifest['module']}"
        
        try:
            module = importlib.import_module(module_path)
        except ImportError as e:
            raise EngineLoadError(f"Failed to import module {module_path}: {str(e)}") from e
        
        # Get class using manifest specification
        class_name = manifest['class']
        
        if not hasattr(module, class_name):
            raise EngineLoadError(f"Class {class_name} not found in module {module_path}")
        
        engine_class = getattr(module, class_name)
        
        # Validate inheritance
        if not issubclass(engine_class, BaseEngine):
            raise EngineLoadError(f"{class_name} is not a subclass of BaseEngine")
        
        # Instantiate and cache
        engine_instance = engine_class()
        self._engines_cache[engine_name] = engine_instance
        
        return engine_instance

    def _load_engine_manifest(self, engine_name: str) -> Dict[str, Any]:
        """Load and validate engine manifest.
        
        Args:
            engine_name: Name of engine
            
        Returns:
            Validated manifest dictionary
            
        Raises:
            EngineLoadError: If manifest is invalid
        """
        manifest_file = self.engine_path / engine_name / "manifest.json"
        
        if not manifest_file.exists():
            raise EngineLoadError(f"Manifest not found for engine: {engine_name}")
        
        try:
            manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, IOError) as e:
            raise EngineLoadError(f"Invalid manifest for {engine_name}: {str(e)}") from e
        
        # Validate required fields
        required_fields = ['name', 'module', 'class']
        for field in required_fields:
            if field not in manifest or not manifest[field]:
                raise EngineLoadError(f"Missing required field in manifest: {field}")
        
        # Validate name matches
        if manifest['name'] != engine_name:
            raise EngineLoadError(f"Manifest name mismatch: expected {engine_name}, got {manifest['name']}")
        
        return manifest

    def clear_cache(self) -> None:
        """Clear cached engine instances.
        
        Useful for development and testing.
        """
        self._engines_cache.clear()


class RegistryError(Exception):
    """Base exception for registry errors."""
    pass


class EngineLoadError(RegistryError):
    """Raised when engine loading fails."""
    pass


if __name__ == "__main__":
    print("Luna Engine Registry")
    print("Engine discovery and instantiation")
    
    registry = LunaRegistry()
    
    # List available engines
    engines = registry.list_engines()
    print(f"\nAvailable engines: {len(engines)}")
    for engine in engines:
        print(f"  - {engine}")
