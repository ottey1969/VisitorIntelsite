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
        # Create a conversation for Perfect Roofing Team to keep content fresh
        topics = [
            "Emergency Roof Repair Services in New Jersey",
            "Professional Roofing Installation and Quality Materials", 
            "Customer Satisfaction and Transparent Pricing",
            "Storm Damage Restoration and Insurance Claims",
            "Roof Maintenance and Inspection Services",
            "Licensed Contractors and Industry Certifications"
        ]
        
        import random
        topic = random.choice(topics)
        
        response = requests.post('http://localhost:5000/start-conversation', 
                               data={
                                   'business_id': 1,  # Perfect Roofing Team ID
                                   'topic': topic
                               },
                               timeout=30)
        
        if response.status_code == 200:
            logging.info(f"Generated new conversation: {topic}")
            return True
        else:
            logging.warning(f"Failed to generate conversation: {response.status_code}")
            return False
            
    except Exception as e:
        logging.error(f"Conversation generation failed: {e}")
        return False

def main():
    """Main keepalive loop"""
    logging.info("Starting AI Conversation Platform keepalive monitor...")
    
    conversation_interval = 3600  # Generate new conversation every hour
    health_check_interval = 300   # Health check every 5 minutes
    
    last_conversation = 0
    last_health_check = 0
    
    while True:
        current_time = time.time()
        
        # Health check
        if current_time - last_health_check >= health_check_interval:
            if check_server_health():
                last_health_check = current_time
            else:
                logging.error("Server health check failed - manual intervention may be needed")
                time.sleep(60)  # Wait before retrying
                continue
        
        # Generate new conversation
        if current_time - last_conversation >= conversation_interval:
            if generate_conversation():
                last_conversation = current_time
            else:
                logging.warning("Failed to generate conversation - will retry")
        
        # Wait before next check
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main()