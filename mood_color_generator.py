"""
Dynamic Color Palette Generator Based on Conversation Mood
Analyzes conversation content to determine emotional tone and generates matching color palettes
"""

import re
import colorsys
from typing import Dict, List, Tuple, Optional
from models import Conversation, ConversationMessage
from app import db

class MoodColorGenerator:
    """Generates dynamic color palettes based on conversation emotional analysis"""
    
    def __init__(self):
        # Define mood keywords and their emotional weights
        self.mood_keywords = {
            'positive': {
                'excellent': 3, 'amazing': 3, 'outstanding': 3, 'fantastic': 3,
                'great': 2, 'good': 2, 'wonderful': 2, 'perfect': 2, 'successful': 2,
                'reliable': 2, 'professional': 2, 'quality': 2, 'efficient': 2,
                'helpful': 1, 'nice': 1, 'pleased': 1, 'satisfied': 1, 'happy': 1,
                'love': 2, 'recommend': 2, 'trust': 2, 'confident': 2
            },
            'energetic': {
                'exciting': 3, 'dynamic': 3, 'innovative': 3, 'cutting-edge': 3,
                'fast': 2, 'quick': 2, 'active': 2, 'vibrant': 2, 'powerful': 2,
                'strong': 2, 'advanced': 2, 'modern': 2, 'new': 1, 'fresh': 1
            },
            'calm': {
                'peaceful': 3, 'relaxing': 3, 'serene': 3, 'tranquil': 3,
                'comfortable': 2, 'gentle': 2, 'smooth': 2, 'easy': 2,
                'stable': 2, 'consistent': 2, 'secure': 2, 'safe': 2,
                'quiet': 1, 'simple': 1, 'clean': 1
            },
            'professional': {
                'business': 3, 'corporate': 3, 'enterprise': 3, 'commercial': 3,
                'industry': 2, 'service': 2, 'expert': 2, 'specialist': 2,
                'team': 2, 'company': 2, 'organization': 2, 'solution': 2,
                'experience': 1, 'skilled': 1, 'trained': 1
            },
            'urgent': {
                'emergency': 3, 'urgent': 3, 'critical': 3, 'immediate': 3,
                'important': 2, 'priority': 2, 'serious': 2, 'concern': 2,
                'problem': 2, 'issue': 2, 'repair': 2, 'fix': 2,
                'attention': 1, 'needed': 1, 'required': 1
            },
            'trustworthy': {
                'certified': 3, 'licensed': 3, 'insured': 3, 'guaranteed': 3,
                'warranty': 2, 'proven': 2, 'established': 2, 'experienced': 2,
                'dependable': 2, 'honest': 2, 'transparent': 2, 'authentic': 2,
                'verified': 1, 'approved': 1, 'authorized': 1
            }
        }
        
        # Base color palettes for different moods
        self.mood_palettes = {
            'positive': {
                'primary': (76, 175, 80),    # Green
                'secondary': (255, 193, 7),   # Amber
                'accent': (33, 150, 243),     # Blue
                'background': (248, 255, 249), # Light green
                'text': (27, 94, 32)          # Dark green
            },
            'energetic': {
                'primary': (255, 87, 34),     # Deep orange
                'secondary': (255, 152, 0),   # Orange
                'accent': (244, 67, 54),      # Red
                'background': (255, 243, 224), # Light orange
                'text': (191, 54, 12)         # Dark orange
            },
            'calm': {
                'primary': (63, 81, 181),     # Indigo
                'secondary': (121, 134, 203), # Light indigo
                'accent': (103, 58, 183),     # Deep purple
                'background': (232, 234, 246), # Very light indigo
                'text': (26, 35, 126)         # Dark indigo
            },
            'professional': {
                'primary': (55, 71, 79),      # Blue grey
                'secondary': (96, 125, 139),  # Light blue grey
                'accent': (0, 96, 100),       # Cyan
                'background': (236, 239, 241), # Very light grey
                'text': (38, 50, 56)          # Dark blue grey
            },
            'urgent': {
                'primary': (244, 67, 54),     # Red
                'secondary': (255, 152, 0),   # Orange
                'accent': (255, 193, 7),      # Amber
                'background': (255, 235, 238), # Light red
                'text': (183, 28, 28)         # Dark red
            },
            'trustworthy': {
                'primary': (33, 150, 243),    # Blue
                'secondary': (100, 181, 246), # Light blue
                'accent': (0, 150, 136),      # Teal
                'background': (227, 242, 253), # Very light blue
                'text': (13, 71, 161)         # Dark blue
            }
        }
    
    def analyze_conversation_mood(self, conversation_id: int) -> Dict[str, float]:
        """Analyze conversation content to determine emotional mood scores"""
        conversation = Conversation.query.get(conversation_id)
        if not conversation:
            return self._get_default_mood()
        
        messages = ConversationMessage.query.filter_by(conversation_id=conversation_id).all()
        if not messages:
            return self._get_default_mood()
        
        # Combine all message content
        full_text = " ".join([msg.content.lower() for msg in messages])
        full_text += f" {conversation.topic.lower()}"
        
        # Calculate mood scores
        mood_scores = {}
        for mood, keywords in self.mood_keywords.items():
            score = 0
            word_count = 0
            
            for keyword, weight in keywords.items():
                # Count occurrences with word boundaries
                matches = len(re.findall(rf'\b{re.escape(keyword)}\b', full_text))
                if matches > 0:
                    score += matches * weight
                    word_count += matches
            
            # Normalize score based on text length and word density
            text_words = len(full_text.split())
            if text_words > 0:
                mood_scores[mood] = (score / max(text_words, 1)) * 100
            else:
                mood_scores[mood] = 0
        
        # Ensure we have at least some mood
        if all(score == 0 for score in mood_scores.values()):
            return self._get_default_mood()
        
        return mood_scores
    
    def generate_color_palette(self, conversation_id: int) -> Dict[str, str]:
        """Generate a dynamic color palette based on conversation mood"""
        mood_scores = self.analyze_conversation_mood(conversation_id)
        
        # Find dominant mood
        dominant_mood = max(mood_scores.keys(), key=lambda k: mood_scores[k])
        dominant_score = mood_scores[dominant_mood]
        
        # Get base palette
        base_palette = self.mood_palettes[dominant_mood].copy()
        
        # Apply mood intensity adjustments
        intensity = min(dominant_score / 10, 1.0)  # Normalize to 0-1
        
        # Adjust colors based on intensity
        adjusted_palette = {}
        for color_name, rgb in base_palette.items():
            if color_name in ['background', 'text']:
                # Keep background and text relatively stable
                adjusted_palette[color_name] = self._rgb_to_hex(rgb)
            else:
                # Adjust saturation and brightness based on intensity
                adjusted_rgb = self._adjust_color_intensity(rgb, intensity)
                adjusted_palette[color_name] = self._rgb_to_hex(adjusted_rgb)
        
        # Add mood-specific CSS variables
        adjusted_palette['mood'] = dominant_mood
        adjusted_palette['intensity'] = round(intensity * 100, 1)
        
        # Generate additional derived colors
        adjusted_palette['primary_light'] = self._lighten_color(adjusted_palette['primary'], 0.8)
        adjusted_palette['primary_dark'] = self._darken_color(adjusted_palette['primary'], 0.2)
        adjusted_palette['secondary_light'] = self._lighten_color(adjusted_palette['secondary'], 0.6)
        
        return adjusted_palette
    
    def get_conversation_theme_css(self, conversation_id: int) -> str:
        """Generate CSS custom properties for conversation theme"""
        palette = self.generate_color_palette(conversation_id)
        
        css_vars = []
        css_vars.append(f"  --conversation-primary: {palette['primary']};")
        css_vars.append(f"  --conversation-secondary: {palette['secondary']};")
        css_vars.append(f"  --conversation-accent: {palette['accent']};")
        css_vars.append(f"  --conversation-background: {palette['background']};")
        css_vars.append(f"  --conversation-text: {palette['text']};")
        css_vars.append(f"  --conversation-primary-light: {palette['primary_light']};")
        css_vars.append(f"  --conversation-primary-dark: {palette['primary_dark']};")
        css_vars.append(f"  --conversation-secondary-light: {palette['secondary_light']};")
        
        return ":root {\n" + "\n".join(css_vars) + "\n}"
    
    def _get_default_mood(self) -> Dict[str, float]:
        """Return default mood scores when analysis fails"""
        return {
            'professional': 5.0,
            'positive': 3.0,
            'trustworthy': 4.0,
            'calm': 2.0,
            'energetic': 1.0,
            'urgent': 0.0
        }
    
    def _adjust_color_intensity(self, rgb: Tuple[int, int, int], intensity: float) -> Tuple[int, int, int]:
        """Adjust color saturation and brightness based on mood intensity"""
        r, g, b = rgb
        h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
        
        # Increase saturation and brightness with higher intensity
        s = min(1.0, s + (intensity * 0.2))
        v = min(1.0, v + (intensity * 0.1))
        
        new_r, new_g, new_b = colorsys.hsv_to_rgb(h, s, v)
        return (int(new_r * 255), int(new_g * 255), int(new_b * 255))
    
    def _rgb_to_hex(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB tuple to hex color string"""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    
    def _lighten_color(self, hex_color: str, factor: float) -> str:
        """Lighten a hex color by mixing with white"""
        # Remove # if present
        hex_color = hex_color.lstrip('#')
        
        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # Mix with white
        r = int(r + (255 - r) * factor)
        g = int(g + (255 - g) * factor)
        b = int(b + (255 - b) * factor)
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _darken_color(self, hex_color: str, factor: float) -> str:
        """Darken a hex color by reducing brightness"""
        # Remove # if present
        hex_color = hex_color.lstrip('#')
        
        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # Reduce brightness
        r = int(r * (1 - factor))
        g = int(g * (1 - factor))
        b = int(b * (1 - factor))
        
        return f"#{r:02x}{g:02x}{b:02x}"

# Global instance
mood_color_generator = MoodColorGenerator()

def get_conversation_color_palette(conversation_id: int) -> Dict[str, str]:
    """Main function to get color palette for a conversation"""
    return mood_color_generator.generate_color_palette(conversation_id)

def get_conversation_theme_css(conversation_id: int) -> str:
    """Get CSS custom properties for conversation theme"""
    return mood_color_generator.get_conversation_theme_css(conversation_id)

def analyze_conversation_mood(conversation_id: int) -> Dict[str, float]:
    """Analyze and return mood scores for a conversation"""
    return mood_color_generator.analyze_conversation_mood(conversation_id)