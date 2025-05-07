# Standard library imports
import datetime

# Convert timestamp in milliseconds to date
def convert_milliseconds_to_date(timestamp_ms: int):
    return datetime.datetime.fromtimestamp(timestamp_ms / 1000).date()