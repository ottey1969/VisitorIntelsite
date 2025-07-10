from app import app, socketio  # noqa: F401
from flask import jsonify

# NEW: Initialize the enhanced VisitorIntelSystem
try:
    from visitor_intel_backend_fix import VisitorIntelSystem
    intel_system = VisitorIntelSystem(socketio)
    
    # Add new API endpoint for the frontend to get the initial state
    @app.route('/api/v2/status')
    def get_status_v2():
        return jsonify(intel_system.get_current_state())
    
    # Start the enhanced system
    intel_system.start()
    print("Enhanced VisitorIntelSystem started successfully")
except Exception as e:
    print(f"Failed to start enhanced VisitorIntelSystem: {e}")
    # Fallback to original system
    try:
        from realtime_conversation import realtime_manager
        realtime_manager.start()
        print("Fallback: Real-time conversation manager started successfully")
    except Exception as fallback_e:
        print(f"Failed to start fallback system: {fallback_e}")

# Background services are now handled in app initialization
