from flask_wtf import FlaskForm
from wtforms import SelectField, BooleanField, StringField, PasswordField, SubmitField, IntegerField, SelectMultipleField, widgets, HiddenField
from wtforms.validators import  DataRequired, Length, EqualTo, ValidationError, NumberRange
from wtforms.fields import ColorField  # Import ColorField for HTML5 color input

from .models import User
import datetime  # Ensure you have this import

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me', default=True)
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    color = ColorField('Favorite Color', validators=[DataRequired()], default='#000000')

    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

class ShiftPreferenceForm(FlaskForm):
    min_shifts = IntegerField('Minimum Shifts', validators=[DataRequired(), NumberRange(min=0, max=31)],default=0)
    max_shifts = IntegerField('Maximum Shifts', validators=[DataRequired(), NumberRange(min=0, max=31)],default=31)
    month = IntegerField('Month', validators=[DataRequired()], default=datetime.datetime.now().month)
    year = IntegerField('Year', validators=[DataRequired()], default=datetime.datetime.now().year)
    selected_days = HiddenField('selectedDates')  # Captures the comma-separated list of selected dates
    submit = SubmitField('Submit Preferences')