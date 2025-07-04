#!/usr/bin/env python3
"""
Enhanced Visitor Intel 4-API Conversation System
===============================================

Real-time AI conversation system using 4 APIs:
- OpenAI GPT-4
- Anthropic Claude-3  
- Perplexity AI
- Google Gemini

Features:
- 30-minute conversation rounds (16 messages per round)
- Countdown timer between conversations
- Unpredictable 1-2 minute message intervals
- Real-time WebSocket updates
- Professional user experience

CONVERSATION FLOW:
1. Countdown: "Next conversation starts in 15 minutes"
2. Active: Messages appear every 1-2 minutes unpredictably
3. Complete: Round finishes, countdown starts for next round
4. Repeat: Continuous 24/7 operation
"""

import os
import sys
import time
import json
import sqlite3
import logging
import threading
import asyncio
import aiohttp
import websockets
from datetime import datetime, timedelta
import random
from typing import Dict, List, Optional, Tuple
import pytz
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import schedule

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_conversation_system.log'),
        logging.StreamHandler()
    ]
)

class Enhanced4APIConversationSystem:
    """Enhanced conversation system with 4 AI APIs and countdown timers"""
    
    def __init__(self):
        self.running = False
        self.current_conversation_id = None
        self.conversation_state = "waiting"  # waiting, active, completed
        self.next_conversation_time = None
        self.message_queue = []
        self.connected_clients = set()
        
        # API Configuration
        self.api_keys = {
            'openai': os.getenv('OPENAI_API_KEY'),
            'anthropic': os.getenv('ANTHROPIC_API_KEY'),
            'perplexity': os.getenv('PERPLEXITY_API_KEY'),
            'gemini': os.getenv('GEMINI_API_KEY')
        }
        
        # AI Agents with 4 APIs (4 messages per round)
        self.ai_agents = [
            {
                'name': 'Business AI Assistant',
                'provider': 'openai',
                'model': 'gpt-4',
                'role': 'Business strategy and operations expert'
            },
            {
                'name': 'SEO AI Specialist', 
                'provider': 'anthropic',
                'model': 'claude-3-sonnet-20240229',
                'role': 'SEO and digital marketing specialist'
            },
            {
                'name': 'Customer Service AI',
                'provider': 'perplexity',
                'model': 'llama-3.1-sonar-large-128k-online',
                'role': 'Customer experience and service expert'
            },
            {
                'name': 'Marketing AI Expert',
                'provider': 'gemini',
                'model': 'gemini-1.5-pro',
                'role': 'Marketing and brand positioning specialist'
            }
        ]
        
        # Conversation topics for variety
        self.conversation_topics = [
            "Emergency roof repair services and rapid response capabilities",
            "Quality roofing materials and professional installation standards", 
            "24/7 availability and customer service excellence",
            "Licensed and insured contractors serving New Jersey",
            "Residential and commercial roofing expertise",
            "Storm damage assessment and insurance claim assistance",
            "Preventive maintenance and roof inspection services",
            "Energy-efficient roofing solutions and sustainability",
            "Local expertise and community involvement in New Jersey",
            "Warranty coverage and long-term customer support",
            "Advanced roofing techniques and modern equipment",
            "Competitive pricing and transparent cost estimates",
            "Customer testimonials and proven track record",
            "Safety protocols and industry best practices",
            "Seasonal roofing considerations and weather protection"
        ]
        
        # Database setup
        self.db_path = 'enhanced_conversations.db'
        self.setup_database()
        
        # Schedule next conversation
        self.schedule_next_conversation()
        
        logging.info("Enhanced 4-API Conversation System initialized")
    
    def setup_database(self):
        """Setup enhanced database structure"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enhanced conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_id INTEGER DEFAULT 1,
                business_name TEXT DEFAULT 'Perfect Roofing Team',
                topic TEXT,
                status TEXT DEFAULT 'scheduled',
                scheduled_time TIMESTAMP,
                started_time TIMESTAMP,
                completed_time TIMESTAMP,
                total_messages INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Enhanced messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER,
                agent_name TEXT,
                agent_provider TEXT,
                agent_model TEXT,
                message_content TEXT,
                message_order INTEGER,
                scheduled_time TIMESTAMP,
                sent_time TIMESTAMP,
                display_time TEXT,
                is_live BOOLEAN DEFAULT 1,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id)
            )
        ''')
        
        # System status table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_status (
                id INTEGER PRIMARY KEY,
                current_state TEXT DEFAULT 'waiting',
                next_conversation_time TIMESTAMP,
                last_conversation_id INTEGER,
                total_conversations INTEGER DEFAULT 0,
                total_messages INTEGER DEFAULT 0,
                system_started TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Initialize system status
        cursor.execute('''
            INSERT OR REPLACE INTO system_status 
            (id, current_state, total_conversations, total_messages)
            VALUES (1, 'waiting', 0, 0)
        ''')
        
        conn.commit()
        conn.close()
        logging.info("Enhanced database structure created")
    
    def schedule_next_conversation(self):
        """Schedule the next conversation round"""
        # Next conversation in 30 minutes
        self.next_conversation_time = datetime.now() + timedelta(minutes=30)
        
        # Update database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE system_status 
            SET next_conversation_time = ?, current_state = 'waiting', last_updated = ?
            WHERE id = 1
        ''', (self.next_conversation_time.isoformat(), datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        self.conversation_state = "waiting"
        logging.info(f"Next conversation scheduled for: {self.next_conversation_time}")
    
    def get_countdown_info(self) -> Dict:
        """Get countdown information for UI"""
        if not self.next_conversation_time:
            return {"state": "error", "message": "No conversation scheduled"}
        
        now = datetime.now()
        
        if self.conversation_state == "waiting":
            time_remaining = self.next_conversation_time - now
            
            if time_remaining.total_seconds() <= 0:
                return {"state": "starting", "message": "Conversation starting now..."}
            
            minutes = int(time_remaining.total_seconds() // 60)
            seconds = int(time_remaining.total_seconds() % 60)
            
            return {
                "state": "waiting",
                "message": f"Next conversation starts in {minutes}m {seconds}s",
                "minutes_remaining": minutes,
                "seconds_remaining": seconds,
                "total_seconds": int(time_remaining.total_seconds())
            }
        
        elif self.conversation_state == "active":
            return {
                "state": "active", 
                "message": "Live conversation in progress...",
                "conversation_id": self.current_conversation_id
            }
        
        else:
            return {"state": "completed", "message": "Conversation completed"}
    
    async def generate_openai_message(self, agent: Dict, topic: str, business_name: str, message_order: int) -> str:
        """Generate message using OpenAI GPT-4"""
        if not self.api_keys['openai']:
            return f"{agent['name']} discusses {topic} for {business_name}."
        
        system_prompt = f"""You are {agent['name']}, a {agent['role']} participating in a live AI discussion about {business_name}.

