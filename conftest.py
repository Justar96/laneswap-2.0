"""
Configure test environment.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set default environment variables if not already set
os.environ.setdefault("MONGODB_URI", os.getenv("LANESWAP_MONGODB_URI", ""))
os.environ.setdefault("MONGODB_NAME", os.getenv("LANESWAP_MONGODB_NAME", ""))
os.environ.setdefault("DISCORD_WEBHOOK_URL", os.getenv("LANESWAP_DISCORD_WEBHOOK", ""))
os.environ.setdefault("CHECK_INTERVAL", os.getenv("LANESWAP_CHECK_INTERVAL", "30"))
os.environ.setdefault("STALE_THRESHOLD", os.getenv("LANESWAP_STALE_THRESHOLD", "60")) 