from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
CORS(app)
app.secret_key = 'your_secret_key'  # Set a secret key for session management

# Database configuration
db_config = {
    'user': 'root',
    'password': 'AyuSS@2231',
    'host': 'localhost',
    'database': 'flight_booking_2231'
}

# Route for home page
@app.route('/')
def index():
    return render_template('home.html')

# Route for user registration
@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data['username']
    password = data['password']
    email = data['email']
    phone = data.get('phone', '')

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    try:
        query = "INSERT INTO User (username, password, email, phone) VALUES (%s, %s, %s, %s)"
        values = (username, password, email, phone)
        cursor.execute(query, values)
        conn.commit()
        return jsonify({'message': 'User registered successfully!'})
    except mysql.connector.Error as err:
        return jsonify({'message': str(err)}), 400
    finally:
        cursor.close()
        conn.close()

# Route for user login
@app.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    username = data['username']
    password = data['password']

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    try:
        query = "SELECT * FROM User WHERE username = %s AND password = %s"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()
        
        if user:
            session['user_id'] = user[0]  # Assuming user ID is the first column
            return jsonify({'message': 'Login successful!', 'redirect_url': '/flights'})
        else:
            return jsonify({'message': 'Invalid credentials!'}), 401
    finally:
        cursor.close()
        conn.close()

# Route to check available flights
@app.route('/flights', methods=['GET'])
def get_flights():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    query = "SELECT * FROM Flight WHERE available_seats > 0"
    
    cursor.execute(query)
    flights = cursor.fetchall()
    
    flight_list = []
    for flight in flights:
        flight_list.append({
            'flight_id': flight[0],
            'flight_number': flight[1],
            'departure_city': flight[2],
            'destination_city': flight[3],
            'departure_time': flight[4],
            'arrival_time': flight[5],
            'status': flight[6],
            'available_seats': flight[7]
        })
    return render_template('flights.html', flights=flight_list)
# Route for booking a flight using flight number
@app.route('/book-flight', methods=['POST'])
def book_flight():
    data = request.get_json()
    user_id = session.get('user_id')  # Get user ID from session
    flight_number = data['flight_number']
    num_seats = int(data['num_seats'])  # Number of seats to book

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    try:
        # Get flight ID and available seats using flight number
        cursor.execute("SELECT flight_id, available_seats FROM Flight WHERE flight_number = %s", (flight_number,))
        flight = cursor.fetchone()

        if flight and flight[1] >= num_seats:  # Check if there are enough available seats
            flight_id = flight[0]
            
            # Update available seats
            cursor.execute("UPDATE Flight SET available_seats = available_seats - %s WHERE flight_id = %s", (num_seats, flight_id))
            cursor.execute("INSERT INTO Booking (user_id, flight_id, seat_number) VALUES (%s, %s, %s)", (user_id, flight_id, num_seats))
            conn.commit()
            
            # Get updated available seats
            cursor.execute("SELECT available_seats FROM Flight WHERE flight_id = %s", (flight_id,))
            updated_seats = cursor.fetchone()[0]
            
            return jsonify({'message': 'Flight booked successfully!', 'updated_seats': updated_seats})
        else:
            return jsonify({'message': 'Not enough available seats for this flight.'}), 400
    except mysql.connector.Error as err:
        return jsonify({'message': str(err)}), 500
    finally:
        cursor.close()
        conn.close()
if __name__ == '__main__':
    app.run(debug=True)
