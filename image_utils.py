
from PIL import Image
from io import BytesIO
import requests
from urllib.parse import urlparse
import os
from datetime import datetime
import uuid

def process_image(source, max_size=(400, 300), file_obj=None):
    """
    Process image from URL or file object:
    1. Download image (if URL) or use file object
    2. Resize while maintaining aspect ratio without cropping
    3. Save with optimized quality
    
    Parameters:
    - source: URL string or filename
    - max_size: Recommended size for event card images (width, height)
    - file_obj: Optional file object from upload
    
    Returns:
    - Path to saved image relative to static folder
    """
    if file_obj:
        # Use uploaded file
        img = Image.open(file_obj)
        filename = file_obj.filename
    else:
        # Parse URL to get filename
        parsed_url = urlparse(source)
        filename = os.path.basename(parsed_url.path)
        
        # Download image
        response = requests.get(source)
        img = Image.open(BytesIO(response.content))
    
    # Convert to RGB if necessary
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
    
    # Get original dimensions
    width, height = img.size
    
    # Calculate aspect ratio
    aspect_ratio = width / height
    
    # Calculate new dimensions while preserving aspect ratio
    target_width, target_height = max_size
    if width > height:
        # Landscape image
        new_width = min(width, target_width)
        new_height = int(new_width / aspect_ratio)
    else:
        # Portrait or square image
        new_height = min(height, target_height)
        new_width = int(new_height * aspect_ratio)
    
    # Resize image using high-quality resampling
    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Save path
    save_dir = 'static/uploads/events'
    os.makedirs(save_dir, exist_ok=True)
    
    # Generate unique filename with timestamp and UUID to avoid overwriting
    base, ext = os.path.splitext(filename)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    save_path = os.path.join(save_dir, f"{base}_{timestamp}_{unique_id}{ext}")
    
    # Save with optimization
    img.save(save_path, optimize=True, quality=85)
    
    # Return relative path for database
    return f'/static/uploads/events/{os.path.basename(save_path)}'
