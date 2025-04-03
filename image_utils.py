
from PIL import Image
from io import BytesIO
import requests
from urllib.parse import urlparse
import os
from datetime import datetime
import uuid
import shutil
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def save_special_format_file(file_obj, destination=None, folder_type='events'):
    """
    Сохраняет файл специального формата (SVG, GIF, PhotoViewer.FileAssoc.Tiff) без обработки.
    
    Parameters:
    - file_obj: Файловый объект из формы
    - destination: Опциональный путь для сохранения
    - folder_type: Тип папки для сохранения (events, categories, venues, slides, venues/schemes)
    
    Returns:
    - Путь к сохраненному файлу относительно static
    """
    try:
        if not file_obj:
            logger.error("Не передан файловый объект")
            return None
            
        filename = file_obj.filename if hasattr(file_obj, 'filename') else "unknown.file"
        
        # Определяем тип файла
        file_type = 'UNKNOWN'
        if filename.lower().endswith('.svg'):
            file_type = 'SVG'
        elif filename.lower().endswith('.gif'):
            file_type = 'GIF'
        elif 'photoviewer.fileassoc.tiff' in filename.lower():
            file_type = 'TIFF-GIF'
        
        logger.info(f"Обработка файла специального формата ({file_type}): {filename}")
        
        # Генерируем уникальное имя файла с временной меткой
        unique_id = uuid.uuid4().hex
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # Для PhotoViewer.FileAssoc.Tiff устанавливаем расширение .gif
        if 'photoviewer.fileassoc.tiff' in filename.lower():
            unique_filename = f"{unique_id}_{timestamp}_animated.gif"
        else:
            # Сохраняем оригинальное расширение файла
            base_name, ext = os.path.splitext(filename)
            if not ext:
                # Если расширения нет, определяем его по типу
                if file_type == 'SVG':
                    ext = '.svg'
                elif file_type == 'GIF':
                    ext = '.gif'
                else:
                    ext = '.dat'  # Для неизвестных типов
            
            # Очистим расширение от лишних символов
            ext = ext.lower()
            if not ext.startswith('.'):
                ext = '.' + ext
            
            unique_filename = f"{unique_id}_{timestamp}_{base_name}{ext}"
        
        # Определяем путь для сохранения
        if destination:
            save_path = destination
        else:
            # Создаем папку для загрузки, если она не существует
            save_dir = os.path.join('static', 'uploads', folder_type)
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, unique_filename)
        
        # Перемещаем указатель файла в начало
        file_obj.seek(0)
        
        # Сохраняем файл как есть, без обработки
        with open(save_path, 'wb') as f:
            f.write(file_obj.read())
        
        logger.info(f"Файл специального формата сохранен как: {save_path}")
        
        # Возвращаем путь относительно 'static'
        if save_path.startswith('static/'):
            return save_path[7:]  # Удаляем 'static/' для URL
        return save_path
        
    except Exception as e:
        logger.error(f"Ошибка при сохранении специального формата: {str(e)}")
        return None

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
    try:
        # Специальные форматы обрабатываем через специальную функцию
        if file_obj and (file_obj.filename.lower().endswith('.svg') or 
                         file_obj.filename.lower().endswith('.gif') or 
                         'photoviewer.fileassoc.tiff' in file_obj.filename.lower()):
            
            logger.info(f"Обнаружен файл специального формата в process_image: {file_obj.filename}")
            
            # Используем функцию save_special_format_file для специальных форматов
            folder_type = 'events'  # По умолчанию папка events
            
            # Определяем папку из пути назначения, если он задан
            if destination:
                if '/categories/' in destination:
                    folder_type = 'categories'
                elif '/venues/schemes/' in destination:
                    folder_type = 'venues/schemes'
                elif '/venues/' in destination:
                    folder_type = 'venues'
                elif '/slides/' in destination:
                    folder_type = 'slides'
            
            # Используем специальную функцию сохранения
            return save_special_format_file(file_obj, destination, folder_type)
        
        if file_obj:
            # Use uploaded file
            logger.info(f"Открываем загруженный файл: {file_obj.filename}")
            try:
                img = Image.open(file_obj)
                filename = file_obj.filename
            except Exception as e:
                logger.error(f"Ошибка при открытии файла: {str(e)}")
                raise e
        elif source:
            # Parse URL to get filename
            parsed_url = urlparse(source)
            filename = os.path.basename(parsed_url.path)
            
            # Download image
            response = requests.get(source)
            img = Image.open(BytesIO(response.content))
        else:
            logger.error("Не предоставлен ни источник, ни файл")
            return None
        
        # Убедимся, что у нас есть расширение файла
        if not filename or '.' not in filename:
            # Если нет имени или расширения, используем временное имя с расширением .jpg
            filename = f"image_{uuid.uuid4().hex}.jpg"
            logger.info(f"Имя файла не задано или без расширения. Новое имя: {filename}")
        
        # Проверка, является ли файл GIF-анимацией
        is_animated_gif = False
        
        # Проверка на особый формат имени файла PhotoViewer.FileAssoc.Tiff (.gif)
        if filename and '.gif' in filename.lower():
            logger.info(f"Обнаружен файл с расширением .gif в имени: {filename}")
            is_animated_gif = True
        
        # Проверка формата изображения
        if hasattr(img, 'format') and img.format == 'GIF':
            if hasattr(img, 'is_animated') and img.is_animated:
                is_animated_gif = True
                logger.info("Обнаружен анимированный GIF")
        
        logger.info(f"Формат изображения: {getattr(img, 'format', 'неизвестно')}, размер: {img.size}, режим: {img.mode}")
        
        # Если это не анимированный GIF, конвертируем в RGB при необходимости
        if not is_animated_gif and img.mode in ('RGBA', 'P'):
            logger.info(f"Конвертируем изображение из режима {img.mode} в RGB")
            try:
                img = img.convert('RGB')
            except Exception as e:
                logger.error(f"Ошибка при конвертации в RGB: {str(e)}")
        
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
        
        logger.info(f"Изменение размера из {img.size} в ({new_width}, {new_height})")
        
        # Если это не анимированный GIF, изменяем размер
        resized_img = None
        if not is_animated_gif:
            # Изменяем размер изображения, используя высококачественную интерполяцию
            try:
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            except Exception as e:
                logger.error(f"Ошибка при изменении размера: {str(e)}")
                resized_img = img  # Используем оригинал в случае ошибки
        else:
            resized_img = img  # Для анимированных GIF используем оригинал
        
        # Определяем путь для сохранения
        if destination:
            save_path = destination
        else:
            save_dir = 'static/uploads/events'
            os.makedirs(save_dir, exist_ok=True)
            
            # Генерируем уникальное имя файла с временной меткой и UUID
            base, ext = os.path.splitext(filename)
            ext = ext.lower()  # Приводим расширение к нижнему регистру
            
            # Проверяем, что у нас действительно есть расширение
            if not ext:
                # По умолчанию используем .jpg
                ext = '.jpg'
            
            # Сохраняем формат для GIF-файлов
            if is_animated_gif and ext != '.gif':
                ext = '.gif'
            
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            save_path = os.path.join(save_dir, f"{base}_{timestamp}_{unique_id}{ext}")
        
        # Проверяем, существует ли папка для сохранения
        save_dir = os.path.dirname(save_path)
        os.makedirs(save_dir, exist_ok=True)
        
        logger.info(f"Сохраняем изображение в: {save_path}")
        
        # Сохраняем с оптимизацией
        try:
            if is_animated_gif:
                # Для GIF-анимаций сохраняем как есть
                img.save(save_path, save_all=True)
                logger.info("Сохранен анимированный GIF")
            elif resized_img.mode == 'RGBA':
                # Для изображений с прозрачностью сохраняем как PNG
                resized_img.save(save_path, optimize=True)
                logger.info("Сохранено изображение с прозрачностью (PNG)")
            elif save_path.lower().endswith('.png'):
                resized_img.save(save_path, optimize=True)
                logger.info("Сохранено как PNG")
            elif save_path.lower().endswith(('.jpg', '.jpeg')):
                resized_img.save(save_path, optimize=True, quality=85)
                logger.info("Сохранено как JPEG")
            else:
                # Для других форматов пробуем использовать расширение
                ext = os.path.splitext(save_path)[1]
                format_name = ext[1:].upper() if ext else 'JPEG'  # убираем точку и переводим в верхний регистр
                
                resized_img.save(save_path, format=format_name, optimize=True)
                logger.info(f"Сохранено в формате {format_name}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении изображения: {str(e)}")
            # Если формат не поддерживается, сохраняем как JPEG
            try:
                if not save_path.lower().endswith('.jpg'):
                    new_save_path = f"{os.path.splitext(save_path)[0]}.jpg"
                else:
                    new_save_path = save_path
                
                if resized_img.mode == 'RGBA':
                    resized_img = resized_img.convert('RGB')
                
                resized_img.save(new_save_path, format='JPEG', optimize=True, quality=85)
                save_path = new_save_path
                logger.info(f"Сохранено в формате JPEG после обработки ошибки: {new_save_path}")
            except Exception as e2:
                logger.error(f"Критическая ошибка при сохранении в JPEG: {str(e2)}")
                # В крайнем случае возвращаем None
                return None
        
        # Возвращаем относительный путь для базы данных
        rel_path = save_path
        if save_path.startswith('static/'):
            rel_path = save_path[7:]  # Удаляем 'static/' из пути
        
        logger.info(f"Возвращаем путь к изображению: {rel_path}")
        return rel_path
    
    except Exception as e:
        logger.error(f"Необработанная ошибка в process_image: {str(e)}")
        # В случае любой ошибки возвращаем None
        return None
