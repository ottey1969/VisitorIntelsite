#!/usr/bin/env python3
"""
Enhanced Visitor Intel 4-API Conversation System
===============================================

Real-time AI conversation system using 4 APIs:
- OpenAI GPT-4o
- Anthropic Claude Sonnet 4  
- Perplexity AI
- Google Gemini

Features:
- 30-minute conversation rounds (16 messages per round)
- Countdown timer between conversations
- Unpredictable 1-2 minute message intervals
- Real-time WebSocket updates
- Professional user experience
- Robust error handling and fallbacks
"""

import os
import sys
import time
import json
import sqlite3
import logging
import threading
import asyncio
from datetime import datetime, timedelta
import random
from typing import Dict, List, Optional, Tuple
import pytz
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import schedule
import requests
from models import Business, Conversation, ConversationMessage, db
from app import app
from geo_language_detector import GeoLanguageDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Enhanced4APIConversationSystem:
    """Enhanced conversation system with 4 AI APIs and countdown timers"""
    
    def __init__(self):
        self.running = False
        self.current_conversation_id = None
        self.conversation_state = "waiting"  # waiting, active, completed
        self.next_conversation_time = None
        self.message_queue = []
        self.socketio = None
        self.geo_detector = GeoLanguageDetector()
        
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
                'model': 'gpt-4o',
                'role': 'Business strategy and operations expert'
            },
            {
                'name': 'SEO AI Specialist', 
                'provider': 'anthropic',
                'model': 'claude-sonnet-4-20250514',
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
                'model': 'gemini-2.5-flash',
                'role': 'Marketing and brand positioning specialist'
            }
        ]
        
        # Conversation Topics
        self.conversation_topics = [
            "Professional Service Excellence and Quality Standards",
            "Customer Experience and Satisfaction Strategies", 
            "Digital Marketing and Online Presence",
            "Industry Expertise and Technical Knowledge",
            "Local Community Engagement and Trust Building",
            "Emergency Response and Reliability",
            "Innovation and Modern Technology Integration",
            "Cost-Effective Solutions and Value Proposition",
            "Licensing, Insurance, and Professional Credentials",
            "Environmental Responsibility and Sustainability"
        ]
        
        # Schedule next conversation
        self.schedule_next_conversation()
        
    def get_user_timezone(self, request_ip=None):
        """Get user's timezone based on IP or default to system timezone"""
        try:
            if request_ip:
                country_code = self.geo_detector.detect_country_from_ip(request_ip)
                if country_code:
                    config = self.geo_detector.get_localized_config(country_code)
                    return pytz.timezone(config.get('timezone', 'UTC'))
            
            # Fallback to system timezone
            return pytz.timezone('UTC')
        except:
            return pytz.timezone('UTC')
            
    def convert_to_local_time(self, utc_time, user_timezone=None):
        """Convert UTC time to user's local timezone"""
        if user_timezone is None:
            user_timezone = self.get_user_timezone()
            
        if utc_time.tzinfo is None:
            utc_time = pytz.UTC.localize(utc_time)
        elif utc_time.tzinfo != pytz.UTC:
            utc_time = utc_time.astimezone(pytz.UTC)
            
        return utc_time.astimezone(user_timezone)
        
    def setup_socketio(self, socketio):
        """Setup SocketIO for real-time updates"""
        self.socketio = socketio
        
    def start_system(self):
        """Start the enhanced conversation system"""
        if self.running:
            return
            
        self.running = True
        logging.info("Enhanced 4-API Conversation System started")
        
        # Start background scheduler thread
        scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        scheduler_thread.start()
        
        # Start countdown update thread
        countdown_thread = threading.Thread(target=self._update_countdown, daemon=True)
        countdown_thread.start()
        
    def stop_system(self):
        """Stop the enhanced conversation system"""
        self.running = False
        logging.info("Enhanced 4-API Conversation System stopped")
        
    def _run_scheduler(self):
        """Background scheduler for conversations"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(10)  # Check every 10 seconds
            except Exception as e:
                logging.error(f"Scheduler error: {e}")
                time.sleep(30)
                
    def _update_countdown(self):
        """Update countdown timer every second"""
        while self.running:
            try:
                if self.conversation_state == "waiting" and self.next_conversation_time:
                    remaining = self.next_conversation_time - datetime.now()
                    if remaining.total_seconds() > 0:
                        countdown_data = {
                            'state': 'waiting',
                            'remaining_seconds': int(remaining.total_seconds()),
                            'next_time': self.next_conversation_time.isoformat()
                        }
                        if self.socketio:
                            self.socketio.emit('countdown_update', countdown_data)
                    else:
                        # Time to start conversation
                        self.start_conversation()
                        
                time.sleep(1)
            except Exception as e:
                logging.error(f"Countdown update error: {e}")
                time.sleep(5)
                
    def schedule_next_conversation(self):
        """Schedule the next conversation"""
        # Schedule for exactly 30 minutes from now
        self.next_conversation_time = datetime.now() + timedelta(minutes=30)
        self.conversation_state = "waiting"
        
        logging.info(f"Next conversation scheduled for: {self.next_conversation_time}")
        
    def start_conversation(self):
        """Start a new conversation round"""
        try:
            self.conversation_state = "active"
            
            # Get featured business
            featured_business = Business.query.filter_by(is_featured=True).first()
            if not featured_business:
                # Fallback to Perfect Roofing Team
                featured_business = Business.query.get(5)
                
            if not featured_business:
                logging.error("No business found for conversation")
                self.schedule_next_conversation()
                return
                
            # Select random topic
            topic = random.choice(self.conversation_topics)
            
            # Create conversation record
            with app.app_context():
                conversation = Conversation(
                    business_id=featured_business.id,
                    topic=topic,
                    created_at=datetime.now()
                )
                db.session.add(conversation)
                db.session.commit()
                
                self.current_conversation_id = conversation.id
                
            logging.info(f"Started conversation: {topic} for {featured_business.name}")
            
            # Start message generation thread
            message_thread = threading.Thread(
                target=self._generate_conversation_messages,
                args=(conversation.id, featured_business, topic),
                daemon=True
            )
            message_thread.start()
            
        except Exception as e:
            logging.error(f"Error starting conversation: {e}")
            self.schedule_next_conversation()
            
    def _generate_conversation_messages(self, conversation_id: int, business: Business, topic: str):
        """Generate 16 messages for the conversation"""
        try:
            with app.app_context():
                conversation = Conversation.query.get(conversation_id)
                if not conversation:
                    return
                    
                # Generate 4 rounds of 4 messages each
                for round_num in range(1, 5):
                    for agent_idx, agent in enumerate(self.ai_agents):
                        try:
                            # Wait random interval between messages (1-2 minutes)
                            if round_num > 1 or agent_idx > 0:  # Don't wait for first message
                                wait_time = random.uniform(60, 120)  # 1-2 minutes
                                time.sleep(wait_time)
                                
                            # Generate message
                            message_content = self._generate_ai_message(
                                agent, business, topic, conversation, round_num
                            )
                            
                            # Save message to database
                            message = ConversationMessage(
                                conversation_id=conversation_id,
                                agent_name=agent['name'],
                                agent_type=agent['provider'],
                                message_content=message_content,
                                created_at=datetime.now()
                            )
                            db.session.add(message)
                            db.session.commit()
                            
                            # Broadcast message via WebSocket
                            if self.socketio:
                                self.socketio.emit('new_message', {
                                    'agent_name': agent['name'],
                                    'agent_type': agent['provider'],
                                    'message': message_content,
                                    'timestamp': datetime.now().isoformat(),
                                    'conversation_id': conversation_id
                                })
                                
                            logging.info(f"Generated message from {agent['name']}")
                            
                        except Exception as e:
                            logging.error(f"Error generating message from {agent['name']}: {e}")
                            # Use fallback message
                            fallback_message = self._get_fallback_message(agent, topic)
                            message = ConversationMessage(
                                conversation_id=conversation_id,
                                agent_name=agent['name'],
                                agent_type=agent['provider'],
                                message_content=fallback_message,
                                created_at=datetime.now()
                            )
                            db.session.add(message)
                            db.session.commit()
                            
                # Mark conversation as completed
                conversation.completed_at = datetime.now()
                db.session.commit()
                
                self.conversation_state = "completed"
                logging.info(f"Completed conversation: {topic}")
                
                # Schedule next conversation
                self.schedule_next_conversation()
                
        except Exception as e:
            logging.error(f"Error in conversation generation: {e}")
            self.schedule_next_conversation()
            
    def _generate_ai_message(self, agent: dict, business: Business, topic: str, 
                           conversation: Conversation, round_num: int) -> str:
        """Generate a message from an AI agent"""
        
        # Build context from previous messages
        previous_messages = ConversationMessage.query.filter_by(
            conversation_id=conversation.id
        ).order_by(ConversationMessage.created_at).all()
        
        context = f"Business: {business.name}\nIndustry: {business.industry}\nLocation: {business.location}\n"
        context += f"Topic: {topic}\nRound: {round_num}\n\n"
        
        if previous_messages:
            context += "Previous conversation:\n"
            for msg in previous_messages[-6:]:  # Last 6 messages for context
                context += f"{msg.agent_name}: {msg.message_content}\n\n"
                
        # Generate based on provider
        try:
            if agent['provider'] == 'openai':
                return self._call_openai_api(agent, context, topic)
            elif agent['provider'] == 'anthropic':
                return self._call_anthropic_api(agent, context, topic)
            elif agent['provider'] == 'perplexity':
                return self._call_perplexity_api(agent, context, topic)
            elif agent['provider'] == 'gemini':
                return self._call_gemini_api(agent, context, topic)
            else:
                return self._get_fallback_message(agent, topic)
                
        except Exception as e:
            logging.error(f"API call failed for {agent['provider']}: {e}")
            return self._get_fallback_message(agent, topic)
            
    def _call_openai_api(self, agent: dict, context: str, topic: str) -> str:
        """Call OpenAI API"""
        if not self.api_keys['openai']:
            raise Exception("OpenAI API key not configured")
            
        headers = {
            'Authorization': f"Bearer {self.api_keys['openai']}",
            'Content-Type': 'application/json'
        }
        
        prompt = f"""You are {agent['name']}, a {agent['role']}.
        
