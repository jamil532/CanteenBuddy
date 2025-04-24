from flask import Flask, jsonify, request, session
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
app.secret_key = "supersecretkey"
CORS(app, resources={r"/*": {"origins": "http://127.0.0.1:5500"}})

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="password",
    database="canteen"
)
cursor = db.cursor()

@app.route('/menu', methods=['GET'])
def get_menu():
    cursor.execute("SELECT item_id, item_name, category, price FROM Menu_Item WHERE availability = TRUE")
    menu = cursor.fetchall()
    return jsonify(menu if menu else {"message": "No available items."})

@app.route('/clear-session', methods=['POST'])
def start_session():
    session['session_id'] = request.json.get('session_id')
    session['order_id'] = None  # Initialize order_id as None
    return jsonify({"message": "Session started", "session_id": session['session_id']})

@app.route('/order', methods=['POST'])
def place_order():
    data = request.get_json()
    
    # Ensure session_id is received from the request
    session_id = data.get('session_id')
    if not session_id:
        return jsonify({"error": "Session ID missing"}), 400

    # Check if order_items exists and is a list
    order_items = data.get('order_items', [])
    if not isinstance(order_items, list) or not order_items:
        return jsonify({"error": "Invalid order data"}), 400

    cursor.execute("INSERT INTO Orders (session_id, amount) VALUES (%s, 0)", (session_id,))
    db.commit()
    order_id = cursor.lastrowid  

    for item in order_items:
        item_id = item.get('item_id')
        quantity = item.get('quantity')
        if not item_id or not quantity:
            return jsonify({"error": "Invalid order item"}), 400
        
        cursor.execute("INSERT INTO Order_Details (order_id, item_id, quantity) VALUES (%s, %s, %s)",
                       (order_id, item_id, quantity))
    
    db.commit()
    
    return jsonify({"message": "Order placed successfully", "order_id": order_id})


@app.route('/bill', methods=['GET'])
def get_bill():
    order_id = request.args.get('order_id')  # Get order_id from URL parameter
    
    if not order_id:
        return jsonify({"error": "Order ID is required"}), 400
    
    # Fetch order total
    cursor.execute("""
        SELECT SUM(m.price * o.quantity) AS total_amount 
        FROM Order_Details o 
        JOIN Menu_Item m ON o.item_id = m.item_id 
        WHERE o.order_id = %s
    """, (order_id,))
    total_amount = cursor.fetchone()[0] or 0.0  # Default to 0 if no orders
    
    # Update the order amount
    cursor.execute("UPDATE Orders SET amount = %s WHERE order_id = %s", (total_amount, order_id))
    db.commit()
    
    # Fetch ordered items
    cursor.execute("""
        SELECT m.item_name, o.quantity, m.price 
        FROM Order_Details o 
        JOIN Menu_Item m ON o.item_id = m.item_id 
        WHERE o.order_id = %s
    """, (order_id,))
    
    items = cursor.fetchall()  # List of ordered items
    
    # If no items found, return an error
    if not items:
        return jsonify({"error": "No active order found for this ID"}), 404
    
    # Convert items to a list of dictionaries
    order_items = [{"item_name": item[0], "quantity": item[1], "price": float(item[2])} for item in items]

    return jsonify({
        "order_id": order_id,
        "total": float(total_amount),
        "orders": order_items
    })


@app.route('/make_payment', methods=['POST'])
def make_payment():
    data = request.json
    order_id = data.get('order_id')  # Get the unique order_id from the request body
    if not order_id:
        return jsonify({"error": "Order ID is required"}), 400
    
    # Fetch total amount from Orders table for the given order_id
    cursor.execute("SELECT amount FROM Orders WHERE order_id = %s", (order_id,))
    result = cursor.fetchone()
    
    if not result:
        return jsonify({"error": "Order not found"}), 404
    
    total_amount = result[0]  # Assuming the amount is in the first column of the result
    
    # Process the payment and insert it into the Payment table
    payment_method = data.get('payment_method')
    if not payment_method:
        return jsonify({"error": "Payment method is required"}), 400
    
    cursor.execute("""
        INSERT INTO Payment (order_id, payment_method, amount)
        VALUES (%s, %s, %s)
    """, (order_id, payment_method, total_amount))
    
    db.commit()  # Commit the transaction

    return jsonify({
        "message": "Payment successful",
        "order_id": order_id,
        "amount_paid": total_amount
    })



@app.route('/end_session', methods=['POST'])
def end_session():
    session.clear()
    return jsonify({"message": "Session ended"})

if __name__ == '__main__':
    app.run(debug=True)
