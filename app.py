from flask import Flask, render_template, flash, request, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, ValidationError
from wtforms.validators import DataRequired, EqualTo, Length
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from wtforms.widgets import TextArea
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user

#create a Flask Instance
app = Flask(__name__)
# Add Database

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = "my super secret key"

# initialize the database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Flask_Login Stuff
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


# Create login Form
class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Submit")

#Create Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user:
            # Check the hash
            if check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                flash("Login Succesfull!!!")
                return redirect (url_for('dashboard'))
            else: 
                flash("Wrong Password - Try Again!")
        else: 
            flash("That User Doesn't Exist! Try Again!")
    return render_template('login.html', form=form)

# Create Logout Page
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash("You Have Been Logged Out! Thanks")
    return redirect(url_for('login'))

#create Dashboard Page
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    form = UserForm()
    id = current_user.id
    name_to_update = Users.query.get_or_404(id)
    if request.method == "POST":
        name_to_update.name = request.form['name']
        name_to_update.email = request.form['email']
        name_to_update.favorite_color = request.form['favorite_color']
        name_to_update.username = request.form['username']
        try:
            db.session.commit()
            flash("User Update Successfully!")
            return render_template("dashboard.html",
                    form = form,
                    name_to_update = name_to_update)
        except: 
            flash("Error There was a problem... Try again!")
            return render_template("dashboard.html",
                    form = form,
                    name_to_update=name_to_update)
    else: 
        return render_template("dashboard.html",
                form = form,
                name_to_update=name_to_update,
                id = id)
   
    return render_template('dashboard.html')

# Create a Blog Post Model
class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    #content = db.Column(db.Text)
    #author = db.Column(db.String(255))
    date_posted = db.Column(db.DateTime, default=datetime.now().replace(microsecond=0))
    #slug = db.Column(db.String(255)) 
    # Foreign Key to Link Users (refer to primary)
    poster_id = db.Column(db.Integer, db.ForeignKey('users.id'))

#Create a Post Form
class PostForm(FlaskForm):
    title = StringField("Note", validators=[DataRequired()])
    """ content = StringField("Content",validators=[DataRequired()], widget= TextArea() )
    author = StringField("Autor")
    slug = StringField("Slug", validators=[DataRequired()]) """
    submit = SubmitField("Submit")

@app.route('/posts/delete/<int:id>')
@login_required
def delete_post(id):
    post_to_delete = Posts.query.get_or_404(id)

    try:
        db.session.delete(post_to_delete)
        db.session.commit()
        flash ("Blog Post Was Deleted!")

        # Grab all the posts from the database
        posts = Posts.query.filter(Posts.poster_id == current_user.id)
        return render_template("posts.html", posts=posts)
    except: 
        # return an error
        flash("There was a problem deleting post, try again")
        # Grab all the posts from the database
        posts = Posts.query.order_by(Posts.date_posted)
        return render_template("posts.html", posts=posts)

@app.route('/posts')
@login_required
def posts():  
    
    
    # Grab all the posts from the database
    posts = Posts.query.filter(Posts.poster_id == current_user.id)
    return render_template("posts.html", posts=posts)

@app.route('/posts/<int:id>')

def post(id):
    post = Posts.query.get_or_404(id)
    return render_template('post.html', post=post)

@app.route('/posts/edit/<int:id>', methods=['GET', 'POST'])
def edit_post(id):
    post = Posts.query.get_or_404(id)
    form = PostForm()
    if form.validate_on_submit():
        """ post.title = form.title.data
        post.content=form.content.data
        #post.author=form.author.data
        post.slug=form.slug.data """

        # Update database 
        db.session.add(post)
        db.session.commit()
        flash ("Post has Been Updated!")
        return redirect(url_for('post', id=post.id))
    
    form.title.data = post.title
    """ #form.author.data = post.author
    form.slug.data = post.slug
    form.content.data = post.content """

    return render_template ("edit_post.html", form=form)

@app.route('/add-post', methods=['GET', 'POST'])
@login_required
def add_post():
    form = PostForm()
    
    if form.validate_on_submit():
        poster = current_user.id
        post = Posts(title=form.title.data, poster_id=poster)

        #Clear de Form
        form.title.data= ''
        """ form.content.data= ''
        #form.author.data=''
        form.slug.data='' """

        # Add post data to database
        db.session.add(post)
        db.session.commit()

        #Return a Message
        flash("Blog Post Successfully!")

    # Redirect to the webpage
    return render_template("add_post.html", form = form)

