
from app import app, db
from models import User
from werkzeug.security import generate_password_hash

def add_admins():
    admins = [
        {
            'email': 'sonik@magiktiket.com',
            'password': 'Yes14889!',
            'username': 'sonik'
        },
        {
            'email': 'temik@magiktiket.com', 
            'password': 'DVfev123##!@',
            'username': 'temik'
        },
        {
            'email': 'vit@magiktiket.com',
            'password': '!@wwe2Wit5',
            'username': 'vit'
        },
        {
            'email': 'vera@magiktiket.com',
            'password': 'V343#qw!w80',
            'username': 'vera'
        }
    ]

    with app.app_context():
        for admin_data in admins:
            # Проверяем существует ли пользователь
            user = User.query.filter_by(email=admin_data['email']).first()
            
            if not user:
                # Создаем нового админа
                user = User(
                    username=admin_data['username'],
                    email=admin_data['email'],
                    password_hash=generate_password_hash(admin_data['password']),
                    is_admin=True
                )
                db.session.add(user)
                print(f"Добавлен новый админ: {admin_data['email']}")
            else:
                # Обновляем существующего пользователя
                user.is_admin = True
                user.password_hash = generate_password_hash(admin_data['password'])
                print(f"Обновлен существующий админ: {admin_data['email']}")
        
        db.session.commit()
        print("Все администраторы успешно добавлены")

if __name__ == "__main__":
    add_admins()
