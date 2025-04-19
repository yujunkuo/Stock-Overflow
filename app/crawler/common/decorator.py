# Standard library imports
import datetime
import functools
import time

# Local imports
from config import logger


def retry_on_failure(max_retries=3, delay=3, fallback=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except:
                    if attempt < max_retries - 1:
                        time.sleep(delay)
            if fallback:
                return fallback(*args, **kwargs)
            return None
        return wrapper
    return decorator


def log_execution_time(log_message=None):
    """
    Decorator to log the execution time of a function.
    
    Args:
        log_message: Optional custom message to log. If not provided, will use the function name.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            time_spent = end_time - start_time
            
            message = log_message if log_message else f"{func.__name__} execution time"
            logger.info(f"{message}: {datetime.timedelta(seconds=int(time_spent))}")
            
            return result
        return wrapper
    return decorator