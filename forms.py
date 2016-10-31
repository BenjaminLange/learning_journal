from flask_wtf import FlaskForm
from wtforms import (StringField, DateField, TextAreaField,
                     PasswordField, IntegerField)
from wtforms.validators import DataRequired, Email, EqualTo


class EntryForm(FlaskForm):
    title = StringField(validators=[DataRequired()])
    date = DateField(validators=[DataRequired()])
    time = IntegerField(validators=[DataRequired()])
    learned = TextAreaField()
    resources = TextAreaField()
    tags = StringField()


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField(validators=[DataRequired()])


class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), EqualTo('password2')])
    password2 = PasswordField('Confirm Password', validators=[DataRequired()])
