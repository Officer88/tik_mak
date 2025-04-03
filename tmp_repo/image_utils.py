
from PIL import Image
from io import BytesIO
import os
from datetime import datetime
import uuid
import shutil
import logging
from werkzeug.utils import secure_filename

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

def process_image(file_obj, max_size=(240, 320), folder_type='events'):
    """
    Обрабатывает изображение, загруженное с ПК:
    1. Проверяет тип файла и применяет специальную обработку для SVG, GIF
    2. Изменяет размер с сохранением пропорций
    3. Сохраняет с оптимизацией
    
    Parameters:
    - file_obj: Файловый объект из формы (обязательный)
    - max_size: Рекомендуемый размер (ширина, высота)
    - folder_type: Тип папки (events, categories, venues, slides, venues/schemes)
    
    Returns:
    - Путь к файлу относительно статической директории
    """
    try:
        if not file_obj:
            logger.error("Файл не передан")
            return None
        
        # Проверяем имя файла
        original_filename = secure_filename(file_obj.filename)
        if not original_filename:
            logger.error("Пустое имя файла")
            return None
        
        logger.info(f"Обработка файла: {original_filename}, тип папки: {folder_type}")
        
        # Проверка на специальные форматы файлов (SVG, GIF)
        if original_filename.lower().endswith('.svg') or original_filename.lower().endswith('.gif') or 'photoviewer.fileassoc.tiff' in original_filename.lower():
            # Используем функцию сохранения специальных форматов
            return save_special_format_file(file_obj, folder_type=folder_type)
        
        # Открываем изображение с помощью PIL
        try:
            # Сбрасываем указатель файла в начало
            file_obj.seek(0)
            img = Image.open(file_obj)
        except Exception as e:
            logger.error(f"Ошибка при открытии файла: {str(e)}")
            return None
            
        # Проверка на GIF-анимацию
        is_animated_gif = False
        if hasattr(img, 'format') and img.format == 'GIF':
            if hasattr(img, 'is_animated') and img.is_animated:
                logger.info("Обнаружен анимированный GIF")
                is_animated_gif = True
                # Для GIF-анимаций используем специальную обработку
                file_obj.seek(0)
                return save_special_format_file(file_obj, folder_type=folder_type)
        
        # Логируем информацию об изображении
        logger.info(f"Формат: {getattr(img, 'format', 'неизвестно')}, размер: {img.size}, режим: {img.mode}")
        
        # Если у нас RGBA или другой формат с прозрачностью, и это не GIF - конвертируем в RGB
        if img.mode in ('RGBA', 'P') and not is_animated_gif:
            try:
                img = img.convert('RGB')
                logger.info(f"Изображение конвертировано из {img.mode} в RGB")
            except Exception as e:
                logger.error(f"Ошибка при конвертации в RGB: {str(e)}")
        
        # Получаем оригинальные размеры
        width, height = img.size
        
        # Рассчитываем новые размеры с сохранением пропорций
        aspect_ratio = width / height
        target_width, target_height = max_size
        
        if width > height:
            # Ландшафтное изображение
            new_width = min(width, target_width)
            new_height = int(new_width / aspect_ratio)
        else:
            # Портретное или квадратное изображение
            new_height = min(height, target_height)
            new_width = int(new_height * aspect_ratio)
        
        # Убеждаемся, что размеры положительные
        new_width = max(new_width, 1)
        new_height = max(new_height, 1)
        
        logger.info(f"Изменение размера: {img.size} -> ({new_width}, {new_height})")
        
        # Изменяем размер
        try:
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        except Exception as e:
            logger.error(f"Ошибка при изменении размера: {str(e)}")
            resized_img = img  # При ошибке используем оригинал
        
        # Создаем директорию для сохранения, если её нет
        save_dir = os.path.join('static', 'uploads', folder_type)
        os.makedirs(save_dir, exist_ok=True)
        
        # Формируем уникальное имя файла
        base_name, ext = os.path.splitext(original_filename)
        if not ext:
            ext = '.jpg'  # Если расширение не определено, используем .jpg
        
        ext = ext.lower()  # Приводим расширение к нижнему регистру
        unique_id = uuid.uuid4().hex
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # Создаем финальное имя файла
        unique_filename = f"{unique_id}_{timestamp}_{base_name}{ext}"
        save_path = os.path.join(save_dir, unique_filename)
        
        # Сохраняем файл
        try:
            if ext.lower() == '.png':
                resized_img.save(save_path, format='PNG', optimize=True)
                logger.info("Сохранено как PNG")
            elif ext.lower() in ('.jpg', '.jpeg'):
                resized_img.save(save_path, format='JPEG', optimize=True, quality=90)
                logger.info("Сохранено как JPEG")
            else:
                # Для других форматов пробуем использовать расширение
                format_name = ext[1:].upper() if ext.startswith('.') else ext.upper()
                resized_img.save(save_path, format=format_name, optimize=True)
                logger.info(f"Сохранено в формате {format_name}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении: {str(e)}")
            # При ошибке пробуем сохранить как JPEG
            try:
                new_save_path = f"{os.path.splitext(save_path)[0]}.jpg"
                if resized_img.mode != 'RGB':
                    resized_img = resized_img.convert('RGB')
                resized_img.save(new_save_path, format='JPEG', optimize=True, quality=90)
                save_path = new_save_path
                logger.info("Сохранено как JPEG после обработки ошибки")
            except Exception as e2:
                logger.error(f"Критическая ошибка при сохранении: {str(e2)}")
                return None
        
        # Возвращаем путь без префикса 'static/'
        if save_path.startswith('static/'):
            rel_path = save_path[7:]
        else:
            rel_path = save_path
            
        logger.info(f"Файл успешно сохранён по пути: {rel_path}")
        return rel_path
        
    except Exception as e:
        logger.error(f"Необработанная ошибка в process_image: {str(e)}")
        return None


def save_image(file_obj, folder_type='events', max_size=(240, 320)):
    """
    Универсальная функция для сохранения изображений, 
    которая заменяет все старые методы загрузки.
    """
    if not file_obj or not hasattr(file_obj, 'filename') or not file_obj.filename:
        logger.error("Некорректный файловый объект")
        return None
        
    return process_image(file_obj, max_size, folder_type)
