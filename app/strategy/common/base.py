# Standard library imports
import json
from typing import Dict, List, Any, Optional

# Third-party imports
import pandas as pd

# Local imports
from app.rule.common.base import Rule
from app.rule.common.types import ComparisonType


class Strategy:
    """
    Base class for all stock analysis strategies.
    A Strategy is a collection of rules that can be applied to a DataFrame of stock data.
    """
    
    def __init__(self, name: Optional[str] = None, description: Optional[str] = None):
        """
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


class UserStrategy(Strategy):
    """
    A strategy created by a user with customizable rules.
    
    This class allows users to create, save, and load their own strategies
    with specific rules tailored to their trading preferences.
    """
    
    def __init__(self, user_id: str, name: Optional[str] = None, description: Optional[str] = None):
        """    
        Args:
            user_id: Unique identifier for the user who owns this strategy
            name: A unique identifier for this strategy
            description: A human-readable description of what this strategy does
        """
        super().__init__(name, description)
        self.user_id = user_id
        self.metadata = {}  # Additional metadata for the strategy
    
    def set_metadata(self, key: str, value: Any) -> 'UserStrategy':
        """
        Set additional metadata for this strategy.
        
        Args:
            key: Metadata key
            value: Metadata value
            
        Returns:
            This strategy, for method chaining
        """
        self.metadata[key] = value
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert this strategy to a dictionary for storage.
        
        Returns:
            A dictionary representation of this strategy
        """
        rule_dicts = []
        for rule in self.rules:
            # Extract rule attributes
            rule_dict = {
                "type": rule.__class__.__name__,
                "name": rule.name,
                "description": rule.description
            }
            
            # Add rule-specific attributes
            for attr, value in rule.__dict__.items():
                if attr not in ["name", "description"] and not attr.startswith("_"):
                    if isinstance(value, ComparisonType):
                        rule_dict[attr] = value.value
                    else:
                        rule_dict[attr] = value
                        
            rule_dicts.append(rule_dict)
            
        return {
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "rules": rule_dicts,
            "metadata": self.metadata
        }
    
    def to_json(self) -> str:
        """
        Convert this strategy to a JSON string for storage.
        
        Returns:
            A JSON string representation of this strategy
        """
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], rule_factory) -> 'UserStrategy':
        """
        Create a new UserStrategy from a dictionary.
        
        Args:
            data: Dictionary containing strategy data
            rule_factory: Factory for creating rules from dictionary representations
            
        Returns:
            A new UserStrategy
        """
        strategy = cls(
            user_id=data["user_id"],
            name=data["name"],
            description=data.get("description", "")
        )
        
        # Set metadata
        for key, value in data.get("metadata", {}).items():
            strategy.set_metadata(key, value)
        
        # Add rules
        for rule_dict in data.get("rules", []):
            rule = rule_factory.create_rule_from_dict(rule_dict)
            if rule:
                strategy.add_rule(rule)
        
        return strategy
    
    @classmethod
    def from_json(cls, json_str: str, rule_factory) -> 'UserStrategy':
        """
        Create a new UserStrategy from a JSON string.
        
        Args:
            json_str: JSON string containing strategy data
            rule_factory: Factory for creating rules from dictionary representations
            
        Returns:
            A new UserStrategy
        """
        data = json.loads(json_str)
        return cls.from_dict(data, rule_factory) 