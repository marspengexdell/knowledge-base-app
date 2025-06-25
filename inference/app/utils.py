import subprocess
import logging

logger = logging.getLogger(__name__)


def detect_gpu_presence() -> bool:
    """Return True if a NVIDIA GPU is available."""
    try:
        subprocess.run(
            ["nvidia-smi"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        return True
    except Exception:
        return False


IS_GPU_AVAILABLE = detect_gpu_presence()
if IS_GPU_AVAILABLE:
    logger.info("GPU detected via nvidia-smi")
else:
    logger.info("nvidia-smi not found or GPU unavailable; using CPU")
