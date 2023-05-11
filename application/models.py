from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from application import db, manager



@manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# описываем модели
class Cart(db.Model):
    __tablename__ = 'Cart'
    __table_args__ = {'schema': 'Market_schem'}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    size = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    product_name = db.Column(db.String(50), nullable=False)
    product_brand = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Integer, nullable=False)

# размеры
class Sizes(db.Model): 
    __tablename__ = 'Sizes'
    __table_args__ = {'schema': 'Market_schem'}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

# брэнды
class Brands(db.Model): 
    __tablename__ = 'Brands'
    __table_args__ = {'schema': 'Market_schem'}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False )

class Category(db.Model):
    __tablename__ = 'Category'
    __table_args__ = {'schema': 'Market_schem'}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)

class Color(db.Model):
    __tablename__ = 'Color'
    __table_args__ = {'schema': 'Market_schem'}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)

#класс юзер наследует UserMixin для работы с flask-login
class User(UserMixin, db.Model):
    __tablename__ = 'Users'
    __table_args__ = {'schema': 'Market_schem'}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    login = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)

    #функция для получения пароля
    def get_id(self):
        return str(self.id)

    #сравнение хэшей пароля
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    #шифрование пароля с использованием веб-сервиса werkzeug.security
    @staticmethod
    def hash_password(password):
        return generate_password_hash(password) 

# склад
class Storage(db.Model):
    __tablename__ = 'Storage'
    __table_args__ = {'schema': 'Market_schem'}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_id = db.Column(db.Integer, db.ForeignKey("Products.id"), nullable=False)
    size = db.Column(db.String(50), db.ForeignKey("Sizes.name"), nullable=False)
    purchase_id = db.Column(db.Integer, db.ForeignKey("Purchase.id"), nullable=False)

# закупки
class Purchase(db.Model):
    __tablename__ = 'Purchase'
    __table_args__ = {'schema': 'Market_schem'}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey("Products.id"), nullable=False)
    total_price = db.Column(db.Integer)
    quantity = db.Column(db.Integer)
    price_per_unit = db.Column(db.Integer)
    # price_per_unit =total_price // quantity

# карточка товара
class Products(db.Model):
    __tablename__ = 'Products'
    __table_args__ = {'schema': 'Market_schem'}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    brand = db.Column(db.String(50), db.ForeignKey("Brands.name"), nullable=False)
    category = db.Column(db.String(50), db.ForeignKey("Category.name"), nullable=False)
    color = db.Column(db.String(50), db.ForeignKey("Color.name"), nullable=False)
    description = db.Column(db.String(100000))
    img_url = db.Column(db.String(100000), unique=True)
    price = db.Column(db.Integer, nullable=False)
    discount = db.Column(db.Integer)
    click = db.Column(db.Integer)


# статус заказа
class OrderStatus(db.Model):
    __tablename__ = 'OrderStatus'
    __table_args__ = {'schema': 'Market_schem'}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    status_name = db.Column(db.String(50), nullable=False, unique=True)

# заказ
class Order(db.Model):
    __tablename__ = 'Order'
    __table_args__ = {'schema': 'Market_schem'}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    addres = db.Column(db.String(50), nullable=False)
    order_data = db.Column(db.DateTime)
    check_sum = db.Column(db.Integer)
    status_name = db.Column(db.String(50), nullable=False, default='Ожидает оплату')

# товар в заказе
class Order_items(db.Model):
    __tablename__ = 'Order_items'
    __table_args__ = {'schema': 'Market_schem'}
    order_id = db.Column(db.Integer, db.ForeignKey("Order.id"), nullable=False)
    item_id = db.Column(db.Integer, nullable=False, unique=True)
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.Integer, db.ForeignKey("Order.id"), nullable=False)