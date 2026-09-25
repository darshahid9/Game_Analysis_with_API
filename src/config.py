import os
from dotenv import load_dotenv

load_dotenv()

SPORTRADAR_API_KEY = os.getenv("SPORTRADAR_API_KEY", "")

# Trial keys use the "trial" access level; paid keys use "production".
SPORTRADAR_ACCESS_LEVEL = os.getenv("SPORTRADAR_ACCESS_LEVEL", "trial")
SPORTRADAR_BASE_URL = f"https://api.sportradar.com/tennis/{SPORTRADAR_ACCESS_LEVEL}/v3/en"

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "tennis_analytics"),
}

# Trial keys are rate-limited to 1 request/second.
REQUEST_DELAY_SECONDS = float(os.getenv("REQUEST_DELAY_SECONDS", 1.1))
