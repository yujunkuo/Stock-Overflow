# Third-party imports
from dotenv import load_dotenv

# Local imports
from app.core.config import BasicConfig
from app.core.logger import setup_logger

# Load environment variables
load_dotenv()

# Load config
config = BasicConfig()

# Set up logger
logger = setup_logger()
