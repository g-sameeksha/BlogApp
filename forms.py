from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,PasswordField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditor, CKEditorField


class BlogNewPost(FlaskForm):
    title = StringField("Blog Title", validators=[DataRequired()])
    subtitle = StringField("SubTitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


class RegisterForm(FlaskForm):
    name = StringField("Your Name" , validators=[DataRequired()])
    email = StringField("Email ID",validators=[DataRequired()])
    password =  PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign Up")


class LoginForm(FlaskForm):
    email = StringField("Email ID", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log In")


class CommentForm(FlaskForm):
    comment_text = CKEditorField("Comments", validators=[DataRequired()])
    submit = SubmitField("Submit Comment")

