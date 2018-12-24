from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = '5d25e8718669fca6e5fdccd3d0eca422'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:dfkblfwbz@139.59.183.169:5432/postgres'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Необходимо войти в систему'
login_manager.login_message_category = 'info'

from webinterface import routes
