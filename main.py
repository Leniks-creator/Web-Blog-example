from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hrumstik_59_098123'

login_manager = LoginManager(app)
login_manager.login_view = 'login'

connection = sqlite3.connect("sqlite.db", check_same_thread=False)
cursor = connection.cursor()


class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    user = cursor.execute('SELECT * FROM user WHERE user_id = ?', (user_id,)).fetchone()
    if user is not None:
        return User(user[0], user[1], user[2])
    return None


def close_db(connection=None):
    if connection is not None:
        connection.close()


@app.teardown_appcontext
def close_connection(exception):
    close_db()


@app.route("/detroit/")
def detroit():
    return render_template("detroit.html")


@app.route("/minecraft/")
def minecraft():
    return render_template("mine.html")


@app.route("/")
def index():
    cursor.execute("SELECT posts.id,posts.title,posts.text,posts.author,user.username, COUNT(like.id) AS likes FROM posts JOIN user ON posts.author = user.user_id LEFT JOIN like ON posts.id = like.post_id GROUP BY posts.id, posts.title, posts.text, posts.author, user.username")
    result = cursor.fetchall()
    posts = []
    for post in reversed(result):
        posts.append({'id': post[0], 'title': post[1], 'text': post[2], 'author': post[3], 'username': post[4], 'likes': post[5]})
        if current_user.is_authenticated:
            cursor.execute('SELECT post_id FROM like WHERE user_id = ?', (current_user.id,))
            liked_result = cursor.fetchall()
            liked_posts = []
            for like in liked_result:
                liked_posts.append(like[0])
            posts[-1] ['liked_posts'] = liked_posts
    context = {'posts': posts}
    return render_template("index.html", **context)


@app.route("/add_post/", methods=['GET', 'POST'])
@login_required
def add_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        author = current_user.id
        cursor.execute("INSERT INTO posts (author, title, text) VALUES (?,?,?)", (author, title, content))
        connection.commit()
        return redirect(url_for('index'))
    return render_template("add_post.html")


@app.route("/post/<post_id>")
def post(post_id):
    result = cursor.execute("SELECT * from posts WHERE id =?", post_id).fetchone()
    post_dict = {'id': result[0], 'author': result[3], 'title': result[1], 'text': result[2]}
    return render_template('post.html', post=post_dict)


@app.route("/authorization/", methods=['GET', 'POST'])
def authorization():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        try:
            cursor.execute("INSERT INTO user (username, password_hash) VALUES (?,?)",
                           (username, generate_password_hash(password),))
            connection.commit()
            print('Регистрация прошла успешно!')
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            return render_template('register.html', message='Данное имя пользоваетеля уже занято, выберите другое!')
    return render_template('register.html')


@app.route("/login/", methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        user = cursor.execute('SELECT * FROM user WHERE username = ?', (username,)).fetchone()
        if user and User(user[0], user[1], user[2]).check_password(password):
            login_user(User(user[0], user[1], user[2]))
            return redirect(url_for('index'))
        else:
            return render_template('login.html', message='Неверное имя или пароль')
    return render_template('login.html')


@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route("/del_post/<int:post_id>", methods=['POST'])
@login_required
def del_post(post_id):
    post = cursor.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    print(post, current_user.id)
    if post and post[3] == current_user.id:
        cursor.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        connection.commit()
        return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))
def user_is_liking(user_id, post_id):
    like = cursor.execute('SELECT * FROM like WHERE user_id = ? AND post_id = ?', (user_id, post_id)).fetchone()
    return bool(like)

@app.route('/like/<int:post_id>')
@login_required
def like_post(post_id):
    post = cursor.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    if post:
        if user_is_liking(current_user.id, post_id):
            cursor.execute('DELETE FROM like WHERE user_id = ? AND post_id = ?', (current_user.id, post_id))
            connection.commit()
            #Убрал лайк👎
        else:
            cursor.execute('INSERT INTO like (user_id, post_id) VALUES (?,?)', (current_user.id, post_id))
            connection.commit()
            #Поставил лайк👍
        return redirect(url_for('index'))
    return 'Post not found', 404


if __name__ == "__main__":
    app.run()