Context: {context}

Provide a professional, insightful response about {topic}. Keep it conversational, under 150 words, and focused on business value."""

        data = {
            'model': agent['model'],
            'messages': [
                {'role': 'system', 'content': f"You are {agent['name']}, a {agent['role']}."},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 200,
            'temperature': 0.7
        }
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        else:
            raise Exception(f"OpenAI API error: {response.status_code}")
            
    def _call_anthropic_api(self, agent: dict, context: str, topic: str) -> str:
        """Call Anthropic API"""
        if not self.api_keys['anthropic']:
            raise Exception("Anthropic API key not configured")
            
        headers = {
            'x-api-key': self.api_keys['anthropic'],
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        
        prompt = f"""You are {agent['name']}, a {agent['role']}.
        
Context: {context}

Provide a professional, insightful response about {topic}. Keep it conversational, under 150 words, and focused on business value."""

        data = {
            'model': agent['model'],
            'max_tokens': 200,
            'messages': [
                {'role': 'user', 'content': prompt}
            ]
        }
        
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['content'][0]['text'].strip()
        else:
            raise Exception(f"Anthropic API error: {response.status_code}")
            
    def _call_perplexity_api(self, agent: dict, context: str, topic: str) -> str:
        """Call Perplexity API"""
        if not self.api_keys['perplexity']:
            raise Exception("Perplexity API key not configured")
            
        headers = {
            'Authorization': f"Bearer {self.api_keys['perplexity']}",
            'Content-Type': 'application/json'
        }
        
        prompt = f"""You are {agent['name']}, a {agent['role']}.
        
