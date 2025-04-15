import time
import functools
import pandas as pd

from config import config, logger


def retry_on_failure(max_retries=3, delay=3):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            data_type = args[0] if args else kwargs.get("data_type")
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except:
                    logger.warning(f"Attempt {func.__name__} for {data_type.value} failed.")
                    if attempt < max_retries - 1:
                        time.sleep(delay)
            return pd.DataFrame(columns=config.COLUMN_KEEP_SETTING[data_type])
        return wrapper
    return decorator
