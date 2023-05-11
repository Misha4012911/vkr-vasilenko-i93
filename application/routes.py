from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Blueprint
from flask_login import login_user, logout_user, login_required, current_user
from flask_paginate import Pagination, get_page_parameter
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from application.models import *
from application import app, db
from sqlalchemy import or_, text, and_
from sqlalchemy.exc import SQLAlchemyError


# узнать размеры товара в наличии
def get_size(product_id):
    sizes = Storage.query.filter_by(item_id=product_id).with_entities(Storage.size).all()
    if not sizes:
        return "Товара нет в наличии"
    else:
        return f"Размеры товара: {', '.join([size[0] for size in sizes])}"

# инкремент кликов для отслеживания популярности товара
def increment_click(product_id):
    # Обновляем значение поля click для записи где id = product_id
    db.session.query(Products).filter(Products.id == product_id).update({Products.click: Products.click + 1})

    # Сохраняем изменения в базе данных
    db.session.commit()

# страница товара
@app.route('/product/<int:product_id>')
def product(product_id):
    increment_click(product_id) # вызываю функцию инкремента кликов
    # код для получения информации о товаре по его идентификатору
    product = Products.query.get(product_id)
    model = Storage.query.filter_by(item_id=product_id).all()
    sizes = Sizes.query.all()
    storage = get_size(product_id)
    size_lst = []
    app.jinja_env.globals['count_available_items'] = count_available_items
    
    for size in sizes:
        if size.name in storage and size.name not in size_lst:
            size_lst.append(size.name)
        size_lst=sorted(size_lst)

    return render_template('product.html', product=product, storage=storage, 
                           model=model,size_lst=size_lst,count_available_items=count_available_items)

# функция добавления товара в корзину 
@app.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    # Получаем данные товара из запроса
    prod_id = request.form['prod_id']
    prod_price = request.form['prod_price']
    prod_name = request.form['prod_name']
    prod_brand = request.form['prod_brand']
    size_inf = request.form['size_inf']
    quantity_inf = request.form['quantity_inf']

   # Проверяем, есть ли товар уже в корзине
    cart_item = Cart.query.filter_by(user_id=current_user.id, product_id=prod_id, size=size_inf).first()
    if cart_item:
    # Если товар уже есть в корзине, увеличиваем его количество на указанное значение
        cart_item.quantity += int(quantity_inf)
    else:
    # Если товара еще нет в корзине, добавляем его в корзину
        cart_item = Cart(user_id=current_user.id, product_id=prod_id, size=size_inf, 
                    quantity=int(quantity_inf), price=prod_price, product_name=prod_name, 
                    product_brand=prod_brand)
        db.session.add(cart_item)

    # Сохраняем изменения в базе данных
    db.session.commit()

    flash('Товар добавлен в корзину')
    return redirect(url_for('cart'))

# удаление из корзины товаров
@app.route('/remove_from_cart/<int:cart_id>', methods=['POST'])
@login_required
def remove_from_cart(cart_id):
    cart_item = Cart.query.get_or_404(cart_id)
    db.session.delete(cart_item)
    db.session.commit()
    flash('Товар удален из корзины')
    return redirect(url_for('cart'))

# страница корзины
@app.route('/cart', methods=['POST', 'GET'])
@login_required
def cart():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    total=total_price()
    all_available = all(count_available_items(item.size, item.product_id) >= item.quantity for item in cart_items)
    # Добавляем функцию count_available_items в глобальный контекст шаблона
    app.jinja_env.globals['count_available_items'] = count_available_items

    return render_template('cart.html',cart_items=cart_items, total=total,all_available=all_available)

# декремент количества товара
@app.route('/decrease_cart_item_quantity/<int:cart_id>', methods=['POST'])
def decrease_cart_item_quantity(cart_id):
    cart_item = Cart.query.get(cart_id)
    if cart_item:
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            db.session.commit()
        else:
            db.session.delete(cart_item)
            db.session.commit()
    return redirect(url_for('cart'))

# инкремент количества товара
@app.route('/increase_cart_item_quantity/<int:cart_id>', methods=['POST'])
def increase_cart_item_quantity(cart_id):
    cart_item = Cart.query.get(cart_id)
    if cart_item:
        cart_item.quantity += 1
        db.session.commit()
    return redirect(url_for('cart'))

# подсчет количества товара одной модели одного размера в БД
def count_available_items(size, item_id):
    # Получаем список item_id из таблицы Order_items
    ordered_items = [item.item_id for item in Order_items.query.all()]
    # Считаем количество записей в таблице Storage, удовлетворяющих заданным условиям
    count = Storage.query.filter_by(size=size, item_id=item_id).filter(Storage.id.notin_(ordered_items)).count()
    return count

# подсчет полной стоимости корзины
def total_price():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    total = 0
    for item in cart_items:
        total = total + item.price * item.quantity
    return total

# регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('logout'))
    if request.method == 'POST':
        name = request.form['name']
        login = request.form['login']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        email = request.form['email']
        user = User.query.filter((User.login==login) | (User.email==email)).first()

        if password != confirm_password:
            flash('Пароли не совпадают')
        elif user:
            flash('Логин или Email заняты')
        else:
            new_user = User(name=name, login=login, password_hash=generate_password_hash(password), email=email)
            db.session.add(new_user)
            db.session.commit()
            flash('Вы успешно зарегистрировались!')
            return redirect(url_for('login'))
    return render_template('register.html')

