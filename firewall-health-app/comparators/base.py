"""
Base comparator class and common result structure for firewall health metrics comparison
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, List
from dataclasses import dataclass
from enum import Enum

class ComparisonStatus(Enum):
    SUCCESS = "success"
    WARNING = "warning" 
    ERROR = "error"
    INFO = "info"

@dataclass
class ComparisonResult:
    """Standardized result format for all comparators"""
    status: ComparisonStatus
    message: str
    details: Dict[str, Any] = None
    metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
        if self.metrics is None:
            self.metrics = {}

class BaseComparator(ABC):
    """Base class for all firewall health metrics comparators"""
    
    def __init__(self, command_name: str):
        self.command_name = command_name
    
    @abstractmethod
    def parse_output(self, output: str) -> Dict[str, Any]:
        """Parse raw command output into structured data"""
        pass
    
    @abstractmethod
    def compare(self, pre_data: Dict[str, Any], post_data: Dict[str, Any]) -> ComparisonResult:
        """Compare pre and post data and return standardized result"""
        pass
    
    def compare_files(self, pre_file_path: str, post_file_path: str) -> ComparisonResult:
        """Compare two files containing command outputs"""
        try:
            # Read pre file
            with open(pre_file_path, 'r') as f:
                pre_output = f.read()
            
            # Read post file  
            with open(post_file_path, 'r') as f:
                post_output = f.read()
            
            # Parse outputs
            pre_data = self.parse_output(pre_output)
            post_data = self.parse_output(post_output)
            
            # Compare parsed data
            return self.compare(pre_data, post_data)
            
        except FileNotFoundError as e:
            return ComparisonResult(
                status=ComparisonStatus.ERROR,
                message=f"File not found: {e}"
            )
        except Exception as e:
            return ComparisonResult(
                status=ComparisonStatus.ERROR,
                message=f"Error comparing files: {str(e)}"
            )
    
    def _calculate_percentage_change(self, old_value: int, new_value: int) -> float:
        """Calculate percentage change between two values"""
        if old_value == 0:
            return 100.0 if new_value > 0 else 0.0
        return ((new_value - old_value) / old_value) * 100.0