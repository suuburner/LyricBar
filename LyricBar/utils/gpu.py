import logging
import platform
import subprocess
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
        ["wmic", "path", "win32_VideoController", "get", "name"],
        ["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"],
    ]

    for command in commands:
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
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


def detect_active_renderer() -> str:
    """Ask OpenGL itself which GPU it actually bound to (GL_RENDERER), rather
    than guessing. Requires a QApplication/QGuiApplication to already exist.
    Returns "" if this can't be determined (headless, driver issue, etc.) --
    callers should treat that as "unknown", not as an error.

    Windows-only: once QOpenGLContext.makeCurrent() binds a real WGL context,
    opengl32.dll's glGetString can be called directly via ctypes. This
    deliberately avoids PyQt5's QOpenGLFunctions wrapper class -- that class
    isn't bundled in every PyQt5 wheel (it wasn't present in the one this was
    tested against), whereas opengl32.dll ships with Windows itself, so this
    has one less thing to go missing.
    """
    if platform.system() != "Windows":
        return ""

    try:
        from PyQt5.QtGui import QOffscreenSurface, QOpenGLContext, QSurfaceFormat
    except Exception as exc:
        logger.debug("Active-renderer detection unavailable (PyQt5 OpenGL classes missing): %s", exc)
        return ""

    import ctypes

    GL_RENDERER = 0x1F01

    try:
        surface = QOffscreenSurface()
        surface.setFormat(QSurfaceFormat.defaultFormat())
        surface.create()
        if not surface.isValid():
            logger.debug("Active-renderer detection: offscreen surface failed to become valid")
            return ""

        ctx = QOpenGLContext()
        if not ctx.create():
            logger.debug("Active-renderer detection: QOpenGLContext.create() failed")
            return ""
        if not ctx.makeCurrent(surface):
            logger.debug("Active-renderer detection: makeCurrent() failed")
            return ""

        try:
            opengl32 = ctypes.windll.opengl32
            opengl32.glGetString.restype = ctypes.c_char_p
            opengl32.glGetString.argtypes = [ctypes.c_uint]
            renderer_bytes = opengl32.glGetString(GL_RENDERER)
        finally:
            ctx.doneCurrent()

        if not renderer_bytes:
            return ""
        return renderer_bytes.decode(errors="replace")
    except Exception as exc:
        logger.debug("Active-renderer detection failed: %s", exc)
        return ""


def _match_active_gpu(gpus: List[str], renderer: str):
    """Match the GL_RENDERER string against the list of GPU names from
    detect_gpu_info(). The two rarely match verbatim (e.g. renderer might be
    "NVIDIA GeForce RTX 4050 Laptop GPU/PCIe/SSE2" vs the driver-reported
    "NVIDIA GeForce RTX 4050 Laptop GPU"), so this checks substrings in
    either direction rather than requiring an exact match."""
    if not renderer:
        return None
    renderer_lower = renderer.lower()
    for gpu in gpus:
        gpu_lower = gpu.lower()
        if gpu_lower in renderer_lower or renderer_lower in gpu_lower:
            return gpu
    return None


def log_gpu_status() -> None:
    """Log detected GPU info without failing startup when detection tools are missing."""
    try:
        gpus = detect_gpu_info()
    except Exception as exc:  # pragma: no cover - safety net for odd environments
        logger.debug("GPU detection failed: %s", exc)
        return

    if not gpus:
        logger.debug("No GPU information detected; relying on the default renderer")
        return

    renderer = detect_active_renderer()
    active = _match_active_gpu(gpus, renderer)

    if active:
        labeled = [f"{gpu} \u2713 (active)" if gpu == active else gpu for gpu in gpus]
        logger.info("GPU(s) detected: %s", ", ".join(labeled))
    elif renderer:
        # We got a renderer string but couldn't tie it back to one of the
        # listed adapter names -- show it raw instead of silently guessing.
        logger.info("GPU(s) detected: %s (renderer in use: %s)", ", ".join(gpus), renderer)
    else:
        # Couldn't determine the active one at all -- say so explicitly
        # rather than printing a plain list that looks like it picked one.
        logger.info("GPU(s) detected: %s (active GPU could not be determined)", ", ".join(gpus))