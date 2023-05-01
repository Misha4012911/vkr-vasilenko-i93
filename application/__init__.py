from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_migrate import upgrade as _upgrade

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123@localhost/market'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secretkey'
db = SQLAlchemy(app)
manager = LoginManager(app)
# migrate = Migrate(app, db, schema='Market_schem')

# # добавление схемы для alembic_version таблицы
# with app.app_context():
#     migrate.init_app(app, db, render_as_batch=True, schema='Market_schem')
#     _upgrade(directory=migrate.directory, schema='Market_schem')