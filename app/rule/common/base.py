# Standard library imports
from abc import ABC, abstractmethod
from typing import Optional

# Third-party imports
import pandas as pd

# Local imports
from app.rule.common.types import ComparisonType


class Rule(ABC):
    """
    Base class for all filtering rules.
    A Rule is a single condition that can be applied to a DataFrame of stock data.
    """
    
    def __init__(self, name: Optional[str], description: Optional[str]):
        """
        Args:
            name: A unique identifier for this rule
            description: A human-readable description of what this rule does
        """
        self.name = name
        self.description = description
    
    @abstractmethod
    def apply(self, df: pd.DataFrame) -> pd.Series:
        """
        Apply this rule to the given DataFrame.
        
        Args:
            df: A DataFrame containing stock data
            
        Returns:
            A boolean Series indicating which rows pass this rule
        """
        pass
    
    def __str__(self) -> str:
        return f"{self.name}: {self.description}"


class RangeRule(Rule):
    """Base class for rules that check if the value of a column is within a specified range."""
    
    def __init__(
        self, 
        column: str, 
        comparison_type: ComparisonType, 
        threshold_1: float, 
        threshold_2: Optional[float] = None, 
        name: Optional[str] = None, 
        description: Optional[str] = None,
    ):
        """
        Args:
            column: The DataFrame column to check
            comparison_type: Type of comparison (LESS_THAN, GREATER_THAN, BETWEEN)
            threshold_1: First threshold value
            threshold_2: Second threshold value (required for BETWEEN comparison)
            name: A unique identifier for this rule
            description: A human-readable description of what this rule does
        """
        if comparison_type == ComparisonType.BETWEEN and threshold_2 is None:
            raise ValueError("threshold_2 is required for BETWEEN comparison")
                
        super().__init__(name, description)
        self.column = column
        self.comparison_type = comparison_type
        self.threshold_1 = threshold_1
        self.threshold_2 = threshold_2
    
    def apply(self, df: pd.DataFrame) -> pd.Series:
        if self.comparison_type == ComparisonType.LESS_THAN:
            return df[self.column] <= self.threshold_1
        elif self.comparison_type == ComparisonType.GREATER_THAN:
            return df[self.column] >= self.threshold_1
        else:
            return (df[self.column] >= self.threshold_1) & (df[self.column] <= self.threshold_2)


class RatioRangeRule(RangeRule):
    """Base class for rules that check if the ratio between two columns is within a specified range."""
    
    def __init__(
        self, 
        column: str, 
        base_column: str, 
        comparison_type: ComparisonType, 
        threshold_1: float, 
        threshold_2: Optional[float] = None, 
        name: Optional[str] = None, 
        description: Optional[str] = None,
    ):
        """
        Args:
            column: The DataFrame column to check
            base_column: The DataFrame column to use as the base for the ratio
            comparison_type: Type of comparison (LESS_THAN, GREATER_THAN, BETWEEN)
            threshold_1: First threshold value
            threshold_2: Second threshold value (required for BETWEEN comparison)
            name: A unique identifier for this rule
            description: A human-readable description of what this rule does
        """
        super().__init__(column, comparison_type, threshold_1, threshold_2, name, description)
        self.base_column = base_column

    def apply(self, df: pd.DataFrame) -> pd.Series:
        return df.apply(self._check_row, axis=1)

    def _check_row(self, row) -> bool:
        threshold_1 = row[self.base_column] * self.threshold_1
        threshold_2 = row[self.base_column] * self.threshold_2 if self.threshold_2 is not None else None
        
        value = row[self.column]
        
        if self.comparison_type == ComparisonType.LESS_THAN:
            return value <= threshold_1
        elif self.comparison_type == ComparisonType.GREATER_THAN:
            return value >= threshold_1
        else:
            return threshold_1 <= value <= threshold_2


class TechnicalRule(Rule, ABC):
    """Base class for technical analysis rules."""
    
    def __init__(
        self, 
        days: int, 
        name: Optional[str] = None, 
        description: Optional[str] = None,
    ):
        """
        Args:
            days: Number of days to look back
            name: A unique identifier for this rule
            description: A human-readable description of what this rule does
        """
        super().__init__(name, description)
        self.days = days


class OneIndicatorRule(TechnicalRule, ABC):
    """Base class for rules that check for one technical indicator."""
    
    def __init__(
        self, 
        indicator: str, 
        days: int, 
        name: Optional[str] = None, 
        description: Optional[str] = None,
    ):
        """
        Args:
            indicator: Technical indicator to analyze
            days: Number of days to look back
            name: A unique identifier for this rule
            description: A human-readable description of what this rule does
        """
        super().__init__(days, name, description)
        self.indicator = indicator


class TwoIndicatorsRule(TechnicalRule, ABC):
    """Base class for rules that check for two technical indicators."""
    
    def __init__(
        self, 
        indicator_1: str, 
        indicator_2: str, 
        days: int, 
        name: Optional[str] = None, 
        description: Optional[str] = None,
    ):
        """
        Args:
            indicator_1: First technical indicator
            indicator_2: Second technical indicator
            days: Number of days to look back
            name: A unique identifier for this rule
            description: A human-readable description of what this rule does
        """
        super().__init__(days, name, description)
        self.indicator_1 = indicator_1
        self.indicator_2 = indicator_2


class ThreeIndicatorsRule(TechnicalRule, ABC):
    """Base class for rules that check for three technical indicators."""
    
    def __init__(
        self, 
        indicator_1: str, 
        indicator_2: str, 
        indicator_3: str, 
        days: int, 
        name: Optional[str] = None, 
        description: Optional[str] = None,
    ):
        """
        Args:
            indicator_1: First technical indicator
            indicator_2: Second technical indicator
            indicator_3: Third technical indicator
            days: Number of days to look back
            name: A unique identifier for this rule
            description: A human-readable description of what this rule does
        """
        super().__init__(days, name, description)
        self.indicator_1 = indicator_1
        self.indicator_2 = indicator_2
        self.indicator_3 = indicator_3