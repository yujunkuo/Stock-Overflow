"""
Chip Analysis Rules

This module provides chip analysis rules for stock screening.
"""

# Local imports
from app.rule.common.base import RangeRule, RatioRangeRule


# ===== Institutional Investors' Movements Rules =====

class InstitutionalBuySellVolumeRule(RangeRule):
    """Rule to check if total institutional investors' buy sell volume is within specified range."""
    
    def __init__(self, comparison_type, threshold_1, threshold_2=None, name=None, description=None):
        super().__init__("三大法人買賣超", comparison_type, threshold_1, threshold_2, name, description)


class ForeignBuySellVolumeRule(RangeRule):
    """Rule to check if foreign investors' buy sell volume is within specified range."""
    
    def __init__(self, comparison_type, threshold_1, threshold_2=None, name=None, description=None):
        super().__init__("外資買賣超", comparison_type, threshold_1, threshold_2, name, description)


class InvestmentBuySellVolumeRule(RangeRule):
    """Rule to check if investment bank's buy sell volume is within specified range."""
    
    def __init__(self, comparison_type, threshold_1, threshold_2=None, name=None, description=None):
        super().__init__("投信買賣超", comparison_type, threshold_1, threshold_2, name, description)


class DealerBuySellVolumeRule(RangeRule):
    """Rule to check if dealer's buy sell volume is within specified range."""
    
    def __init__(self, comparison_type, threshold_1, threshold_2=None, name=None, description=None):
        super().__init__("自營商買賣超", comparison_type, threshold_1, threshold_2, name, description)  


class InstitutionalBuySellRatioRule(RatioRangeRule):
    """Rule to check if institutional investors' buy sell ratio is within specified range."""
    
    def __init__(self, comparison_type, threshold_1, threshold_2=None, name=None, description=None):
        super().__init__("三大法人買賣超", "成交量", comparison_type, threshold_1, threshold_2, name, description)


class ForeignBuySellRatioRule(RatioRangeRule):
    """Rule to check if foreign investors' buy sell ratio is within specified range."""
    
    def __init__(self, comparison_type, threshold_1, threshold_2=None, name=None, description=None):
        super().__init__("外資買賣超", "成交量", comparison_type, threshold_1, threshold_2, name, description)
        

class InvestmentBuySellRatioRule(RatioRangeRule):
    """Rule to check if investment bank's buy sell ratio is within specified range."""
    
    def __init__(self, comparison_type, threshold_1, threshold_2=None, name=None, description=None):
        super().__init__("投信買賣超", "成交量", comparison_type, threshold_1, threshold_2, name, description)
        

class DealerBuySellRatioRule(RatioRangeRule):
    """Rule to check if dealer's buy sell ratio is within specified range."""
    
    def __init__(self, comparison_type, threshold_1, threshold_2=None, name=None, description=None):
        super().__init__("自營商買賣超", "成交量", comparison_type, threshold_1, threshold_2, name, description)


# ===== Margin Trading's Movements Rules =====

class MarginTradingChangeVolumeRule(RangeRule):
    """Rule to check if margin trading change volume is within specified range."""
    
    def __init__(self, comparison_type, threshold_1, threshold_2=None, name=None, description=None):
        super().__init__("融資變化量", comparison_type, threshold_1, threshold_2, name, description)


class ShortSellingChangeVolumeRule(RangeRule):
    """Rule to check if short selling change volume is within specified range."""
    
    def __init__(self, comparison_type, threshold_1, threshold_2=None, name=None, description=None):
        super().__init__("融券變化量", comparison_type, threshold_1, threshold_2, name, description)


class MarginTradingChangeRatioRule(RatioRangeRule):
    """Rule to check if margin trading change ratio is within specified range."""
    
    def __init__(self, comparison_type, threshold_1, threshold_2=None, name=None, description=None):
        super().__init__("融資變化量", "成交量", comparison_type, threshold_1, threshold_2, name, description)


class ShortSellingChangeRatioRule(RatioRangeRule):
    """Rule to check if short selling change ratio is within specified range."""
    
    def __init__(self, comparison_type, threshold_1, threshold_2=None, name=None, description=None):
        super().__init__("融券變化量", "成交量", comparison_type, threshold_1, threshold_2, name, description)


class ShortToMarginRatioRule(RangeRule):
    """Rule to check if short-to-margin ratio is within specified threshold."""
    
    def __init__(self, comparison_type, threshold_1, threshold_2=None, name=None, description=None):
        super().__init__("券資比(%)", comparison_type, threshold_1, threshold_2, name, description)
