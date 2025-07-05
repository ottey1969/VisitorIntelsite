#!/usr/bin/env python3
"""
Keep the AI conversation platform running 24/7
Monitors the server and ensures continuous operation
"""

import time
import requests
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def check_server_health():
    """Check if the server is responding"""
    try:
        response = requests.get('http://localhost:5000/api-status', timeout=10)
        if response.status_code == 200:
            data = response.json()
            logging.info(f"Server healthy - All APIs: {all(data.values())}")
            return True
        else:
            logging.warning(f"Server returned status {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"Server health check failed: {e}")
        return False

def generate_conversation():
    """Generate a new AI conversation to keep the platform active"""
    try:
        response = requests.post('http://localhost:5000/keepalive/generate', 
                               timeout=60)  # Longer timeout for AI generation
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                logging.info(f"Generated new conversation: {result.get('topic')} ({result.get('messages_count')} messages)")
                return True
            else:
                logging.warning(f"API returned error: {result.get('error', 'Unknown error')}")
                return False
        else:
            logging.warning(f"Failed to generate conversation: {response.status_code}")
            return False
            
    except Exception as e:
        logging.error(f"Conversation generation failed: {e}")
        return False

def main():
    """Main keepalive loop"""
    logging.info("Starting AI Conversation Platform keepalive monitor...")
    
    conversation_interval = 1260  # Generate new conversation every 21 minutes (16min conversation + 5min break)
    health_check_interval = 180   # Health check every 3 minutes (more frequent)
    ping_interval = 60           # Server ping every minute to prevent sleep
    
    last_conversation = 0
    last_health_check = 0
    last_ping = 0
    
    while True:
        current_time = time.time()
        
        # Keep server active with regular pings
        if current_time - last_ping >= ping_interval:
            try:
                requests.get('http://localhost:5000/', timeout=5)
                last_ping = current_time
                logging.debug("Server ping successful")
            except:
                logging.warning("Server ping failed")
        
        # Health check
        if current_time - last_health_check >= health_check_interval:
            if check_server_health():
                last_health_check = current_time
            else:
                logging.error("Server health check failed - manual intervention may be needed")
                time.sleep(30)  # Shorter wait before retrying
                continue
        
        # Generate new conversation
        if current_time - last_conversation >= conversation_interval:
            if generate_conversation():
                last_conversation = current_time
                logging.info("New conversation generated - keeping platform active")
            else:
                logging.warning("Failed to generate conversation - will retry in 5 minutes")
                last_conversation = current_time - conversation_interval + 300  # Retry in 5 minutes
        
        # Wait before next check
        time.sleep(30)  # Check every 30 seconds for better responsiveness

if __name__ == "__main__":
    main()