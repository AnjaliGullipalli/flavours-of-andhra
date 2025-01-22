from flask import Blueprint, render_template, request, jsonify, session, redirect, current_app
import hashlib

main = Blueprint('main', __name__)


@main.route('/')
def hello_world():
    return render_template('home.html')


@main.route('/login')
def login():
    if 'id' in session:
        return redirect('/dashboard')
    return render_template('login.html')


@main.route('/registration')
def registration():
    if 'id' in session:
        return redirect('/dashboard')
    return render_template('registration.html')


@main.route('/registrationHandle', methods=['POST'])
def registrationHandle():
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
        return '', 200, headers

    data = request.get_json()
    username = data.get('username')  # Use the correct key to get the username
    password = data.get('password')

    if not username or not password:  # Check if username or password is None
        return jsonify({"message": 'Username and password are required!'}), 400

    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

    cur = current_app.mysql.connection.cursor()

    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    if user:
        cur.close()
        return jsonify({"message": 'Username already exists!'}), 400

    cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
    current_app.mysql.connection.commit()
    cur.close()

    return jsonify({"message": 'Done'})


@main.route('/submitHandle', methods=['POST'])
def loginHandle():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

    # Connect to MySQL database
    cur = current_app.mysql.connection.cursor()

    # Query user with username and hashed password
    cur.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, hashed_password))
    user = cur.fetchone()
    cur.close()

    if user:
        session['id'] = user['id']
        return jsonify({'status': 'success', 'username': username}), 200

    return jsonify({'status': 'notfound'}), 200


@main.route('/logout')
def logout():
    session.pop('id', None)
    return redirect('/')


@main.route('/profile')
def profile():
    if 'id' in session:
        id = session['id']
        # Connect to MySQL database
        cur = current_app.mysql.connection.cursor()

        # Query user by username
        cur.execute("SELECT * FROM users WHERE id = %s", (id,))
        user = cur.fetchone()
        cur.close()

        if user:
            return jsonify({"name": user['username']})  # Assuming 'username' is the field for name
    return jsonify({"name": "not logged in"})


@main.route('/home')
def home():
    return render_template('home.html')


@main.route('/dashboard')
def dashboard():
    if 'id' not in session:
        return redirect('/login')
    return render_template('dashboard.html')


@main.route('/cart')
def cart():
    if 'id' not in session:
        return redirect('/login')
    return render_template('cart.html')


@main.route('/order')
def order():
    if 'id' not in session:
        return redirect('/login')
    return render_template('order.html')


@main.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'id' not in session:
        return jsonify({'message': 'User not logged in!'}), 401

    data = request.get_json()
    item_name = data.get('item_name')
    quantity = data.get('quantity')
    price = data.get('price')

    if not item_name or not quantity:
        return jsonify({"message": 'Item name and quantity are required!'}), 400

    user_id = session['id']

    cur = current_app.mysql.connection.cursor()
    # Check if the item is already in the cart
    cur.execute("SELECT quantity FROM cart WHERE user_id = %s AND item_name = %s", (user_id, item_name))
    existing_item = cur.fetchone()
    print(existing_item)

    if existing_item is not None:
        # If the item is already in the cart, update the quantity
        new_quantity = existing_item['quantity'] + quantity
        cur.execute("UPDATE cart SET quantity = %s WHERE user_id = %s AND item_name = %s",
                    (new_quantity, user_id, item_name))
    else:
        # If the item is not in the cart, insert a new row
        cur.execute("INSERT INTO cart (user_id, item_name, quantity, price) VALUES (%s, %s, %s, %s)",
                    (user_id, item_name, quantity, price))

    current_app.mysql.connection.commit()
    cur.close()

    return jsonify({'message': 'Item added to cart!'}), 200


@main.route('/view_cart', methods=['GET'])
def view_cart():
    if 'id' not in session:
        return jsonify({'message': 'User not logged in!'}), 401

    user_id = session['id']

    cur = current_app.mysql.connection.cursor()
    cur.execute("SELECT * FROM cart WHERE user_id = %s", (user_id,))
    cart_items = cur.fetchall()
    cur.close()

    return jsonify({'items': cart_items}), 200


