from app import app, db
from app.models import User, get_shift_model
from flask_migrate import Migrate
import os

# Configuration based on the FLASK_ENV environment variable
if os.getenv('FLASK_ENV') == 'production':
    app.config.from_object('config.ProdConfig')
elif os.getenv('FLASK_ENV') == 'testing':
    app.config.from_object('config.TestConfig')
else:
    app.config.from_object('config.DevConfig')

migrate = Migrate(app, db)

#@app.before_first_request
def create_tables():
    with app.app_context():
        db.create_all()

if __name__ == "__main__":
    create_tables()
    app.run(host='0.0.0.0', port='1111')
