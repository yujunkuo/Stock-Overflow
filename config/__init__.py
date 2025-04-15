# Standard library imports
import logging

# Third-party imports
from dotenv import load_dotenv

# Local imports
from .config import BasicConfig

# Load envs
load_dotenv()

# Set up config
config = BasicConfig()

# Set up logger
logging.basicConfig(
    format="[%(asctime)s] [%(process)d] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S %z",
    level=logging.INFO,
)

logger = logging.getLogger()