# авторизация 
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']

        user = User.query.filter_by(login=login).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Вы успешно авторизовались!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Ошибка авторизации', 'danger')

    return render_template('login.html')

#выход и учетки
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

#личный кабинет
@app.route('/dashboard')
@login_required
def dashboard():
    orders = Order.query.filter(Order.user_id == current_user.id).order_by(Order.id.desc()).all()
    return render_template('dashboard.html', orders=orders)

# главная страница
@app.route('/')
def index():
    brands = Brands.query.all()
    categorys = Category.query.all()
    products = Products.query.order_by(Products.click.desc()).all() # сортировка по количеству кликов
    return render_template('index.html', brands=brands, categorys=categorys, products=products)

# добавление заказа
@app.route('/add_order', methods=['POST', 'GET'])
def add_order():
    if request.method == 'POST':
        apart = request.form['apart']
        addres = ' '.join([request.form['addres'], 'квартира', apart])
        phone = request.form['phone']
        total = total_price()
        cart= Cart.query.filter_by(user_id=current_user.id).all()

        # добавляем номер телефона
        update_user_phone(id=current_user.id, phone=phone)
        # Создаем объект модели Order
        new_order = Order(user_id=current_user.id, addres=addres, order_data=datetime.now(), check_sum=total)
        # Добавляем объект в сессию
        db.session.add(new_order)    
        # Сохраняем изменения в базе данных
        db.session.commit()

        #добавляем в заказ экземпляры модели и размера из корзины которые есть на складе 
        # for item in cart:
        #     storage = find_storage_id(item_id=item.product_id, size=item.size)
        #     order_item = Order_items(order_id= new_order.id, item_id=storage)
        #     db.session.add(order_item)
        
        return redirect(url_for('dashboard'))
    return render_template('order_form.html')


# Функция поиска записи в таблице Storage
def find_storage_id(item_id, size):
    # Ищем запись в таблице Storage по item_id и size, с условием что её id не встречается в Order_items.item_id
    storage = Storage.query.outerjoin(Order_items, Storage.item_id == Order_items.item_id).filter(Order_items.item_id == None).first()
    if storage:
        # Если запись найдена, возвращаем ее id
        return storage.id
    else:
        flash('Товара нет в наличии', 'danger')


# Функция обновления записи в таблице User
def update_user_phone(id, phone):
    # Получаем объект записи из таблицы User по id
    user = User.query.filter_by(id=id).first()
    # Обновляем значение поля phone
    user.phone = phone
    # Сохраняем изменения в базе данных
    db.session.commit()

# страница поиска
@app.route('/search')
def search():
    query = request.args.get('query')
    brands = Brands.query.all()
    categorys = Category.query.all()
    colors = Color.query.all()
    products = Products.query.order_by(Products.click).all() 
    if query:
        results = Products.query.filter(
            Products.name.ilike(f'%{query}%') | 
            Products.brand.ilike(f'%{query}%') |
            Products.category.ilike(f'%{query}%')
        )

        print(str(Products.query.filter(
            Products.name.ilike(f'%{query}%') | 
            Products.brand.ilike(f'%{query}%') |
            Products.category.ilike(f'%{query}%')
        ).statement))
        return render_template('search_results.html', results=results)

    else:
        return render_template('search.html', brands=brands, categorys=categorys, products=products, colors=colors)
    
# фильтрация
@app.route('/filter')
def filter():
    category = request.args.get('category')
    brand = request.args.get('brand')
    color = request.args.get('color')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price') 

    filters = []
    if category:
       filters.append(Products.category.ilike(f'%{category}%'))
    if brand:
       filters.append(Products.brand.ilike(f'%{brand}%'))
    if color:
       filters.append(Products.color.ilike(f'%{color}%'))
    if min_price:
       filters.append(Products.price >= int(min_price))
    if max_price:
       filters.append(Products.price <= int(max_price))

    if filters:
        results = Products.query.filter(and_(*filters)).all()
    else:
        results = Products.query.all()

    return render_template('search_results.html', results=results)


# эта функция удаляет все записи из корзины пользователя
def delete_cart_items():
    Cart.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()

# #добавление товара в бд
@app.route('/add_product', methods=['GET', 'POST'])
def add_product():    
    if current_user.login == 'admin':
        # Данные для списков
        brands = Brands.query.all()
        categorys = Category.query.all()
        colors = Color.query.all()

        if request.method == 'POST':
            # Получаем данные товара из запроса
            category = request.form['category']
            price = request.form['price']
            name = request.form['name']
            brand = request.form['brand']
            color = request.form['color']
            img_url = request.form['image']
            new_product = Products(name=name, price=price, category=category, brand=brand, color=color, img_url=img_url)
            db.session.add(new_product)
            db.session.commit()
            flash('Товар успешно добавлен')
            return redirect(url_for('product', product_id=new_product.id))

        return render_template('add_product.html', brands=brands, categorys=categorys, colors=colors)
    

    # try:
    # except:
    #     return redirect(url_for('index'))