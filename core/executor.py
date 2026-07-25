#!/usr/bin/env python3
"""Executor - Coordinate engine execution and data flow.

This module implements the engine execution coordinator that manages the workflow
between DataLoader, engines, and result formatting. It serves as the central
orchestration component in the Luna Core architecture.

Key Features:
- Engine lifecycle management
- Data flow coordination
- Error handling
- Result standardization
- Registry integration
- No market-specific logic
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from core.registry import LunaRegistry
from core.data_loader import DataLoader
from core.market_sync import MarketSync
from engines.base_engine import BaseEngine, PredictionResult, PredictionError


def _resolve_project_root(project_root: Optional[str] = None) -> Path:
    """Resolve project root from explicit input or current workspace."""
    if project_root:
        return Path(project_root).expanduser().resolve()

    current = Path.cwd().resolve()
    if (current / "core").exists() and (current / "data_harian").exists():
        return current

    for candidate in [Path(__file__).resolve().parents[1], Path(".").resolve()]:
        if (candidate / "core").exists() and (candidate / "data_harian").exists():
            return candidate

    return current


class Executor:
    """Coordinate engine execution and data flow."""

    def __init__(self, project_root: Optional[str] = None):
        """Initialize Executor with project root.
        
        Args:
            project_root: Path to Togelku project root directory
        """
        resolved_root = _resolve_project_root(project_root)
        self.project_root = resolved_root
        self.registry = LunaRegistry(engine_path=str(resolved_root / "engines"))
        self.data_loader = DataLoader(project_root=str(resolved_root))
        self.market_aliases = {
            "TOTO MACAU": "4DTOTOMACAU",
            "TOTO_MACAU": "4DTOTOMACAU",
            "TOTOMACAU": "4DTOTOMACAU",
        }

    def _resolve_market(self, name: str) -> str:
        """Resolve market name alias to canonical form."""
        normalized = name.strip().upper()
        if normalized in self.market_aliases:
            return self.market_aliases[normalized]
        return str(name)

    def _run_sync(self):
        """Sync all data_harian files to pasaran_luna before prediction.
        
        Ensures latest daily data is always available for prediction engines,
        especially for markets with multiple draws per day (e.g. Toto Macau).
        """
        sync = MarketSync(project_root=str(self.project_root))
        sync.sync_all()

    def get_available_engines(self) -> List[str]:
        """Get list of available engine names.
        
        Returns:
            List of registered engine names
        """
        return self.registry.list_engines()

    def execute(self, engine_name: str, market_name: str) -> PredictionResult:
        """Execute prediction for a specific engine and market.
        
        Args:
            engine_name: Name of engine to use
            market_name: Name of market to predict
            
        Returns:
            PredictionResult containing prediction and analysis
            
        Raises:
            ExecutionError: If execution fails
        """
        try:
            # 1. Validate inputs
            self._validate_inputs(engine_name, market_name)
            
            # 2. Resolve market name alias
            market_name = self._resolve_market(market_name)
            
            # 3. Sync latest data from data_harian to pasaran_luna
            self._run_sync()
            
            # 4. Load market data
            market_data = self._load_market_data(market_name)
            
            # 5. Get engine instance
            engine = self._get_engine_instance(engine_name)
            
            # 6. Prepare input for engine
            engine_input = self._prepare_engine_input(market_data, engine_name)
            
            # 7. Execute prediction
            result = engine.predict(engine_input)
            
            # 8. Clean up
            engine.cleanup()
            
            return result
            
        except ExecutionError:
            raise
        except Exception as e:
            raise ExecutionError(f"Execution failed: {str(e)}") from e

    def _validate_inputs(self, engine_name: str, market_name: str) -> None:
        """Validate execution inputs.
        
        Args:
            engine_name: Engine name to validate
            market_name: Market name to validate
            
        Raises:
            InvalidInputError: If inputs are invalid
        """
        if not engine_name or not isinstance(engine_name, str):
            raise InvalidInputError("Engine name must be a non-empty string")
        
        if not market_name or not isinstance(market_name, str):
            raise InvalidInputError("Market name must be a non-empty string")

    def _load_market_data(self, market_name: str) -> Dict[str, Any]:
        """Load market data using DataLoader.
        
        Args:
            market_name: Name of market to load
            
        Returns:
            Dictionary containing market data
            
        Raises:
            DataLoadingError: If data loading fails
        """
        try:
            return self.data_loader.load_market(market_name)
        except ValueError as e:
            raise DataLoadingError(f"Failed to load market data: {str(e)}") from e

    def _get_engine_instance(self, engine_name: str) -> BaseEngine:
        """Get engine instance from registry.
        
        Args:
            engine_name: Name of engine to retrieve
            
        Returns:
            Engine instance
            
        Raises:
            EngineNotFoundError: If engine is not registered
        """
        try:
            return self.registry.get_engine(engine_name)
        except Exception as e:
            raise EngineNotFoundError(f"Engine '{engine_name}' not found: {str(e)}") from e

    def _prepare_engine_input(self, market_data: Dict[str, Any], engine_name: str) -> Dict[str, Any]:
        """Prepare input data for engine.
        
        Args:
            market_data: Market data from DataLoader
            engine_name: Name of target engine
            
        Returns:
            Dictionary containing prepared input data
        """
        # Add engine-specific context
        engine_input = {
            "market": market_data["name"],
            "data": market_data,
            "rules": {},  # Rules would be loaded by engine if needed
            "metadata": {
                "generated_by": "executor",
                "engine": engine_name
            }
        }
        
        return engine_input

    def execute_multiple(self, requests: List[Tuple[str, str]]) -> List[PredictionResult]:
        """Execute multiple engine/market pairs.
        
        Args:
            requests: List of (engine_name, market_name) tuples
            
        Returns:
            List of PredictionResults
        """
        results = []
        
        for engine_name, market_name in requests:
            try:
                result = self.execute(engine_name, market_name)
                results.append(result)
            except ExecutionError as e:
                # Create error result for failed execution
                error_result = self._create_error_result(engine_name, market_name, str(e))
                results.append(error_result)
        
        return results

    def _create_error_result(self, engine_name: str, market_name: str, error_msg: str) -> PredictionResult:
        """Create standardized error result.
        
        Args:
            engine_name: Engine name
            market_name: Market name
            error_msg: Error message
            
        Returns:
            PredictionResult with error information
        """
        result = PredictionResult(engine_name, market_name, "ERROR")
        result.set_prediction(
            main_digits=[],
            backup_digits=[],
            confidence=0.0,
            method="error"
        )
        result.set_analysis({
            "error": error_msg,
            "status": "failed"
        })
        
        # Add error flag to metadata
        result.metadata["error"] = True
        result.metadata["error_message"] = error_msg
        
        return result


class ExecutionError(Exception):
    """Base exception for execution failures."""
    pass


class EngineNotFoundError(ExecutionError):
    """Raised when engine is not registered."""
    pass


class DataLoadingError(ExecutionError):
    """Raised when data loading fails."""
    pass


class InvalidInputError(ExecutionError):
    """Raised when input validation fails."""
    pass


if __name__ == "__main__":
    print("Luna Core Executor")
    print("Engine execution coordinator")
    print("Usage: Import and use Executor class")
