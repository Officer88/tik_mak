from app import app, db
from sqlalchemy import text
import sys

def migrate_venues():
    try:
        with app.app_context():
            # Получаем текущую версию схемы
            conn = db.engine.connect()
            
            # Проверяем, существуют ли уже столбцы
            has_logo_url = False
            has_scheme_url = False
            has_description = False
            
            # Проверяем наличие столбцов
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='venue'"))
            columns = [row[0] for row in result]
            
            print(f"Существующие столбцы в таблице venue: {columns}")
            
            if 'logo_url' in columns:
                has_logo_url = True
                print("Столбец logo_url уже существует")
            
            if 'scheme_url' in columns:
                has_scheme_url = True
                print("Столбец scheme_url уже существует")
                
            if 'description' in columns:
                has_description = True
                print("Столбец description уже существует")
            
            # Добавляем отсутствующие столбцы
            if not has_logo_url:
                print("Добавление столбца logo_url...")
                conn.execute(text("ALTER TABLE venue ADD COLUMN logo_url VARCHAR(256)"))
            
            if not has_scheme_url:
                print("Добавление столбца scheme_url...")
                conn.execute(text("ALTER TABLE venue ADD COLUMN scheme_url VARCHAR(256)"))
                
            if not has_description:
                print("Добавление столбца description TEXT...")
                conn.execute(text("ALTER TABLE venue ADD COLUMN description TEXT"))
            
            # Фиксируем изменения
            conn.commit()
            print("Миграция успешно завершена!")
            
    except Exception as e:
        print(f"Ошибка при миграции: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = migrate_venues()
    sys.exit(0 if success else 1)