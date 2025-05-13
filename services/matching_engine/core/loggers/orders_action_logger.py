import logging
import os
from core.config import settings

log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

file_handler = logging.FileHandler(f"{log_dir}/orders.log", encoding="utf-8")
file_handler.setFormatter(logging.Formatter('%(message)s'))

logger = logging.getLogger("orders_logger")
logger.setLevel(settings.LOG_LEVEL)
logger.propagate = False

logger.addHandler(file_handler)