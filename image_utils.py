
from PIL import Image
from io import BytesIO
import requests
from urllib.parse import urlparse
import os
from datetime import datetime
import uuid

def process_image(source, max_size=(240, 320), file_obj=None, destination=None):
    """
    Process image from URL or file object:
    1. Download image (if URL) or use file object
    2. Resize while maintaining aspect ratio without cropping
    3. Save with optimized quality
    
    Parameters:
    - source: URL string or filename
    - max_size: Recommended size for event card images (width, height)
    - file_obj: Optional file object from upload
    - destination: Optional full path where to save the file
    
    Returns:
    - Path to saved image relative to static folder
    """
    if file_obj:
        # Use uploaded file
        img = Image.open(file_obj)
        filename = file_obj.filename
    elif source:
        # Parse URL to get filename
        parsed_url = urlparse(source)
        filename = os.path.basename(parsed_url.path)
        
        # Download image
        response = requests.get(source)
        img = Image.open(BytesIO(response.content))
    else:
        return None
    
    # Проверка, является ли файл GIF-анимацией
    is_animated_gif = False
    if hasattr(img, 'is_animated') and img.is_animated:
        is_animated_gif = True
    
    # Если это не анимированный GIF, конвертируем в RGB при необходимости
    if not is_animated_gif and img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
    
    # Получаем оригинальные размеры
    width, height = img.size
    
    # Рассчитываем соотношение сторон
    aspect_ratio = width / height
    
    # Рассчитываем новые размеры с сохранением соотношения сторон
    target_width, target_height = max_size
    if width > height:
        # Ландшафтное изображение
        new_width = min(width, target_width)
        new_height = int(new_width / aspect_ratio)
    else:
        # Портретное или квадратное изображение
        new_height = min(height, target_height)
        new_width = int(new_height * aspect_ratio)
    
    # Если это не анимированный GIF, изменяем размер
    if not is_animated_gif:
        # Изменяем размер изображения, используя высококачественную интерполяцию
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Определяем путь для сохранения
    if destination:
        save_path = destination
    else:
        save_dir = 'static/uploads/events'
        os.makedirs(save_dir, exist_ok=True)
        
        # Генерируем уникальное имя файла с временной меткой и UUID
        base, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        save_path = os.path.join(save_dir, f"{base}_{timestamp}_{unique_id}{ext}")
    
    # Проверяем, существует ли папка для сохранения
    save_dir = os.path.dirname(save_path)
    os.makedirs(save_dir, exist_ok=True)
    
    # Сохраняем с оптимизацией
    if is_animated_gif:
        # Для GIF-анимаций сохраняем как есть
        img.save(save_path)
    else:
        img.save(save_path, optimize=True, quality=85)
    
    # Возвращаем относительный путь для базы данных
    rel_path = save_path
    if save_path.startswith('static/'):
        rel_path = save_path[7:]  # Удаляем 'static/' из пути
    
    return rel_path
