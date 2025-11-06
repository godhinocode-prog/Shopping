from flask import Flask, render_template_string, request, redirect, url_for, flash, session
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-12345')

# Sample products data
products = [
    {'id': 1, 'name': 'Laptop', 'price': 999.99, 'description': 'High-performance laptop', 'image': '💻', 'category': 'Electronics'},
    {'id': 2, 'name': 'Smartphone', 'price': 699.99, 'description': 'Latest smartphone', 'image': '📱', 'category': 'Electronics'},
    {'id': 3, 'name': 'Headphones', 'price': 149.99, 'description': 'Noise-cancelling headphones', 'image': '🎧', 'category': 'Electronics'},
    {'id': 4, 'name': 'T-Shirt', 'price': 19.99, 'description': 'Cotton t-shirt', 'image': '👕', 'category': 'Clothing'},
]

users = [{'id': 1, 'username': 'admin', 'password': 'admin', 'email': 'admin@shop.com'}]
orders = []

# HTML Templates (include all the template strings from previous example)
BASE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>ShopApp</title>
    <style>
        body { font-family: Arial; margin: 0; padding: 20px; background: #f4f4f4; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #2c3e50; color: white; padding: 1rem; margin-bottom: 20px; }
        .products-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; }
        .product-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .btn { background: #3498db; color: white; padding: 10px; border: none; border-radius: 4px; text-decoration: none; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛍️ ShopApp</h1>
        <div>
            <a href="/" style="color: white; margin-right: 15px;">Home</a>
            <a href="/cart" style="color: white; margin-right: 15px;">Cart</a>
            <a href="/login" style="color: white;">Login</a>
        </div>
    </div>
    <div class="container">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

HOME_TEMPLATE = """
{% extends "base.html" %}
{% block content %}
<h2>Our Products</h2>
<div class="products-grid">
    {% for product in products %}
    <div class="product-card">
        <div style="font-size: 3rem; text-align: center;">{{ product.image }}</div>
        <h3>{{ product.name }}</h3>
        <p>{{ product.description }}</p>
        <p style="color: #27ae60; font-weight: bold; font-size: 1.2rem;">${{ "%.2f"|format(product.price) }}</p>
        <form method="POST" action="/add_to_cart/{{ product.id }}">
            <button type="submit" class="btn">Add to Cart</button>
        </form>
    </div>
    {% endfor %}
</div>
{% endblock %}
"""

# Add all the routes from previous example
@app.route('/')
def index():
    return render_template_string(HOME_TEMPLATE, products=products)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'cart' not in session:
        session['cart'] = []
    
    cart = session['cart']
    for item in cart:
        if item['product_id'] == product_id:
            item['quantity'] += 1
            session['cart'] = cart
            flash('Product quantity updated!')
            return redirect('/')
    
    cart.append({'product_id': product_id, 'quantity': 1})
    session['cart'] = cart
    flash('Product added to cart!')
    return redirect('/')

@app.route('/cart')
def cart():
    return "Cart page - implement as needed"

@app.route('/login', methods=['GET', 'POST'])
def login():
    return "Login page - implement as needed"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
