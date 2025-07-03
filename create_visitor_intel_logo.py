"""
Create Visitor Intel Logo
Professional version of the AI conversation platform logo
"""

from PIL import Image, ImageDraw, ImageFont
import base64
from io import BytesIO

def create_visitor_intel_logo():
    """Create a professional logo for Visitor Intel"""
    
    # Logo dimensions
    width = 400
    height = 400
    
    # Colors
    primary_color = '#1a1a1a'  # Dark background
    gold_color = '#ffd700'     # Gold text
    red_color = '#dc2626'      # Red accent
    blue_color = '#3b82f6'     # Blue accent
    
    # Create image with transparent background
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw outer circle
    margin = 20
    circle_coords = [margin, margin, width-margin, height-margin]
    draw.ellipse(circle_coords, fill=primary_color, outline=gold_color, width=4)
    
    # Center for character
    center_x = width // 2
    center_y = height // 2
    
    # Draw devil horns (simplified)
    horn_size = 25
    # Left horn
    horn_left = [center_x - 40, center_y - 80, center_x - 15, center_y - 55]
    draw.ellipse(horn_left, fill=red_color)
    # Right horn
    horn_right = [center_x + 15, center_y - 80, center_x + 40, center_y - 55]
    draw.ellipse(horn_right, fill=red_color)
    
    # Draw face (simplified)
    face_coords = [center_x - 60, center_y - 50, center_x + 60, center_y + 50]
    draw.ellipse(face_coords, fill=red_color, outline='#b91c1c', width=2)
    
    # Draw crown
    crown_points = [
        (center_x - 45, center_y - 70),
        (center_x - 30, center_y - 85),
        (center_x - 15, center_y - 75),
        (center_x, center_y - 90),
        (center_x + 15, center_y - 75),
        (center_x + 30, center_y - 85),
        (center_x + 45, center_y - 70),
        (center_x + 40, center_y - 60),
        (center_x - 40, center_y - 60)
    ]
    draw.polygon(crown_points, fill=gold_color, outline='#eab308', width=2)
    
    # Draw eyes
    eye_y = center_y - 20
    # Left eye
    draw.ellipse([center_x - 35, eye_y - 8, center_x - 15, eye_y + 8], fill=blue_color)
    draw.ellipse([center_x - 30, eye_y - 4, center_x - 20, eye_y + 4], fill='white')
    # Right eye
    draw.ellipse([center_x + 15, eye_y - 8, center_x + 35, eye_y + 8], fill=blue_color)
    draw.ellipse([center_x + 20, eye_y - 4, center_x + 30, eye_y + 4], fill='white')
    
    # Draw smile
    smile_coords = [center_x - 30, center_y + 10, center_x + 30, center_y + 30]
    draw.arc(smile_coords, start=0, end=180, fill='white', width=3)
    
    # Text around the circle
    try:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    except:
        font_large = font_small = ImageFont.load_default()
    
    # Top text: "VISITOR INTEL"
    top_text = "VISITOR INTEL"
    # Calculate text position (approximate)
    text_y_top = margin + 25
    text_x = center_x - 70  # Approximate center
    draw.text((text_x, text_y_top), top_text, fill=gold_color, font=font_large)
    
    # Bottom text: "AI CONVERSATIONS"
    bottom_text = "AI CONVERSATIONS"
    text_y_bottom = height - margin - 45
    text_x_bottom = center_x - 85  # Approximate center
    draw.text((text_x_bottom, text_y_bottom), bottom_text, fill=gold_color, font=font_small)
    
    # Save logo
    img.save('/tmp/visitor_intel_logo.png', 'PNG')
    img.save('/home/runner/workspace/static/visitor_intel_logo.png', 'PNG')
    print("Visitor Intel logo created")
    
    # Return base64 for web use
    img_buffer = BytesIO()
    img.save(img_buffer, format='PNG')
    img_bytes = img_buffer.getvalue()
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    
    return img_base64

def create_favicon():
    """Create a favicon version of the logo"""
    
    # Small favicon size
    size = 32
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Simple devil head for favicon
    center = size // 2
    
    # Face
    face_coords = [4, 8, size-4, size-4]
    draw.ellipse(face_coords, fill='#dc2626')
    
    # Horns
    draw.ellipse([6, 2, 10, 8], fill='#991b1b')
    draw.ellipse([size-10, 2, size-6, 8], fill='#991b1b')
    
    # Crown
    crown_points = [(8, 6), (12, 2), (16, 4), (20, 2), (24, 6), (22, 8), (10, 8)]
    draw.polygon(crown_points, fill='#ffd700')
    
    # Eyes
    draw.ellipse([10, 12, 12, 14], fill='white')
    draw.ellipse([20, 12, 22, 14], fill='white')
    
    img.save('/home/runner/workspace/static/favicon.ico', 'ICO')
    img.save('/home/runner/workspace/static/favicon.png', 'PNG')
    print("Favicon created")

if __name__ == "__main__":
    create_visitor_intel_logo()
    create_favicon()