@main.route('/update_cart', methods=['POST'])
def update_cart():
    if 'id' not in session:
        return jsonify({'message': 'User not logged in!'}), 401

    data = request.get_json()
    cart_id = data.get('cart_id')
    quantity = data.get('quantity')

    if not cart_id or not quantity:
        return jsonify({"message": 'Cart ID and quantity are required!'}), 400

    user_id = session['id']

    cur = current_app.mysql.connection.cursor()
    cur.execute("UPDATE cart SET quantity = %s WHERE id = %s AND user_id = %s", (quantity, cart_id, user_id))
    current_app.mysql.connection.commit()
    cur.close()

    return jsonify({'message': 'Cart item updated!'}), 200


@main.route('/delete_cart', methods=['POST'])
def delete_cart():
    if 'id' not in session:
        return jsonify({'message': 'User not logged in!'}), 401

    data = request.get_json()
    cart_id = data.get('cart_id')

    if not cart_id:
        return jsonify({"message": 'Cart ID is required!'}), 400

    user_id = session['id']

    cur = current_app.mysql.connection.cursor()
    cur.execute("DELETE FROM cart WHERE id = %s AND user_id = %s", (cart_id, user_id))
    current_app.mysql.connection.commit()
    cur.close()

    return jsonify({'message': 'Cart item deleted!'}), 200


@main.route('/submit_order', methods=['POST'])
def submit_order():
    if 'id' not in session:
        return jsonify({'message': 'User not logged in!'}), 401

    user_id = session['id']
    order_items = request.json.get('items', [])

    if not order_items:
        return jsonify({'message': 'Cart is empty!'}), 400

    total_amount = 0

    # Calculate total_amount with type conversion
    for item in order_items:
        try:
            price = float(item['price'])  # Ensure price is a float
            quantity = int(item['quantity'])  # Ensure quantity is an integer
            total_amount += price * quantity
        except (ValueError, TypeError) as e:
            return jsonify({'message': f'Invalid data: {str(e)}'}), 400

    cur = current_app.mysql.connection.cursor()

    try:
        # Insert the order into the orders table
        cur.execute("""
            INSERT INTO orders (user_id, total_amount)
            VALUES (%s, %s)
        """, (user_id, total_amount))
        order_id = cur.lastrowid

        # Insert the items into the order_items table
        for item in order_items:
            cur.execute("""
                INSERT INTO order_items (order_id, item_id, quantity, price)
                VALUES (%s, %s, %s, %s)
            """, (order_id, item['id'], int(item['quantity']), float(item['price'])))

        # Delete the items from the cart
        cur.execute("DELETE FROM cart WHERE user_id = %s", (user_id,))
        current_app.mysql.connection.commit()

        return jsonify({'message': 'Order successfully submitted!'}), 200

    except Exception as e:
        current_app.mysql.connection.rollback()
        print(e)
        return jsonify({'message': str(e)}), 500

    finally:
        cur.close()


@main.route('/view_orders', methods=['GET'])
def view_orders():
    if 'id' not in session:
        return jsonify({'message': 'User not logged in!'}), 401

    user_id = session['id']

    cur = current_app.mysql.connection.cursor()

    # Retrieve orders with their items
    cur.execute("""
        SELECT orders.id AS order_id, orders.total_amount, orders.order_date, order_items.item_id, order_items.quantity, order_items.price
        FROM orders
        JOIN order_items ON orders.id = order_items.order_id
        WHERE orders.user_id = %s
        ORDER BY orders.order_date DESC
    """, (user_id,))

    results = cur.fetchall()

    # Organize results into a structured format
    orders = {}
    for row in results:
        order_id = row['order_id']
        if order_id not in orders:
            orders[order_id] = {
                'order_id': order_id,
                'total_amount': row['total_amount'],
                'order_date': row['order_date'],
                'items': []
            }
        orders[order_id]['items'].append({
            'item_id': row['item_id'],
            'quantity': row['quantity'],
            'price': row['price']
        })

    cur.close()

    # Convert orders dictionary to a list for JSON response
    order_list = list(orders.values())

    return jsonify({'orders': order_list}), 200
