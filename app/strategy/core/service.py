# Standard library imports
import os
import datetime
from typing import Dict, List, Any, Optional

# Local imports
from app.rule.common.factory import RuleFactory
from app.strategy.common.base import UserStrategy


class StrategyService:
    """
    Service for managing user strategies.
    
    This class provides methods for creating, retrieving, updating, and deleting
    user strategies, as well as managing the persistence of strategies.
    """
    
    def __init__(self, storage_dir: str, rule_factory: RuleFactory):
        """
        Args:
            storage_dir: Directory where strategies will be stored
            rule_factory: Factory for creating rules from dictionary representations
        """
        self.storage_dir = storage_dir
        self.rule_factory = rule_factory
        
        # Create the storage directory if it doesn't exist
        os.makedirs(storage_dir, exist_ok=True)
    
    def _get_user_dir(self, user_id: str) -> str:
        """
        Get the directory for a user's strategies.
        
        Args:
            user_id: The user ID
            
        Returns:
            The path to the user's strategy directory
        """
        user_dir = os.path.join(self.storage_dir, user_id)
        os.makedirs(user_dir, exist_ok=True)
        return user_dir
    
    def _get_strategy_path(self, user_id: str, strategy_name: str) -> str:
        """
        Get the path to a strategy file.
        
        Args:
            user_id: The user ID
            strategy_name: The strategy name
            
        Returns:
            The path to the strategy file
        """
        return os.path.join(self._get_user_dir(user_id), f"{strategy_name}.json")
    
    def _save_strategy(self, strategy: UserStrategy) -> None:
        """
        Save a strategy to disk.
        
        Args:
            strategy: The strategy to save
        """
        strategy_path = self._get_strategy_path(strategy.user_id, strategy.name)
        with open(strategy_path, "w") as f:
            f.write(strategy.to_json()) 
    
    def create_strategy(self, user_id: str, name: str, description: str, rules: List[Dict[str, Any]]) -> UserStrategy:
        """
        Create a new user strategy.
        
        Args:
            user_id: The user ID
            name: The strategy name
            description: The strategy description
            rules: A list of rule dictionaries
            
        Returns:
            The created UserStrategy
        
        Raises:
            ValueError: If a strategy with the same name already exists for the user
        """
        # Check if a strategy with this name already exists
        if os.path.exists(self._get_strategy_path(user_id, name)):
            raise ValueError(f"Strategy with name '{name}' already exists for user '{user_id}'")
        
        # Create the strategy
        strategy = UserStrategy(user_id, name, description)
        
        # Add the rules
        for rule_dict in rules:
            rule = self.rule_factory.create_rule_from_dict(rule_dict)
            if rule:
                strategy.add_rule(rule)
        
        # Add metadata
        strategy.set_metadata("created_at", datetime.datetime.now().isoformat())
        strategy.set_metadata("updated_at", datetime.datetime.now().isoformat())
        
        # Save the strategy
        self._save_strategy(strategy)
        
        return strategy
    
    def get_strategy(self, user_id: str, strategy_name: str) -> Optional[UserStrategy]:
        """
        Get a user strategy by name.
        
        Args:
            user_id: The user ID
            strategy_name: The strategy name
            
        Returns:
            The UserStrategy, or None if it doesn't exist
        """
        strategy_path = self._get_strategy_path(user_id, strategy_name)
        if not os.path.exists(strategy_path):
            return None
        
        with open(strategy_path, "r") as f:
            return UserStrategy.from_json(f.read(), self.rule_factory)
    
    def get_user_strategies(self, user_id: str) -> List[UserStrategy]:
        """
        Get all strategies for a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            A list of UserStrategy instances
        """
        user_dir = self._get_user_dir(user_id)
        strategies = []
        
        for filename in os.listdir(user_dir):
            if filename.endswith(".json"):
                with open(os.path.join(user_dir, filename), "r") as f:
                    strategy = UserStrategy.from_json(f.read(), self.rule_factory)
                    strategies.append(strategy)
        
        return strategies
    
    def update_strategy(self, user_id: str, strategy_name: str, description: Optional[str] = None, rules: Optional[List[Dict[str, Any]]] = None) -> Optional[UserStrategy]:
        """
        Update an existing user strategy.
        
        Args:
            user_id: The user ID
            strategy_name: The strategy name
            description: The new strategy description (optional)
            rules: A new list of rule dictionaries (optional)
            
        Returns:
            The updated UserStrategy, or None if it doesn't exist
        """
        strategy = self.get_strategy(user_id, strategy_name)
        if not strategy:
            return None
        
        # Update description if provided
        if description is not None:
            strategy.description = description
        
        # Update rules if provided
        if rules is not None:
            strategy.rules = []
            for rule_dict in rules:
                rule = self.rule_factory.create_rule_from_dict(rule_dict)
                if rule:
                    strategy.add_rule(rule)
        
        # Update metadata
        strategy.set_metadata("updated_at", datetime.datetime.now().isoformat())
        
        # Save the strategy
        self._save_strategy(strategy)
        
        return strategy
    
    def delete_strategy(self, user_id: str, strategy_name: str) -> bool:
        """
        Delete a user strategy.
        
        Args:
            user_id: The user ID
            strategy_name: The strategy name
            
        Returns:
            True if the strategy was deleted, False if it didn't exist
        """
        strategy_path = self._get_strategy_path(user_id, strategy_name)
        if not os.path.exists(strategy_path):
            return False
        
        os.remove(strategy_path)
        return True
