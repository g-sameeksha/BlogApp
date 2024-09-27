from flask import Flask, render_template, redirect, url_for, request,flash
from flask_bootstrap import Bootstrap5, Bootstrap
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy import Integer, String, Text ,ForeignKey
from flask_ckeditor import CKEditor, CKEditorField
from datetime import date
from forms import BlogNewPost,RegisterForm,LoginForm,CommentForm
from werkzeug.security import check_password_hash,generate_password_hash
from flask_login import UserMixin,login_user,login_required,logout_user,current_user,LoginManager
# from flask_gravatar import Gravatar
from hashlib import md5

from dotenv import load_dotenv
import os

load_dotenv()
# from flask import abort
# from functools import wraps
'''
Make sure the required packages are installed: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from the requirements.txt for this project.
'''



app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("FLASK_KEY")

Bootstrap5(app)
ckeditor = CKEditor(app)


# CREATE DATABASE
class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URI', 'sqlite:///posts.db')
db = SQLAlchemy(model_class=Base)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

# CONFIGURE TABLE
class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    author_id : Mapped[int] = mapped_column(Integer,db.ForeignKey("users.id"))
    author = relationship("User",back_populates="posts")

    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    # author: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

    comments = relationship("Comment", back_populates="parent_post")


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))
    posts = relationship("BlogPost",back_populates="author")

    # *******Add parent relationship*******#
    # "comment_author" refers to the comment_author property in the Comment class.
    comments = relationship("Comment", back_populates="comment_author")


class Comment(db.Model):
    __tablename__ = "comments"
    id : Mapped[int] = mapped_column(Integer,primary_key=True)
    # *******Add child relationship*******#
    # "users.id" The users refers to the tablename of the Users class.
    # "comments" refers to the comments property in the User class.
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("users.id"))
    comment_author = relationship("User", back_populates="comments")

    post_id: Mapped[int] = mapped_column(Integer, db.ForeignKey("blog_posts.id"))
    parent_post = relationship("BlogPost", back_populates="comments")
    text: Mapped[str] = mapped_column(Text, nullable=False)


with app.app_context():
    db.create_all()


# def admin_only(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         # If id is not 1 then return abort with 403 error
#         if current_user.id != 1:
#             return abort(403)
#         # Otherwise continue with the route function
#         return f(*args, **kwargs)
#
#     return decorated_function
#
# gravatar = Gravatar(app,
#                     size=100,
#                     rating='g',
#                     default='retro',
#                     force_default=False,
#                     force_lower=False,
#                     use_ssl=False,
#                     base_url=None)

def avatar(email):
   digest = md5(email.lower().encode('utf-8')).hexdigest()
   return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={100}'



@app.route('/')
def get_all_posts():
    # TODO: Query the database for all the posts. Convert the data to a python list.

    posts = []
    queryset = db.session.execute(db.select(BlogPost))
    queryset = queryset.scalars().all()
    for query in queryset:
        posts.append(query)
    print(posts)
    return render_template("index.html", all_posts=posts,current_user=current_user)


# TODO: Add a route so that you can click on individual posts.
@app.route('/post/<int:post_id>',methods =["GET","POST"])
def show_post(post_id):
    # TODO: Retrieve a BlogPost from the database based on the post_id
    requested_post = db.get_or_404(BlogPost, post_id)
    form = CommentForm()
    commentset = db.session.execute(db.select(Comment))
    commentset = commentset.scalars().all()
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment on posts")
            return redirect(url_for("login"))
        new_comment = Comment(
            text=form.comment_text.data,
            comment_author=current_user,
            parent_post=requested_post
        )
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('show_post',post_id=post_id))

    return render_template("post.html", post=requested_post,form=form,comments = commentset,avatar=avatar)


# TODO: add_new_post() to create a new blog post
@app.route('/new-post', methods=["GET", "POST"])
@login_required
def add_new_post():
    form = BlogNewPost()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y"),
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('get_all_posts'))
    return render_template("make-post.html", form=form,current_user=current_user)


# TODO: edit_post() to change an existing blog post
@app.route('/edit-post/<post_id>', methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = db.get_or_404(BlogPost, post_id)
    edit_form = BlogNewPost(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.body = edit_form.body.data
        post.img_url = edit_form.img_url.data
        post.author = current_user
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", is_edit=True, form=edit_form,current_user=current_user)


# TODO: delete_post() to remove a blog post from the database
@app.route('/delete-post/<post_id>')
@login_required
def delete_post(post_id):

    post = db.get_or_404(BlogPost,post_id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for("get_all_posts"))

# Below is the code from previous lessons. No changes needed.
@app.route("/about")

def about():
    return render_template("about.html",current_user=current_user)


@app.route("/contact")

def contact():
    return render_template("contact.html",current_user=current_user)

@app.route("/register",methods = ["GET","POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email = form.email.data).first() :
            flash("Account with that email already exists.please login","error")
            return redirect(url_for('login'))
        salted_hashed_password = generate_password_hash(form.password.data,method='pbkdf2:sha256',salt_length=8)
        user = User(
            name = form.name.data,
            email =  form.email.data,
            password = salted_hashed_password
        )
        db.session.add(user)
        db.session.commit()
        flash("Account created Successfully","success")
        return redirect(url_for('register'))

    return render_template("register.html",form = form)


@app.route("/login",methods=["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        result = db.session.execute(db.select(User).where(User.email == form.email.data))
        user = result.scalar()

        if not user:
            flash("That email does not exist, please try again", "error")
            return redirect(url_for('login'))

        password = form.password.data
        if check_password_hash(user.password , password):
            login_user(user)
            return redirect(url_for('get_all_posts'))
        else :
            flash('Invalid password. Please try again.')
            return redirect(url_for('login'))

    return render_template("login.html",form = form,logged_in = current_user.is_authenticated)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))

if __name__ == "__main__":
    app.run(debug=False, port=5003)

    # from functools import wraps
    # from flask import abort
    #
    #
    # # Create admin-only decorator
    # def admin_only(f):
    #     @wraps(f)
    #     def decorated_function(*args, **kwargs):
    #         # If id is not 1 then return abort with 403 error
    #         if current_user.id != 1:
    #             return abort(403)
    #         # Otherwise continue with the route function
    #         return f(*args, **kwargs)
    #
    #     return decorated_function
