import os
import json
import requests
from bs4 import BeautifulSoup
import random
from datetime import datetime, timedelta
from app import app, db
from models import Category, Venue, Event, Slide

# Функция для получения данных с magiktiket.com
def scrape_magiktiket():
    try:
        response = requests.get('https://magiktiket.com')
        if response.status_code != 200:
            print(f"Ошибка при получении данных: {response.status_code}")
            return None
        return response.text
    except Exception as e:
        print(f"Произошла ошибка при запросе к сайту: {e}")
        return None

# Поскольку мы не можем напрямую получить доступ к сайту через скрипт,
# создадим заполнители с примерными данными, похожими на те, что могли бы быть на magiktiket.com
def create_sample_data():
    # Категории
    categories = [
        {"name": "Концерты", "icon": "fa-music"},
        {"name": "Театры", "icon": "fa-theater-masks"},
        {"name": "Спорт", "icon": "fa-futbol"},
        {"name": "Фестивали", "icon": "fa-flag"},
        {"name": "Детские", "icon": "fa-child"},
        {"name": "Выставки", "icon": "fa-palette"}
    ]
    
    # Площадки
    venues = [
        {"name": "Крокус Сити Холл", "address": "Международная, 20", "city": "Москва"},
        {"name": "Спортивный комплекс Олимпийский", "address": "Олимпийский проспект, 16", "city": "Москва"},
        {"name": "Ледовый дворец", "address": "Проспект Пятилеток, 1", "city": "Санкт-Петербург"},
        {"name": "Театр им. Вахтангова", "address": "ул. Арбат, 26", "city": "Москва"},
        {"name": "Экспоцентр", "address": "Краснопресненская набережная, 14", "city": "Москва"}
    ]
    
    # События
    events = [
        {
            "title": "Концерт группы Ленинград",
            "description": "Новая программа популярной группы с лучшими хитами и премьерами песен.",
            "image_url": "https://i.imgur.com/IluELxJ.jpg",
            "date": (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d %H:%M"),
            "category_id": 1,  # Концерты
            "venue_id": 1,  # Крокус Сити Холл
            "base_price": 2500,
            "max_price": 10000
        },
        {
            "title": "Балет 'Лебединое озеро'",
            "description": "Классический балет в исполнении артистов Большого театра.",
            "image_url": "https://i.imgur.com/JC2vGkm.jpg",
            "date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M"),
            "category_id": 2,  # Театры
            "venue_id": 4,  # Театр им. Вахтангова
            "base_price": 3000,
            "max_price": 8000
        },
        {
            "title": "Хоккейный матч ЦСКА - СКА",
            "description": "Решающий матч чемпионата КХЛ между принципиальными соперниками.",
            "image_url": "https://i.imgur.com/iF0tjbL.jpg",
            "date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d %H:%M"),
            "category_id": 3,  # Спорт
            "venue_id": 3,  # Ледовый дворец
            "base_price": 1800,
            "max_price": 5500
        },
        {
            "title": "Фестиваль 'Усадьба Jazz'",
            "description": "Ежегодный фестиваль под открытым небом с участием российских и зарубежных исполнителей.",
            "image_url": "https://i.imgur.com/VnWcQ5c.jpg",
            "date": (datetime.now() + timedelta(days=45)).strftime("%Y-%m-%d %H:%M"),
            "category_id": 4,  # Фестивали
            "venue_id": 5,  # Экспоцентр
            "base_price": 3500,
            "max_price": 7000
        },
        {
            "title": "Детское шоу 'Маша и Медведь'",
            "description": "Интерактивное представление для детей по мотивам любимого мультфильма.",
            "image_url": "https://i.imgur.com/8GkGoYJ.jpg",
            "date": (datetime.now() + timedelta(days=12)).strftime("%Y-%m-%d %H:%M"),
            "category_id": 5,  # Детские
            "venue_id": 2,  # СК Олимпийский
            "base_price": 1200,
            "max_price": 3000
        },
        {
            "title": "Выставка 'Современное искусство России'",
            "description": "Экспозиция работ современных российских художников разных направлений.",
            "image_url": "https://i.imgur.com/Prlnl7T.jpg",
            "date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d %H:%M"),
            "end_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M"),
            "category_id": 6,  # Выставки
            "venue_id": 5,  # Экспоцентр
            "base_price": 500,
            "max_price": 1500
        },
        {
            "title": "Stand-Up концерт Нурлана Сабурова",
            "description": "Новая программа одного из самых популярных комиков России.",
            "image_url": "https://i.imgur.com/jx5r0TK.jpg",
            "date": (datetime.now() + timedelta(days=25)).strftime("%Y-%m-%d %H:%M"),
            "category_id": 1,  # Концерты
            "venue_id": 2,  # СК Олимпийский
            "base_price": 2000,
            "max_price": 6000
        },
        {
            "title": "Спектакль 'Мастер и Маргарита'",
            "description": "Театральная постановка по знаменитому роману Михаила Булгакова.",
            "image_url": "https://i.imgur.com/GTQtUlB.jpg",
            "date": (datetime.now() + timedelta(days=9)).strftime("%Y-%m-%d %H:%M"),
            "category_id": 2,  # Театры
            "venue_id": 4,  # Театр им. Вахтангова
            "base_price": 2200,
            "max_price": 5500
        }
    ]
    
    # Слайды для главной страницы
    slides = [
        {
            "title": "Летний фестиваль музыки",
            "subtitle": "Более 50 исполнителей на 4 сценах",
            "image_url": "https://i.imgur.com/XqXh3L1.jpg",
            "button_text": "Купить билет",
            "button_url": "/events?category=4",
            "order": 1
        },
        {
            "title": "Театральный сезон открыт!",
            "subtitle": "Премьеры лучших постановок",
            "image_url": "https://i.imgur.com/H6K26hR.jpg",
            "button_text": "Афиша",
            "button_url": "/events?category=2",
            "order": 2
        },
        {
            "title": "Спортивные события года",
            "subtitle": "Не пропустите решающие матчи сезона",
            "image_url": "https://i.imgur.com/N88AKUn.jpg",
            "button_text": "Билеты онлайн",
            "button_url": "/events?category=3",
            "order": 3
        }
    ]
    
    return {
        "categories": categories,
        "venues": venues,
        "events": events,
        "slides": slides
    }

