# Standard library imports
from typing import Dict, Any, Optional, Type, List

# Local imports
from app.rule.common.base import Rule
from app.model.enums import ComparisonType

class RuleFactory:
    """
    Factory for creating Rule instances from dictionary representations.
    
    This class maintains a registry of rule types and is responsible for
    instantiating rules based on their dictionary representation.
    """
    
    def __init__(self):
        """Initialize a new RuleFactory with an empty registry."""
        self._registry = {}
    
    def register_rule_type(self, rule_type_name: str, rule_class: Type[Rule]) -> None:
        """
        Register a rule class with this factory.
        
        Args:
            rule_type_name: The name of the rule type
            rule_class: The rule class to register
        """
        self._registry[rule_type_name] = rule_class
    
    def register_rule_types(self, rule_mapping: Dict[str, Type[Rule]]) -> None:
        """
        Register multiple rule classes with this factory.
        
        Args:
            rule_mapping: A dictionary mapping rule type names to rule classes
        """
        for rule_type_name, rule_class in rule_mapping.items():
            self.register_rule_type(rule_type_name, rule_class)
    
    def get_available_rule_types(self) -> List[str]:
        """
        Get a list of all available rule types.
        
        Returns:
            A list of rule type names
        """
        return list(self._registry.keys())
    
    def create_rule_from_dict(self, rule_dict: Dict[str, Any]) -> Optional[Rule]:
        """
        Create a Rule instance from a dictionary representation.
        
        Args:
            rule_dict: A dictionary containing rule data
            
        Returns:
            A Rule instance, or None if the rule type is not registered
        """
        rule_type = rule_dict.get("type")
        if not rule_type or rule_type not in self._registry:
            return None
        
        rule_class = self._registry[rule_type]
        
        # Extract common parameters
        name = rule_dict.get("name")
        description = rule_dict.get("description")
        
        # Process ComparisonType enum values
        for key, value in rule_dict.items():
            if key == "comparison_type" and isinstance(value, str):
                rule_dict[key] = ComparisonType(value)
        
        # Remove type, name, and description from the dict
        rule_params = {k: v for k, v in rule_dict.items() if k not in ["type", "name", "description"]}
        
        # Create and return the rule
        try:
            return rule_class(name=name, description=description, **rule_params)
        except TypeError as e:
            # Handle the case where the rule constructor doesn't match the parameters
            print(f"Error creating rule: {e}")
            return None


def create_rule_factory() -> RuleFactory:
    """
    Create and initialize a RuleFactory with all available rule types.
    
    Returns:
        An initialized RuleFactory
    """
    factory = RuleFactory()
    
    # Register all rule types
    rule_mapping = {
        # # Fundamental rules
        # "PERangeRule": PERangeRule,
        # "PBRangeRule": PBRangeRule,
        # "DividendYieldRangeRule": DividendYieldRangeRule,
        
        # # Technical rules
        # "SMARule": SMARule,
        # "CrossAboveRule": CrossAboveRule,
        # "CrossBelowRule": CrossBelowRule,
        # "RSIRule": RSIRule,
        # "MACDRule": MACDRule,
        # "BollingerBandsRule": BollingerBandsRule,
        # "VolumeRule": VolumeRule,
        
        # # Chip rules
        # "ForeignInvestorsRule": ForeignInvestorsRule,
        # "InvestmentTrustRule": InvestmentTrustRule,
        # "DealersRule": DealersRule,
        # "MarginTradingRule": MarginTradingRule,
        # "ShortSellingRule": ShortSellingRule,
    }
    
    factory.register_rule_types(rule_mapping)
    
    return factory 