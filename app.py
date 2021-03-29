from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
from models import *
migrate = Migrate(app,db)

from core.views import core_bp
app.register_blueprint(core_bp)

from api.views import api_bp
app.register_blueprint(api_bp, url_prefix='/api')
