from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message='Email je povinný')
    ])
    password = PasswordField('Heslo', validators=[
        DataRequired(message='Heslo je povinné')
    ])
    remember_me = BooleanField('Zapamatovat si mě')
    submit = SubmitField('Přihlásit se')

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message='Email je povinný'),
        Email(message='Neplatný email')
    ])
    password = PasswordField('Heslo', validators=[
        DataRequired(message='Heslo je povinné'),
        Length(min=8, message='Heslo musí mít alespoň 8 znaků')
    ])
    password2 = PasswordField('Potvrdit heslo', validators=[
        DataRequired(message='Potvrzení hesla je povinné'),
        EqualTo('password', message='Hesla se musí shodovat')
    ])
    submit = SubmitField('Registrovat se') 