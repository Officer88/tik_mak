from app import app, db
from models import User

def make_admin():
    with app.app_context():
        user = User.query.filter_by(username="admin").first()
        print(f"Admin exists: {user is not None}, Is admin: {user.is_admin if user else None}")
        
        if user and not user.is_admin:
            user.is_admin = True
            db.session.commit()
            print("Admin role updated")
        elif not user:
            from werkzeug.security import generate_password_hash
            admin = User(username="admin", email="admin@example.com", 
                        password_hash=generate_password_hash("admin123"),
                        is_admin=True)
            db.session.add(admin)
            db.session.commit()
            print("Admin created")
        else:
            print("Admin already exists and has admin privileges")

if __name__ == "__main__":
    make_admin()
