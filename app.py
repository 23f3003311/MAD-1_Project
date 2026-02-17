from flask import Flask
from flask_login import LoginManager
from config import Config
from models import db, User
from werkzeug.security import generate_password_hash
from routes import register_routes

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


with app.app_context():
    db.create_all()

    # Create admin if not exists
    if not User.query.filter_by(role="admin").first():
        admin = User(
            name="Admin",
            email="admin@portal.com",
            password_hash=generate_password_hash("admin123"),
            role="admin",
            approval_status="Approved"
        )
        db.session.add(admin)
        db.session.commit()

register_routes(app)

if __name__ == "__main__":
    app.run(debug=True)
