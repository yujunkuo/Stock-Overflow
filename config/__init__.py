import logging

from dotenv import load_dotenv
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
