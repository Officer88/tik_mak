
from PIL import Image
from io import BytesIO
import requests
from urllib.parse import urlparse
import os

def process_image(url, max_size=(800, 600)):
    """
    Process image from URL:
    1. Download image
    2. Resize while maintaining aspect ratio
    3. Save with optimized quality
    """
    # Parse URL to get filename
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
    
    # Download image
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    
    # Convert to RGB if necessary
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
    
    # Resize image
    img.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    # Save path
    save_dir = 'static/uploads/events'
    os.makedirs(save_dir, exist_ok=True)
    
    # Generate unique filename
    base, ext = os.path.splitext(filename)
    save_path = os.path.join(save_dir, f"{base}{ext}")
    
    # Save with optimization
    img.save(save_path, optimize=True, quality=85)
    
    # Return relative path for database
    return f'/static/uploads/events/{os.path.basename(save_path)}'
