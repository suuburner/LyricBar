import logging
import os
import platform
import subprocess
import sys
from typing import List


logger = logging.getLogger(__name__)


def detect_gpu_info() -> List[str]:
    """Return a best-effort list of detected GPU names.

    The previous implementation relied on ``wmic`` and ``tasklist`` commands,
    which are not available or reliable on some Windows setups. This version
    falls back gracefully and avoids raising noisy startup warnings.
    """
    if platform.system() != "Windows":
        return []

    results: List[str] = []
    commands = [
        (["wmic", "path", "win32_VideoController", "get", "name"], "wmic"),
        (["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"], "powershell"),
    ]

    for command, tool_name in commands:
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except (FileNotFoundError, OSError):
            continue
        except Exception:
            continue

        if completed.returncode != 0:
            continue

        for line in completed.stdout.splitlines():
            cleaned = line.strip()
            if not cleaned or cleaned.lower() == "name":
                continue
            if cleaned not in results:
                results.append(cleaned)

        if results:
            return results

    return results


def log_gpu_status() -> None:
    """Log detected GPU info without failing startup when detection tools are missing."""
    try:
        gpus = detect_gpu_info()
    except Exception as exc:  # pragma: no cover - safety net for odd environments
        logger.info("ℹ️  GPU detection failed: %s", exc)
        return

    if not gpus:
        logger.info("ℹ️  No GPU information detected; relying on the default renderer")
        return

    for gpu in gpus:
        logger.info("🎮 Detected GPU: %s", gpu)
        lowered = gpu.lower()
        if "nvidia" in lowered or "rtx" in lowered or "geforce" in lowered:
            logger.info("✅ NVIDIA GPU detected")
        elif "intel" in lowered:
            logger.info("ℹ️  Intel GPU detected")
        elif "amd" in lowered or "radeon" in lowered:
            logger.info("ℹ️  AMD GPU detected")
        else:
            logger.info("ℹ️  GPU detected")
