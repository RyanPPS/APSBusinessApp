"""Forms for the APSBusinessApp application."""
from flask_wtf import Form
from wtforms import TextField, PasswordField, SelectField
from wtforms.validators import DataRequired


class LoginForm(Form):
    """Form class for user login."""
    email = TextField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])