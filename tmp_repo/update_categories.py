from app import app, db
from models import Category, Event

def update_categories():
    # Определим новые категории с нужными именами и иконками
    target_categories = [
        {"name": "Театр", "icon": "fa-theater-masks", "seo_title": "Билеты на театры - MAGIK TIKET", "seo_description": "Купить билеты на театры по выгодным ценам на MAGIK TIKET. Большой выбор мероприятий."},
        {"name": "Концерты", "icon": "fa-music", "seo_title": "Билеты на концерты - MAGIK TIKET", "seo_description": "Купить билеты на концерты по выгодным ценам на MAGIK TIKET. Большой выбор мероприятий."},
        {"name": "Экскурсии", "icon": "fa-walking", "seo_title": "Билеты на экскурсии - MAGIK TIKET", "seo_description": "Купить билеты на экскурсии по выгодным ценам на MAGIK TIKET. Большой выбор мероприятий."},
        {"name": "Фестивали", "icon": "fa-flag-checkered", "seo_title": "Билеты на фестивали - MAGIK TIKET", "seo_description": "Купить билеты на фестивали по выгодным ценам на MAGIK TIKET. Большой выбор мероприятий."},
        {"name": "Выставки", "icon": "fa-palette", "seo_title": "Билеты на выставки - MAGIK TIKET", "seo_description": "Купить билеты на выставки по выгодным ценам на MAGIK TIKET. Большой выбор мероприятий."},
        {"name": "Спорт", "icon": "fa-running", "seo_title": "Билеты на спорт - MAGIK TIKET", "seo_description": "Купить билеты на спорт по выгодным ценам на MAGIK TIKET. Большой выбор мероприятий."},
        {"name": "Международные события", "icon": "fa-globe", "seo_title": "Билеты на международные события - MAGIK TIKET", "seo_description": "Купить билеты на международные события по выгодным ценам на MAGIK TIKET. Большой выбор мероприятий."}
    ]
    
    # Получим существующие категории
    existing_categories = {cat.name: cat for cat in Category.query.all()}
    print(f"Существующие категории: {', '.join(existing_categories.keys())}")
    
    for cat_data in target_categories:
        name = cat_data["name"]
        if name in existing_categories:
            # Обновляем существующую категорию
            cat = existing_categories[name]
            cat.icon = cat_data["icon"]
            cat.seo_title = cat_data["seo_title"]
            cat.seo_description = cat_data["seo_description"]
            print(f"Обновлена категория: {name}")
        else:
            # Создаем новую категорию
            new_cat = Category(
                name=name,
                icon=cat_data["icon"],
                seo_title=cat_data["seo_title"],
                seo_description=cat_data["seo_description"]
            )
            db.session.add(new_cat)
            print(f"Создана новая категория: {name}")
    
    # Делаем коммит созданных и обновленных категорий, чтобы можно было их использовать при обновлении событий
    db.session.commit()
    
    # Находим категории, которые нужно удалить
    to_delete_names = set(existing_categories.keys()) - {cat["name"] for cat in target_categories}
    
    if to_delete_names:
        # Находим категорию, в которую перенесем события
        first_target = Category.query.filter_by(name=target_categories[0]["name"]).first()
        if not first_target:
            print(f"Ошибка: целевая категория '{target_categories[0]['name']}' не найдена")
            return
        
        print(f"Будем перемещать события в категорию: {first_target.name} (ID: {first_target.id})")
        
        for cat_name in to_delete_names:
            cat_to_delete = existing_categories[cat_name]
            # Получаем события, которые нужно переместить
            events = Event.query.filter_by(category_id=cat_to_delete.id).all()
            if events:
                print(f"Найдено {len(events)} событий для категории '{cat_name}'")
                # Обновляем категорию для всех событий
                for event in events:
                    print(f"Событие '{event.title}' (ID: {event.id}) перемещено из категории '{cat_name}' (ID: {cat_to_delete.id}) в категорию '{first_target.name}' (ID: {first_target.id})")
                    event.category_id = first_target.id
                
                # Сохраняем изменения перед удалением категории
                db.session.commit()
            
            # Теперь можно удалить категорию - запомним ID для вывода
            cat_id = cat_to_delete.id
            db.session.delete(cat_to_delete)
            print(f"Удалена категория: {cat_name} (ID: {cat_id})")
            db.session.commit()
    
    print(f"Успешно обновлены категории")

if __name__ == "__main__":
    with app.app_context():
        update_categories()