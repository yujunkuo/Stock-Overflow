# Standard library imports
from enum import Enum

class ComparisonType(Enum):
    """Enum for different types of value comparisons."""
    LESS_THAN = "less_than"
    GREATER_THAN = "greater_than" 
    BETWEEN = "between"