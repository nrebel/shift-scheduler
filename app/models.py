from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Boolean, Column, Integer, String, inspect
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from . import db, login_manager  # Import db instance from the application package

Base = declarative_base()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(200))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {}>'.format(self.username)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Event(db.Model):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True)
    title = Column(String(80), nullable=False)
    description = Column(String(200))

    def __repr__(self):
        return '<Event {}>'.format(self.title)

class ShiftTableMeta(type):
    def __new__(cls, year, month):
        table_name = f"shift_preferences_{year}_{month}"
        num_days = (datetime(year, month % 12 + 1, 1) - datetime(year, month, 1)).days
        attrs = {
            '__tablename__': table_name,
            '__table_args__': {'extend_existing': True},
            'id': Column(Integer, primary_key=True),
            'username': Column(String(100), unique=True),
            'month': Column(Integer, default=month),
            'year': Column(Integer, default=year),
            'min_shifts': Column(Integer, default=0),
            'max_shifts': Column(Integer, default=num_days),
            **{f"day_{i+1}": Column(Boolean, default=False) for i in range(num_days)}
        }
        model = type(table_name, (db.Model,), attrs)
        
        # Use inspect to safely check for table existence within the current app context
        with current_app.app_context():
            inspector = inspect(db.engine)
            if not inspector.has_table(table_name):
                model.__table__.create(db.engine)  # Create the table if it doesn't exist
                
        return model

def get_shift_model(year, month):
    return ShiftTableMeta(year, month)

def initialize_shift_table(model, username, year, month, true_days, minshifts, maxshifts):
    existing_entry = model.query.filter_by(username=username, year=year, month=month).first()
    if existing_entry is None:
        new_entry = model(username=username, year=year, month=month, min_shifts=minshifts, max_shifts=maxshifts)
        db.session.add(new_entry)
    else:
        new_entry = existing_entry

    # Reset all days to False initially
    num_days = (datetime(year, month % 12 + 1, 1) - datetime(year, month, 1)).days
    for day in range(1, num_days):  # assuming maximum days in any month is 31
        setattr(new_entry, f'day_{day}', False)

    # Set true days
    for day in true_days:
        setattr(new_entry, f'day_{day}', True)

    setattr(new_entry, 'min_shifts', minshifts)
    setattr(new_entry, 'max_shifts', maxshifts)

    db.session.commit()
