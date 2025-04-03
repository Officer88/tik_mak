import os
import logging
from app import app

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Создаем необходимые директории для загрузок файлов
def ensure_upload_dirs():
    upload_dirs = [
        os.path.join('static', 'uploads'),
        os.path.join('static', 'uploads', 'events'),
        os.path.join('static', 'uploads', 'categories'),
        os.path.join('static', 'uploads', 'venues'),
        os.path.join('static', 'uploads', 'venues', 'schemes'),
        os.path.join('static', 'uploads', 'slides'),
    ]
    
    for directory in upload_dirs:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Убедились, что директория {directory} существует")

# На случай если приложение запущено не через Gunicorn
if __name__ == "__main__":
    logger.info("Запуск приложения в режиме разработки")
    ensure_upload_dirs()
    app.run(host="0.0.0.0", port=5000, debug=True)