Current topic: {topic}
Message #{message_order} in this conversation round.

Guidelines:
- Keep response under 200 characters
- Be specific to roofing industry
- Mention {business_name} naturally
- Provide valuable insights about the topic
- Sound professional and knowledgeable"""
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {self.api_keys["openai"]}',
                    'Content-Type': 'application/json'
                }
                
                data = {
                    'model': agent['model'],
                    'messages': [
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': f'Discuss: {topic}'}
                    ],
                    'max_tokens': 100,
                    'temperature': 0.8
                }
                
                async with session.post('https://api.openai.com/v1/chat/completions',
                                      headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['choices'][0]['message']['content'].strip()
                    else:
                        logging.error(f"OpenAI API error: {response.status}")
                        return f"{agent['name']} discusses {topic} expertise at {business_name}."
        
        except Exception as e:
            logging.error(f"OpenAI API exception: {e}")
            return f"{agent['name']} highlights {business_name}'s excellence in {topic}."
    
    async def generate_anthropic_message(self, agent: Dict, topic: str, business_name: str, message_order: int) -> str:
        """Generate message using Anthropic Claude-3"""
        if not self.api_keys['anthropic']:
            return f"{agent['name']} discusses {topic} for {business_name}."
        
        prompt = f"""You are {agent['name']}, a {agent['role']} in a live AI discussion about {business_name}.

