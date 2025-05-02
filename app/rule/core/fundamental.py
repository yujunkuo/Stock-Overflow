"""
Fundamental Analysis Rules

This module provides fundamental analysis rules for stock screening.
"""

# Local imports
from app.rule.common.base import RangeRule


# ===== Fundamental Rules =====

class PerRule(RangeRule):
    """Rule to check if PE Ratio is within specified range."""
    
    def __init__(self, comparison_type, threshold_1, threshold_2=None, name=None, description=None):
        super().__init__("本益比", comparison_type, threshold_1, threshold_2, name, description)


class PbrRule(RangeRule):
    """Rule to check if PB Ratio is within specified range."""
    
    def __init__(self, comparison_type, threshold_1, threshold_2=None, name=None, description=None):
        super().__init__("股價淨值比", comparison_type, threshold_1, threshold_2, name, description)


class DividendYieldRule(RangeRule):
    """Rule to check if Dividend Yield is within specified range."""
    
    def __init__(self, comparison_type, threshold_1, threshold_2=None, name=None, description=None):
        super().__init__("殖利率(%)", comparison_type, threshold_1, threshold_2, name, description)


class MomRule(RangeRule):
    """Rule to check if MoM Revenue Growth Rate is within specified range."""
    
    def __init__(self, comparison_type, threshold_1, threshold_2=None, name=None, description=None):
        super().__init__("(月)營收月增率(%)", comparison_type, threshold_1, threshold_2, name, description)


class YoyRule(RangeRule):
    """Rule to check if YoY Revenue Growth Rate is within specified range."""
    
    def __init__(self, comparison_type, threshold_1, threshold_2=None, name=None, description=None):
        super().__init__("(月)營收年增率(%)", comparison_type, threshold_1, threshold_2, name, description)


class AccYoyRule(RangeRule):
    """Rule to check if Acc-YoY Revenue Growth Rate is within specified range."""
    
    def __init__(self, comparison_type, threshold_1, threshold_2=None, name=None, description=None):
        super().__init__("(月)累積營收年增率(%)", comparison_type, threshold_1, threshold_2, name, description)
