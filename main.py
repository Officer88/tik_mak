import os
from app import app

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
        print(f"Убедились, что директория {directory} существует")

if __name__ == "__main__":
    ensure_upload_dirs()
    app.run(host="0.0.0.0", port=5000, debug=True)