Context: {context}

Provide a professional, insightful response about {topic}. Keep it conversational, under 150 words, and focused on business value."""

        data = {
            'model': agent['model'],
            'messages': [
                {'role': 'system', 'content': f"You are {agent['name']}, a {agent['role']}."},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 200,
            'temperature': 0.7
        }
        
        response = requests.post(
            'https://api.perplexity.ai/chat/completions',
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        else:
            raise Exception(f"Perplexity API error: {response.status_code}")
            
    def _call_gemini_api(self, agent: dict, context: str, topic: str) -> str:
        """Call Gemini API"""
        if not self.api_keys['gemini']:
            raise Exception("Gemini API key not configured")
            
        headers = {
            'Content-Type': 'application/json'
        }
        
        prompt = f"""You are {agent['name']}, a {agent['role']}.
        
Context: {context}

Provide a professional, insightful response about {topic}. Keep it conversational, under 150 words, and focused on business value."""

        data = {
            'contents': [
                {
                    'parts': [
                        {'text': prompt}
                    ]
                }
            ],
            'generationConfig': {
                'maxOutputTokens': 200,
                'temperature': 0.7
            }
        }
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{agent['model']}:generateContent?key={self.api_keys['gemini']}"
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and result['candidates']:
                content = result['candidates'][0]['content']['parts'][0]['text']
                return content.strip()
            else:
                raise Exception("No content in Gemini response")
        else:
            raise Exception(f"Gemini API error: {response.status_code}")
            
    def _get_fallback_message(self, agent: dict, topic: str) -> str:
        """Generate fallback message when API fails"""
        fallback_messages = {
            'Business AI Assistant': [
                f"From a business perspective, {topic.lower()} represents a crucial opportunity for growth and competitive advantage.",
                f"Strategic implementation of {topic.lower()} can significantly impact operational efficiency and customer satisfaction.",
                f"The key to successful {topic.lower()} lies in understanding market dynamics and customer needs."
            ],
            'SEO AI Specialist': [
                f"For optimal SEO results, {topic.lower()} should be integrated into your content strategy and local search optimization.",
                f"Search engines highly value businesses that demonstrate expertise in {topic.lower()} through quality content.",
                f"Local SEO benefits tremendously when businesses showcase their capabilities in {topic.lower()}."
            ],
            'Customer Service AI': [
                f"Customers consistently appreciate transparency and expertise when it comes to {topic.lower()}.",
                f"Effective communication about {topic.lower()} builds trust and long-term customer relationships.",
                f"The customer experience is enhanced when businesses proactively address {topic.lower()}."
            ],
            'Marketing AI Expert': [
                f"Marketing {topic.lower()} effectively requires authentic storytelling and demonstrated results.",
                f"Brand positioning around {topic.lower()} creates differentiation in competitive markets.",
                f"Content marketing focused on {topic.lower()} drives engagement and qualified leads."
            ]
        }
        
        messages = fallback_messages.get(agent['name'], [
            f"This is an important aspect of {topic.lower()} that deserves careful consideration.",
            f"Industry best practices for {topic.lower()} continue to evolve with market demands.",
            f"Professional expertise in {topic.lower()} delivers measurable business value."
        ])
        
        return random.choice(messages)
        
    def get_system_status(self) -> dict:
        """Get current system status"""
        return {
            'running': self.running,
            'state': self.conversation_state,
            'current_conversation_id': self.current_conversation_id,
            'next_conversation_time': self.next_conversation_time.isoformat() if self.next_conversation_time else None,
            'api_keys_configured': {
                'openai': bool(self.api_keys['openai']),
                'anthropic': bool(self.api_keys['anthropic']),
                'perplexity': bool(self.api_keys['perplexity']),
                'gemini': bool(self.api_keys['gemini'])
            }
        }
        
    def get_countdown_info(self, request_ip=None) -> dict:
        """Get countdown information with local timezone conversion"""
        if not self.next_conversation_time:
            return {'error': 'No conversation scheduled'}
            
        # Get user timezone
        user_timezone = self.get_user_timezone(request_ip)
        
        # Convert to local time
        local_next_time = self.convert_to_local_time(self.next_conversation_time, user_timezone)
        
        # Calculate remaining time
        now_utc = datetime.now()
        remaining = self.next_conversation_time - now_utc
        
        return {
            'state': self.conversation_state,
            'remaining_seconds': max(0, int(remaining.total_seconds())),
            'next_time_utc': self.next_conversation_time.isoformat(),
            'next_time_local': local_next_time.isoformat(),
            'formatted_time_local': local_next_time.strftime('%H:%M:%S'),
            'timezone': str(user_timezone),
            'timezone_offset': local_next_time.strftime('%z')
        }

# Global system instance
enhanced_system = Enhanced4APIConversationSystem()

def start_enhanced_system():
    """Start the enhanced conversation system"""
    enhanced_system.start_system()
    return enhanced_system

def get_enhanced_status():
    """Get system status"""
    return enhanced_system.get_system_status()

def get_countdown_info():
    """Get countdown information"""
    return enhanced_system.get_countdown_info()

def setup_enhanced_socketio(socketio):
    """Setup SocketIO for the enhanced system"""
    enhanced_system.setup_socketio(socketio)