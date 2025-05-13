import logging
from core.config import settings 

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger("orders_service")

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)