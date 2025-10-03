import sqlite3
from werkzeug.security import generate_password_hash


connection = sqlite3.connect("sqlite.db", check_same_thread=False)
cursor = connection.cursor()


cursor.execute('''CREATE TABLE like (id INTEGER PRIMARY KEY AUTOINCREMENT, post_id INTEGER NOT NULL, user_id INTEGER NOT NULL );''')

connection.commit()
connection.close()