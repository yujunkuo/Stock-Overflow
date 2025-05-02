# Standard library imports
from abc import ABC
from typing import List

# Third-party imports
import pandas as pd

# Local imports
from app.rule.common.base import Rule


class Strategy(ABC):
    """
    Base class for all stock analysis strategies.
    
    A Strategy is a collection of rules that can be applied to a DataFrame of stock data.
    """
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize a new Strategy.
        
        Args:
            name: A unique identifier for this strategy
            description: A human-readable description of what this strategy does
        """
        self.name = name
        self.description = description
        self.rules: List[Rule] = []
    
    def add_rule(self, rule: Rule) -> 'Strategy':
        """
        Add a rule to this strategy.
        
        Args:
            rule: The rule to add
            
        Returns:
            This strategy, for method chaining
        """
        self.rules.append(rule)
        return self
    
    def apply(self, df: pd.DataFrame) -> pd.Series:
        """
        Apply all rules in this strategy to the given DataFrame.
        
        Args:
            df: A DataFrame containing stock data
            
        Returns:
            A boolean Series indicating which rows pass all rules in this strategy
        """
        if not self.rules:
            return pd.Series(True, index=df.index)
        
        result = self.rules[0].apply(df)
        for rule in self.rules[1:]:
            result = result & rule.apply(df)
        
        return result
    
    def __str__(self) -> str:
        return f"{self.name}: {self.description}"


class CompositeStrategy(Strategy):
    """
    A strategy that combines multiple other strategies.
    
    A CompositeStrategy allows you to combine multiple strategies into a single strategy.
    """
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize a new CompositeStrategy.
        
        Args:
            name: A unique identifier for this strategy
            description: A human-readable description of what this strategy does
        """
        super().__init__(name, description)
        self.strategies: List[Strategy] = []
    
    def add_strategy(self, strategy: Strategy) -> 'CompositeStrategy':
        """
        Add a strategy to this composite strategy.
        
        Args:
            strategy: The strategy to add
            
        Returns:
            This composite strategy, for method chaining
        """
        self.strategies.append(strategy)
        return self
    
    def apply(self, df: pd.DataFrame) -> pd.Series:
        """
        Apply all strategies in this composite strategy to the given DataFrame.
        
        Args:
            df: A DataFrame containing stock data
            
        Returns:
            A boolean Series indicating which rows pass all strategies in this composite strategy
        """
        if not self.strategies:
            return pd.Series(True, index=df.index)
        
        result = self.strategies[0].apply(df)
        for strategy in self.strategies[1:]:
            result = result & strategy.apply(df)
        
        return result