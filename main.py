from app import app  # noqa: F401

# Start real-time conversation manager
try:
    from realtime_conversation import realtime_manager
    realtime_manager.start()
    print("Real-time conversation manager started successfully")
except Exception as e:
    print(f"Failed to start real-time conversation manager: {e}")

# Background services are now handled in app initialization
