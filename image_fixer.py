"""
Скрипт для исправления обработки изображений в проекте BiletService.
"""

import os
import re

def fix_admin_routes_image_handling():
    """
    Фиксирует все вызовы обработки изображений в файле admin_routes.py,
    заменяя их на использование функции save_image().
    """
    
    # Путь к файлу
    file_path = 'admin_routes.py'
    
    # Создаем резервную копию файла
    backup_path = f"{file_path}.bak_fix"
    os.system(f"cp {file_path} {backup_path}")
    print(f"Создана резервная копия: {backup_path}")
    
    # Читаем содержимое файла
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Шаблон 1: Замена импорта process_image на save_image
    pattern1 = r'from image_utils import process_image'
    replacement1 = 'from image_utils import save_image'
    content = re.sub(pattern1, replacement1, content)
    
    # Шаблон 2: Замена вызовов process_image на save_image для слайдеров
    pattern2 = r'saved_path = process_image\(\s*source=None,\s*max_size=\(1200,\s*600\),\s*file_obj=form\.image\.data,\s*destination=os\.path\.join\(upload_folder,\s*unique_filename\)\s*\)'
    replacement2 = '''saved_path = save_image(
                file_obj=form.image.data,
                folder_type='slides',
                max_size=(1200, 600)  # Размер слайдера
            )'''
    content = re.sub(pattern2, replacement2, content)
    
    # Шаблон 3: Замена вызовов process_image на save_image для категорий
    pattern3 = r'saved_path = process_image\(\s*source=None,\s*max_size=\(100,\s*100\),\s*file_obj=form\.icon_image\.data,\s*destination=os\.path\.join\(upload_folder,\s*unique_filename\)\s*\)'
    replacement3 = '''saved_path = save_image(
                    file_obj=form.icon_image.data,
                    folder_type='categories',
                    max_size=(100, 100)  # Размер иконки категории
                )'''
    content = re.sub(pattern3, replacement3, content)
    
    # Шаблон 4: Замена вызовов process_image на save_image для площадок
    pattern4 = r'saved_path = process_image\(\s*source=None,\s*max_size=\(200,\s*100\),\s*file_obj=form\.logo_file\.data,\s*destination=os\.path\.join\(upload_folder,\s*unique_filename\)\s*\)'
    replacement4 = '''saved_path = save_image(
                file_obj=form.logo_file.data,
                folder_type='venues',
                max_size=(200, 100)  # Размер логотипа площадки
            )'''
    content = re.sub(pattern4, replacement4, content)

    # Шаблон 5: Замена обработки URL на пустую строку
    pattern5 = r'elif image_url\s*[^\n]+\s*# Обрабатываем изображение по URL\s*[^\n]+\s*image_url = process_image\(image_url[^\n]+\)'
    replacement5 = '''elif False:
                    # Загрузка по URL удалена
                    pass'''
    content = re.sub(pattern5, replacement5, content)
    
    # Записываем изменения в файл
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Файл {file_path} успешно обновлен!")

if __name__ == "__main__":
    fix_admin_routes_image_handling()