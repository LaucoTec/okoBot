import logging
import logging.handlers
from pathlib import Path

# Create logs directory if it doesn't exist
log_dir = Path(__file__).parent.parent / "files"
log_dir.mkdir(exist_ok=True)

# Configure logger for database operations
logger = logging.getLogger("okoBot.db")
logger.setLevel(logging.INFO)

# File handler with rotation (5MB per file, keep 5 backups)
file_handler = logging.handlers.RotatingFileHandler(
    log_dir / "database.log",
    maxBytes=5 * 1024 * 1024,  # 5MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(logging.DEBUG)

# Console handler (only show WARNING and above)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)

# Formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to logger
if not logger.handlers:
    logger.propagate = False
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
