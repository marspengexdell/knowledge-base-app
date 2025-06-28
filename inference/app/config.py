import os

MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))
EARLY_STOP_TOKENS = [t for t in os.getenv("EARLY_STOP_TOKENS", "").split(',') if t]
USE_KV_CACHE = os.getenv("USE_KV_CACHE", "1").lower() not in ("0", "false", "no")