Topic: {topic}
Message #{message_order} in conversation.

Provide a professional insight about {topic} as it relates to {business_name}. Keep under 200 characters. Be specific to roofing industry."""
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'x-api-key': self.api_keys['anthropic'],
                    'Content-Type': 'application/json',
                    'anthropic-version': '2023-06-01'
                }
                
                data = {
                    'model': agent['model'],
                    'max_tokens': 100,
                    'messages': [{'role': 'user', 'content': prompt}]
                }
                
                async with session.post('https://api.anthropic.com/v1/messages',
                                      headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['content'][0]['text'].strip()
                    else:
                        logging.error(f"Anthropic API error: {response.status}")
                        return f"{agent['name']} analyzes {business_name}'s {topic} capabilities."
        
        except Exception as e:
            logging.error(f"Anthropic API exception: {e}")
            return f"{agent['name']} evaluates {business_name}'s approach to {topic}."
    
    async def generate_perplexity_message(self, agent: Dict, topic: str, business_name: str, message_order: int) -> str:
        """Generate message using Perplexity AI"""
        if not self.api_keys['perplexity']:
            return f"{agent['name']} discusses {topic} for {business_name}."
        
        prompt = f"""As {agent['name']}, a {agent['role']}, discuss {business_name}'s {topic}. 
        