# Create Model
class Users(db.Model, UserMixin):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    #favorite_color = db.Column(db.String(120))
    date_added = db.Column(db.DateTime, default=datetime.now().replace(microsecond=0))
    # do some passaword stuff!
    password_hash = db.Column(db.String(128))
    # User Can Have Many Posts
    posts = db.relationship('Posts', backref='poster')

    @property
    def password(self):
        raise AttributeError('password os not a readable attribute!')

    @password.setter
    def password(self, password):
        password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    #Create a String
    def __repr__(self):
        return '<Name %r>' % self.name
    
@app.route('/delete/ <int:id>')
def delete(id):
    user_to_delete = Users.query.get_or_404(id)
    name = None
    form = UserForm()

    try:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash("User Deleted Successfully!")
        our_users = Users.query.order_by(Users.date_added)
        return render_template("add_user.html",
             form = form,
             name=name,
             our_users=our_users )
    
    except:
        flash("There was a problem user, try again")
        return render_template("add_user.html",
             form = form,
             name=name,
             our_users=our_users )

# Create Form Class
class UserForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    #favorite_color = StringField("Favorite Color")
    password_hash = PasswordField('Password', validators=[DataRequired(), EqualTo('password_hash2', message= 'Passwords Must Match!')])
    password_hash2 = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField("Submit")

#Updade Database Record
@app.route('/updade/<int:id>', methods =['GET', 'POST'])

def update(id):
    form = UserForm()
    name_to_update = Users.query.get_or_404(id)
    if request.method == "POST":
        name_to_update.name = request.form['name']
        name_to_update.email = request.form['email']
        #name_to_update.favorite_color = request.form['favorite_color']
        name_to_update.username = request.form['username']
        try:
            db.session.commit()
            flash("User Update Successfully!")
            return render_template("updade.html",
                    form = form,
                    name_to_update = name_to_update)
        except: 
            flash("Error There was a problem... Try again!")
            return render_template("updade.html",
                    form = form,
                    name_to_update=name_to_update)
    else: 
        return render_template("updade.html",
                form = form,
                name_to_update=name_to_update,
                id = id)   

class PasswordForm(FlaskForm):
    email = StringField("What's Your Email", validators=[DataRequired()])
    password_hash = PasswordField("What's Your Password", validators=[DataRequired()])
    submit = SubmitField("Submit") 

# Create Form Class
class NamerForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Submit")    
# Create a route decorator

@app.route('/user/add', methods=['GET', 'POST'])
def add_user():
    name = None
    form = UserForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user is None:
            # Hash the passwor!!!
            hashed_pw = generate_password_hash (form.password_hash.data)
            user = Users(username=form.username.data, name=form.name.data, email=form.email.data,
            password_hash=hashed_pw)
            db.session.add(user)
            db.session.commit()
        name = form.name.data
        form.name.data = ''
        form.username.data = ''
        form.email.data = ''
        #form.favorite_color.data = ''
        form.password_hash.data = ''

        flash("User Added Successful")
    our_users = Users.query.order_by(Users.date_added)
    return render_template("add_user.html",
             form = form,
             name=name,
             our_users=our_users )


#def index():
#    return "<h1>Hello World!</h1>"
@app.route('/')
def index():

    return render_template("index.html")

#Create Custom Error Pages
#Ivalid URL

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def page_not_found(e):
    return render_template("500.html"), 500

#Create Password test Page
@app.route('/test_pw', methods=['GET', 'POST'])
def test_pw():
    email = None
    password = None
    pw_to_check = None
    passed = None
    form = PasswordForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password_hash.data
        #clear the form
        form.email.data = ''
        form.password_hash.data = ''

        # lookup User By Email Add Address
        pw_to_check = Users.query.filter_by(email=email).first()

        # Check Hashed Password
        passed=check_password_hash(pw_to_check.password_hash, password)
        
    return render_template("test_pw.html", 
        email = email,
        password=password,
        pw_to_check=pw_to_check,
        passed = passed,
        form = form)




if __name__ == '__main__':
    app.run (debug=True)