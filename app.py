from flask import Flask, render_template_string, request, redirect, url_for, flash, session
import os
import json
from datetime import datetime

app = Flask(__name__)
# Use environment variable for secret key in production
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

  # Change this in production!

# In-memory database (for demo purposes)
products = [
    {'id': 1, 'name': 'Laptop', 'price': 999.99, 'description': 'High-performance laptop', 'image': '💻', 'category': 'Electronics'},
    {'id': 2, 'name': 'Smartphone', 'price': 699.99, 'description': 'Latest smartphone', 'image': '📱', 'category': 'Electronics'},
    {'id': 3, 'name': 'Headphones', 'price': 149.99, 'description': 'Noise-cancelling headphones', 'image': '🎧', 'category': 'Electronics'},
    {'id': 4, 'name': 'T-Shirt', 'price': 19.99, 'description': 'Cotton t-shirt', 'image': '👕', 'category': 'Clothing'},
    {'id': 5, 'name': 'Coffee Mug', 'price': 12.99, 'description': 'Ceramic coffee mug', 'image': '☕', 'category': 'Home'},
    {'id': 6, 'name': 'Book', 'price': 24.99, 'description': 'Bestselling novel', 'image': '📚', 'category': 'Books'},
]

users = [
    {'id': 1, 'username': 'admin', 'password': 'admin', 'email': 'admin@shop.com'}
]

orders = []