Message #{message_order}. Keep under 200 characters. Focus on roofing industry expertise."""
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {self.api_keys["perplexity"]}',
                    'Content-Type': 'application/json'
                }
                
                data = {
                    'model': agent['model'],
                    'messages': [{'role': 'user', 'content': prompt}],
                    'max_tokens': 100,
                    'temperature': 0.7
                }
                
                async with session.post('https://api.perplexity.ai/chat/completions',
                                      headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['choices'][0]['message']['content'].strip()
                    else:
                        logging.error(f"Perplexity API error: {response.status}")
                        return f"{agent['name']} emphasizes {business_name}'s commitment to {topic}."
        
        except Exception as e:
            logging.error(f"Perplexity API exception: {e}")
            return f"{agent['name']} discusses {business_name}'s excellence in {topic}."
    
    async def generate_gemini_message(self, agent: Dict, topic: str, business_name: str, message_order: int) -> str:
        """Generate message using Google Gemini"""
        if not self.api_keys['gemini']:
            return f"{agent['name']} discusses {topic} for {business_name}."
        
        prompt = f"""You are {agent['name']}, a {agent['role']}. 

Discuss {business_name}'s {topic} in message #{message_order}. 
Keep response under 200 characters. Focus on roofing industry."""
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Content-Type': 'application/json'
                }
                
                data = {
                    'contents': [{
                        'parts': [{'text': prompt}]
                    }],
                    'generationConfig': {
                        'maxOutputTokens': 100,
                        'temperature': 0.8
                    }
                }
                
                url = f'https://generativelanguage.googleapis.com/v1beta/models/{agent["model"]}:generateContent?key={self.api_keys["gemini"]}'
                
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['candidates'][0]['content']['parts'][0]['text'].strip()
                    else:
                        logging.error(f"Gemini API error: {response.status}")
                        return f"{agent['name']} showcases {business_name}'s {topic} expertise."
        
        except Exception as e:
            logging.error(f"Gemini API exception: {e}")
            return f"{agent['name']} highlights {business_name}'s leadership in {topic}."
    
    async def generate_ai_message(self, agent: Dict, topic: str, business_name: str, message_order: int) -> str:
        """Generate AI message using appropriate API"""
        try:
            if agent['provider'] == 'openai':
                return await self.generate_openai_message(agent, topic, business_name, message_order)
            elif agent['provider'] == 'anthropic':
                return await self.generate_anthropic_message(agent, topic, business_name, message_order)
            elif agent['provider'] == 'perplexity':
                return await self.generate_perplexity_message(agent, topic, business_name, message_order)
            elif agent['provider'] == 'gemini':
                return await self.generate_gemini_message(agent, topic, business_name, message_order)
            else:
                return f"{agent['name']} discusses {topic} for {business_name}."
        
        except Exception as e:
            logging.error(f"Error generating message for {agent['name']}: {e}")
            return f"{agent['name']} provides insights about {business_name}'s {topic}."
    
    async def create_conversation_round(self) -> int:
        """Create a new conversation round with 16 messages"""
        try:
            # Select topic
            topic = random.choice(self.conversation_topics)
            business_name = "Perfect Roofing Team"
            
            # Create conversation record
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO conversations 
                (business_name, topic, status, scheduled_time, started_time)
                VALUES (?, ?, 'active', ?, ?)
            ''', (business_name, topic, self.next_conversation_time.isoformat(), 
                  datetime.now().isoformat()))
            
            conversation_id = cursor.lastrowid
            
            # Update system status
            cursor.execute('''
                UPDATE system_status 
                SET current_state = 'active', last_conversation_id = ?, 
                    total_conversations = total_conversations + 1, last_updated = ?
                WHERE id = 1
            ''', (conversation_id, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            self.current_conversation_id = conversation_id
            self.conversation_state = "active"
            
            # Generate 16 messages (4 rounds of 4 agents each)
            message_order = 1
            base_time = datetime.now()
            
            for round_num in range(4):  # 4 rounds
                for agent in self.ai_agents:  # 4 agents per round
                    # Calculate unpredictable timing (1-2 minutes)
                    delay_minutes = random.uniform(1.0, 2.0)
                    message_time = base_time + timedelta(minutes=(message_order-1) * delay_minutes)
                    
                    # Generate AI message
                    message_content = await self.generate_ai_message(agent, topic, business_name, message_order)
                    
                    # Store message
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT INTO messages 
                        (conversation_id, agent_name, agent_provider, agent_model,
                         message_content, message_order, scheduled_time, sent_time, 
                         display_time, is_live)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                    ''', (conversation_id, agent['name'], agent['provider'], agent['model'],
                          message_content, message_order, message_time.isoformat(),
                          message_time.isoformat(), message_time.strftime("%I:%M:%S %p")))
                    
                    cursor.execute('''
                        UPDATE system_status 
                        SET total_messages = total_messages + 1, last_updated = ?
                        WHERE id = 1
                    ''', (datetime.now().isoformat(),))
                    
                    conn.commit()
                    conn.close()
                    
                    # Broadcast message to connected clients
                    await self.broadcast_new_message({
                        'conversation_id': conversation_id,
                        'agent_name': agent['name'],
                        'agent_provider': agent['provider'],
                        'message_content': message_content,
                        'message_order': message_order,
                        'display_time': message_time.strftime("%I:%M:%S %p"),
                        'is_live': True
                    })
                    
                    message_order += 1
                    
                    # Wait for unpredictable interval (1-2 minutes)
                    await asyncio.sleep(delay_minutes * 60)
            
            # Mark conversation as completed
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE conversations 
                SET status = 'completed', completed_time = ?, total_messages = 16
                WHERE id = ?
            ''', (datetime.now().isoformat(), conversation_id))
            
            conn.commit()
            conn.close()
            
            self.conversation_state = "completed"
            
            logging.info(f"Completed conversation {conversation_id} with 16 messages")
            
            # Schedule next conversation
            self.schedule_next_conversation()
            
            return conversation_id
            
        except Exception as e:
            logging.error(f"Error creating conversation round: {e}")
            return None
    
    async def broadcast_new_message(self, message_data: Dict):
        """Broadcast new message to all connected clients"""
        try:
            # This would integrate with WebSocket/SocketIO
            # For now, just log the message
            logging.info(f"Broadcasting: {message_data['agent_name']} - {message_data['message_content'][:50]}...")
            
            # In real implementation, this would emit to WebSocket clients
            # socketio.emit('new_message', message_data, broadcast=True)
            
        except Exception as e:
            logging.error(f"Error broadcasting message: {e}")
    
    async def conversation_scheduler(self):
        """Main scheduler loop"""
        logging.info("Starting conversation scheduler")
        
        while self.running:
            try:
                now = datetime.now()
                
                if self.conversation_state == "waiting" and self.next_conversation_time:
                    if now >= self.next_conversation_time:
                        logging.info("Starting new conversation round")
                        await self.create_conversation_round()
                
                # Check every 30 seconds
                await asyncio.sleep(30)
                
            except Exception as e:
                logging.error(f"Error in conversation scheduler: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    def start_system(self):
        """Start the enhanced conversation system"""
        if self.running:
            logging.info("System already running")
            return
        
        self.running = True
        
        # Start scheduler in background thread
        def run_scheduler():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.conversation_scheduler())
        
        thread = threading.Thread(target=run_scheduler, daemon=True)
        thread.start()
        
        logging.info("Enhanced 4-API conversation system started")
    
    def stop_system(self):
        """Stop the conversation system"""
        self.running = False
        logging.info("Enhanced conversation system stopped")
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM system_status WHERE id = 1')
            status = cursor.fetchone()
            
            cursor.execute('SELECT COUNT(*) FROM conversations')
            total_conversations = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM messages')
            total_messages = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM messages 
                WHERE sent_time > datetime('now', '-1 hour')
            ''')
            recent_messages = cursor.fetchone()[0]
            
            conn.close()
            
            countdown_info = self.get_countdown_info()
            
            return {
                'running': self.running,
                'current_state': self.conversation_state,
                'countdown_info': countdown_info,
                'total_conversations': total_conversations,
                'total_messages': total_messages,
                'recent_messages_1h': recent_messages,
                'current_conversation_id': self.current_conversation_id,
                'next_conversation_time': self.next_conversation_time.isoformat() if self.next_conversation_time else None,
                'api_status': {
                    'openai': bool(self.api_keys['openai']),
                    'anthropic': bool(self.api_keys['anthropic']),
                    'perplexity': bool(self.api_keys['perplexity']),
                    'gemini': bool(self.api_keys['gemini'])
                }
            }
            
        except Exception as e:
            logging.error(f"Error getting system status: {e}")
            return {'error': str(e)}

