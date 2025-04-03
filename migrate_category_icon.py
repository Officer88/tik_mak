from app import app, db
from sqlalchemy import Column, String
from alembic import op
import sqlalchemy as sa

def migrate_category_icon():
    with app.app_context():
        # Добавление нового столбца icon_image_path в таблицу category
        try:
            op.add_column('category', sa.Column('icon_image_path', sa.String(length=256), nullable=True))
            print("Добавлен столбец icon_image_path в таблицу category")
        except Exception as e:
            print(f"Ошибка при добавлении столбца icon_image_path: {str(e)}")
            # Если столбец уже существует, продолжаем
            pass

        # Добавление новых столбцов в таблицу venue
        try:
            op.add_column('venue', sa.Column('logo_path', sa.String(length=256), nullable=True))
            print("Добавлен столбец logo_path в таблицу venue")
        except Exception as e:
            print(f"Ошибка при добавлении столбца logo_path: {str(e)}")
            pass

        try:
            op.add_column('venue', sa.Column('scheme_path', sa.String(length=256), nullable=True))
            print("Добавлен столбец scheme_path в таблицу venue")
        except Exception as e:
            print(f"Ошибка при добавлении столбца scheme_path: {str(e)}")
            pass

        # Добавление нового столбца file_path в таблицу ticket
        try:
            op.add_column('ticket', sa.Column('file_path', sa.String(length=256), nullable=True))
            print("Добавлен столбец file_path в таблицу ticket")
        except Exception as e:
            print(f"Ошибка при добавлении столбца file_path: {str(e)}")
            pass

if __name__ == "__main__":
    migrate_category_icon()