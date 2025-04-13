from .util import fetch_economic_calendar, parse_events_from_calendar

# (Public) Get the economic events from Investing.com calendar
def get_economic_events(date_from: str, date_to: str) -> list:
    # Fetch the economic calendar data
    economic_calendar = fetch_economic_calendar(date_from, date_to)
    if not economic_calendar:
        return []
    # Parse the events from the fetched data
    events = parse_events_from_calendar(economic_calendar)
    return events