# HTML Templates
BASE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}ShopApp{% endblock %}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; line-height: 1.6; background: #f4f4f4; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: #2c3e50; color: white; padding: 1rem 0; }
        .nav { display: flex; justify-content: space-between; align-items: center; }
        .logo { font-size: 1.5rem; font-weight: bold; }
        .nav-links a { color: white; text-decoration: none; margin-left: 20px; }
        .cart-count { background: #e74c3c; padding: 2px 6px; border-radius: 50%; font-size: 0.8rem; }
        .products-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }
        .product-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .product-image { font-size: 3rem; text-align: center; margin-bottom: 10px; }
        .product-price { color: #27ae60; font-weight: bold; font-size: 1.2rem; }
        .btn { display: inline-block; background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border: none; border-radius: 4px; cursor: pointer; }
        .btn-success { background: #27ae60; }
        .btn-danger { background: #e74c3c; }
        .cart-item { background: white; padding: 15px; margin: 10px 0; border-radius: 8px; }
        .flash-messages { margin: 20px 0; }
        .flash { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .flash.success { background: #d4edda; color: #155724; }
        .flash.error { background: #f8d7da; color: #721c24; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; }
        input, select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <div class="nav">
                <div class="logo">🛍️ ShopApp</div>
                <div class="nav-links">
                    <a href="{{ url_for('index') }}">Home</a>
                    <a href="{{ url_for('cart') }}">Cart 
                        {% if 'cart' in session %}<span class="cart-count">{{ session.cart|length }}</span>{% endif %}
                    </a>
                    {% if 'user_id' in session %}
                        <a href="{{ url_for('orders') }}">My Orders</a>
                        <a href="{{ url_for('logout') }}">Logout</a>
                    {% else %}
                        <a href="{{ url_for('login') }}">Login</a>
                        <a href="{{ url_for('register') }}">Register</a>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    
    <div class="container">
        <div class="flash-messages">
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="flash {{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
        </div>
        
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

HOME_TEMPLATE = """
{% extends "base.html" %}
{% block content %}
<h1>Welcome to ShopApp!</h1>

<div style="margin: 20px 0;">
    <form method="GET" action="{{ url_for('index') }}">
        <input type="text" name="search" placeholder="Search products..." value="{{ request.args.get('search', '') }}">
        <select name="category">
            <option value="">All Categories</option>
            <option value="Electronics" {% if request.args.get('category') == 'Electronics' %}selected{% endif %}>Electronics</option>
            <option value="Clothing" {% if request.args.get('category') == 'Clothing' %}selected{% endif %}>Clothing</option>
            <option value="Home" {% if request.args.get('category') == 'Home' %}selected{% endif %}>Home</option>
            <option value="Books" {% if request.args.get('category') == 'Books' %}selected{% endif %}>Books</option>
        </select>
        <button type="submit" class="btn">Filter</button>
    </form>
</div>

<div class="products-grid">
    {% for product in filtered_products %}
    <div class="product-card">
        <div class="product-image">{{ product.image }}</div>
        <h3>{{ product.name }}</h3>
        <p>{{ product.description }}</p>
        <p class="product-price">${{ "%.2f"|format(product.price) }}</p>
        <p><small>Category: {{ product.category }}</small></p>
        <form method="POST" action="{{ url_for('add_to_cart', product_id=product.id) }}">
            <button type="submit" class="btn btn-success">Add to Cart</button>
        </form>
    </div>
    {% endfor %}
</div>
{% endblock %}
"""

CART_TEMPLATE = """
{% extends "base.html" %}
{% block title %}Shopping Cart - ShopApp{% endblock %}
{% block content %}
<h1>Shopping Cart</h1>

{% if cart_items %}
    {% for item in cart_items %}
    <div class="cart-item">
        <h3>{{ item.product.image }} {{ item.product.name }}</h3>
        <p>Price: ${{ "%.2f"|format(item.product.price) }}</p>
        <p>Quantity: {{ item.quantity }}</p>
        <p>Subtotal: ${{ "%.2f"|format(item.product.price * item.quantity) }}</p>
        <div style="margin-top: 10px;">
            <form method="POST" action="{{ url_for('update_cart', product_id=item.product.id) }}" style="display: inline;">
                <input type="number" name="quantity" value="{{ item.quantity }}" min="1" style="width: 60px;">
                <button type="submit" class="btn">Update</button>
            </form>
            <form method="POST" action="{{ url_for('remove_from_cart', product_id=item.product.id) }}" style="display: inline;">
                <button type="submit" class="btn btn-danger">Remove</button>
            </form>
        </div>
    </div>
    {% endfor %}
    
    <div style="margin-top: 20px; text-align: right;">
        <h2>Total: ${{ "%.2f"|format(total) }}</h2>
        {% if 'user_id' in session %}
            <form method="POST" action="{{ url_for('checkout') }}">
                <button type="submit" class="btn btn-success">Checkout</button>
            </form>
        {% else %}
            <p><a href="{{ url_for('login') }}">Login</a> to checkout</p>
        {% endif %}
    </div>
{% else %}
    <p>Your cart is empty. <a href="{{ url_for('index') }}">Start shopping!</a></p>
{% endif %}
{% endblock %}
"""

LOGIN_TEMPLATE = """
{% extends "base.html" %}
{% block title %}Login - ShopApp{% endblock %}
{% block content %}
<h1>Login</h1>
<form method="POST">
    <div class="form-group">
        <label>Username:</label>
        <input type="text" name="username" required>
    </div>
    <div class="form-group">
        <label>Password:</label>
        <input type="password" name="password" required>
    </div>
    <button type="submit" class="btn">Login</button>
</form>
<p>Don't have an account? <a href="{{ url_for('register') }}">Register here</a></p>
{% endblock %}
"""

REGISTER_TEMPLATE = """
{% extends "base.html" %}
{% block title %}Register - ShopApp{% endblock %}
{% block content %}
<h1>Register</h1>
<form method="POST">
    <div class="form-group">
        <label>Username:</label>
        <input type="text" name="username" required>
    </div>
    <div class="form-group">
        <label>Email:</label>
        <input type="email" name="email" required>
    </div>
    <div class="form-group">
        <label>Password:</label>
        <input type="password" name="password" required>
    </div>
    <button type="submit" class="btn">Register</button>
</form>
<p>Already have an account? <a href="{{ url_for('login') }}">Login here</a></p>
{% endblock %}
"""

ORDERS_TEMPLATE = """
{% extends "base.html" %}
{% block title %}My Orders - ShopApp{% endblock %}
{% block content %}
<h1>My Orders</h1>

{% if user_orders %}
    {% for order in user_orders %}
    <div class="cart-item">
        <h3>Order #{{ order.id }} - {{ order.date }}</h3>
        <p><strong>Status:</strong> {{ order.status }}</p>
        <p><strong>Total:</strong> ${{ "%.2f"|format(order.total) }}</p>
        <h4>Items:</h4>
        <ul>
            {% for item in order.items %}
            <li>{{ item.product.name }} - ${{ "%.2f"|format(item.product.price) }} x {{ item.quantity }}</li>
            {% endfor %}
        </ul>
    </div>
    {% endfor %}
{% else %}
    <p>You haven't placed any orders yet. <a href="{{ url_for('index') }}">Start shopping!</a></p>
{% endif %}
{% endblock %}
"""

# Routes
@app.route('/')
def index():
    search = request.args.get('search', '').lower()
    category = request.args.get('category', '')
    
    filtered_products = products
    
    if search:
        filtered_products = [p for p in filtered_products if search in p['name'].lower() or search in p['description'].lower()]
    
    if category:
        filtered_products = [p for p in filtered_products if p['category'] == category]
    
    return render_template_string(HOME_TEMPLATE, filtered_products=filtered_products)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'cart' not in session:
        session['cart'] = []
    
    cart = session['cart']
    
    # Check if product already in cart
    for item in cart:
        if item['product_id'] == product_id:
            item['quantity'] += 1
            session['cart'] = cart
            flash('Product quantity updated in cart!', 'success')
            return redirect(url_for('index'))
    
    # Add new product to cart
    cart.append({'product_id': product_id, 'quantity': 1})
    session['cart'] = cart
    flash('Product added to cart!', 'success')
    return redirect(url_for('index'))

@app.route('/cart')
def cart():
    cart_items = []
    total = 0
    
    if 'cart' in session:
        for item in session['cart']:
            product = next((p for p in products if p['id'] == item['product_id']), None)
            if product:
                cart_items.append({
                    'product': product,
                    'quantity': item['quantity']
                })
                total += product['price'] * item['quantity']
    
    return render_template_string(CART_TEMPLATE, cart_items=cart_items, total=total)

@app.route('/update_cart/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    quantity = int(request.form['quantity'])
    
    if 'cart' in session:
        cart = session['cart']
        for item in cart:
            if item['product_id'] == product_id:
                item['quantity'] = quantity
                break
        session['cart'] = cart
        flash('Cart updated!', 'success')
    
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    if 'cart' in session:
        session['cart'] = [item for item in session['cart'] if item['product_id'] != product_id]
        flash('Product removed from cart!', 'success')
    
    return redirect(url_for('cart'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = next((u for u in users if u['username'] == username and u['password'] == password), None)
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if any(u['username'] == username for u in users):
            flash('Username already exists!', 'error')
        else:
            new_user = {
                'id': len(users) + 1,
                'username': username,
                'email': email,
                'password': password
            }
            users.append(new_user)
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
    
    return render_template_string(REGISTER_TEMPLATE)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/orders')
def orders():
    if 'user_id' not in session:
        flash('Please login to view your orders!', 'error')
        return redirect(url_for('login'))
    
    user_orders = [order for order in orders if order['user_id'] == session['user_id']]
    return render_template_string(ORDERS_TEMPLATE, user_orders=user_orders)

@app.route('/checkout', methods=['POST'])
def checkout():
    if 'user_id' not in session:
        flash('Please login to checkout!', 'error')
        return redirect(url_for('login'))
    
    if 'cart' not in session or not session['cart']:
        flash('Your cart is empty!', 'error')
        return redirect(url_for('cart'))
    
    # Calculate total
    total = 0
    cart_items = []
    for item in session['cart']:
        product = next((p for p in products if p['id'] == item['product_id']), None)
        if product:
            total += product['price'] * item['quantity']
            cart_items.append({
                'product': product,
                'quantity': item['quantity']
            })
    
    # Create order
    new_order = {
        'id': len(orders) + 1,
        'user_id': session['user_id'],
        'items': cart_items,
        'total': total,
        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'status': 'Processing'
    }
    orders.append(new_order)
    
    # Clear cart
    session.pop('cart', None)
    
    flash(f'Order placed successfully! Order #{new_order["id"]}', 'success')
    return redirect(url_for('orders'))


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
