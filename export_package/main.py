from app import app  # noqa: F401
import threading
import time
import logging

# Start background keepalive service
def start_keepalive_service():
    """Start the background keepalive service"""
    import keepalive
    keepalive.main()

# Start keepalive in background thread
keepalive_thread = threading.Thread(target=start_keepalive_service, daemon=True)
keepalive_thread.start()
logging.info("Background keepalive service started")
