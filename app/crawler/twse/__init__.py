"""
TWSE (Taiwan Stock Exchange) data crawler module.

This module provides functionality to fetch and process data from the Taiwan Stock Exchange.
It handles various types of data including price, fundamental, margin trading, and institutional data.

Main functions:
    get_twse_data: Fetch, process and aggregate all TWSE data for a given date
"""

from .twse import get_twse_data

__all__ = ["get_twse_data"]