def import_to_db(data):
    with app.app_context():
        try:
            # Очищаем существующие данные (если запускаем импорт повторно)
            # Важно соблюдать порядок удаления из-за внешних ключей
            print("Очистка существующих данных...")
            db.session.query(Event).delete()
            db.session.query(Slide).delete()
            db.session.query(Venue).delete()
            db.session.query(Category).delete()
            db.session.commit()
            
            print("Импорт категорий...")
            # Создаем словарь для хранения соответствия индексов и реальных ID категорий
            category_id_map = {}
            for i, cat_data in enumerate(data["categories"], 1):
                category = Category(
                    name=cat_data["name"],
                    icon=cat_data["icon"],
                    seo_title=f"Билеты на {cat_data['name'].lower()} - MAGIK TIKET",
                    seo_description=f"Купить билеты на {cat_data['name'].lower()} по выгодным ценам на MAGIK TIKET. Большой выбор мероприятий."
                )
                db.session.add(category)
                db.session.flush()  # Получаем ID без коммита
                category_id_map[i] = category.id
                
            # Сохраняем категории
            db.session.commit()
            print(f"Категории импортированы, маппинг ID: {category_id_map}")
            
            print("Импорт площадок...")
            # Создаем словарь для хранения соответствия индексов и реальных ID площадок
            venue_id_map = {}
            for i, venue_data in enumerate(data["venues"], 1):
                venue = Venue(
                    name=venue_data["name"],
                    address=venue_data["address"],
                    city=venue_data["city"]
                )
                db.session.add(venue)
                db.session.flush()  # Получаем ID без коммита
                venue_id_map[i] = venue.id
                
            # Сохраняем площадки
            db.session.commit()
            print(f"Площадки импортированы, маппинг ID: {venue_id_map}")
            
            print("Импорт событий...")
            for event_data in data["events"]:
                # Используем маппинг для получения актуальных ID
                real_category_id = category_id_map[event_data["category_id"]]
                real_venue_id = venue_id_map[event_data["venue_id"]]
                
                # Получаем название площадки из словаря venues по индексу
                venue_name = data['venues'][event_data['venue_id']-1]['name']
                
                event = Event(
                    title=event_data["title"],
                    description=event_data["description"],
                    image_url=event_data["image_url"],
                    date=datetime.strptime(event_data["date"], "%Y-%m-%d %H:%M"),
                    end_date=datetime.strptime(event_data["end_date"], "%Y-%m-%d %H:%M") if "end_date" in event_data else None,
                    category_id=real_category_id,  # Используем актуальный ID категории
                    venue_id=real_venue_id,  # Используем актуальный ID площадки
                    base_price=event_data["base_price"],
                    max_price=event_data["max_price"],
                    is_active=True,
                    seo_title=f"{event_data['title']} - купить билеты на MAGIK TIKET",
                    seo_description=f"Билеты на {event_data['title']}. Дата: {event_data['date']}. Место: {venue_name}. Купить онлайн на MAGIK TIKET."
                )
                db.session.add(event)
            db.session.commit()
            
            print("Импорт слайдов...")
            for slide_data in data["slides"]:
                slide = Slide(
                    title=slide_data["title"],
                    subtitle=slide_data["subtitle"],
                    image_url=slide_data["image_url"],
                    button_text=slide_data["button_text"],
                    button_url=slide_data["button_url"],
                    order=slide_data["order"],
                    is_active=True
                )
                db.session.add(slide)
            db.session.commit()
            
            print("Импорт данных успешно завершен!")
            
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка при импорте данных: {e}")

if __name__ == "__main__":
    # Пытаемся получить данные с сайта
    html_content = scrape_magiktiket()
    
    # Если не удалось получить данные с сайта, используем подготовленные примеры
    if not html_content:
        print("Не удалось получить данные с сайта, используем примерные данные")
        data = create_sample_data()
        import_to_db(data)
    else:
        # Здесь был бы код для парсинга HTML и извлечения данных
        print("Данные с сайта получены, но требуется парсинг HTML")
        # В данном случае все равно используем примерные данные
        data = create_sample_data()
        import_to_db(data)