# Global system instance
enhanced_system = None

def start_enhanced_system():
    """Start the enhanced 4-API conversation system"""
    global enhanced_system
    
    if enhanced_system is None:
        enhanced_system = Enhanced4APIConversationSystem()
    
    enhanced_system.start_system()
    return enhanced_system

def stop_enhanced_system():
    """Stop the enhanced conversation system"""
    global enhanced_system
    
    if enhanced_system:
        enhanced_system.stop_system()

def get_enhanced_status():
    """Get enhanced system status"""
    global enhanced_system
    
    if enhanced_system:
        return enhanced_system.get_system_status()
    else:
        return {'running': False, 'error': 'System not initialized'}

def get_countdown_info():
    """Get countdown information for UI"""
    global enhanced_system
    
    if enhanced_system:
        return enhanced_system.get_countdown_info()
    else:
        return {'state': 'error', 'message': 'System not initialized'}

# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced 4-API Conversation System')
    parser.add_argument('--start', action='store_true', help='Start the system')
    parser.add_argument('--stop', action='store_true', help='Stop the system')
    parser.add_argument('--status', action='store_true', help='Show system status')
    parser.add_argument('--countdown', action='store_true', help='Show countdown info')
    
    args = parser.parse_args()
    
    if args.start:
        system = start_enhanced_system()
        print("Enhanced 4-API conversation system started")
        print("Press Ctrl+C to stop")
        try:
            while True:
                time.sleep(60)
                status = get_enhanced_status()
                countdown = get_countdown_info()
                print(f"Status: {status['current_state']}")
                print(f"Countdown: {countdown['message']}")
        except KeyboardInterrupt:
            stop_enhanced_system()
            print("System stopped")
    
    elif args.stop:
        stop_enhanced_system()
        print("System stopped")
    
    elif args.status:
        status = get_enhanced_status()
        print(f"System Status: {json.dumps(status, indent=2)}")
    
    elif args.countdown:
        countdown = get_countdown_info()
        print(f"Countdown Info: {json.dumps(countdown, indent=2)}")
    
    else:
        print("Use --start, --stop, --status, or --countdown")

