# Standard library imports
import logging

def setup_logger(level=logging.INFO):
    logging.basicConfig(
        format="[%(asctime)s] [%(process)d] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S %z",
        level=level,
    )
    return logging.getLogger()
