from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
import os
import sqlite3

from database import init_db, get_db_connection
from models import User, Hotel, Booking
from blockchain import verify_chain, calculate_hash, get_booking_data_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'vedic_stay_secret_key_sha256_secured')

# Initialize database on startup
with app.app_context():
    init_db()

# --- MIDDLEWARES / DECORATORS ---
def is_logged_in():
    return 'user_id' in session

def is_admin():
    return session.get('role') == 'admin'

@app.context_processor
def inject_cities():
    # Inject cities into navbar/layouts globally
    try:
        cities = Hotel.get_cities()
    except Exception:
        cities = []
    return dict(cities=cities)

# --- CLIENT ROUTES ---

@app.route('/')
def index():
    # Fetch first 4 hotels as featured ones
    featured_hotels = Hotel.get_all()[:4]
    return render_template('index.html', featured_hotels=featured_hotels)

@app.route('/hotels')
def hotels():
    search_query = request.args.get('search_query')
    city = request.args.get('city')
    rating = request.args.get('rating')
    sort_by = request.args.get('sort_by')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')

    hotel_list = Hotel.get_all(
        search_query=search_query,
        city=city,
        rating=rating,
        sort_by=sort_by,
        min_price=min_price,
        max_price=max_price
    )
    return render_template('hotels.html', hotels=hotel_list)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if is_logged_in():
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        user_id = User.create(name, email, password)
        if user_id:
            flash("Account registered successfully! Please login.", "success")
            return redirect(url_for('login'))
        else:
            flash("Email address already registered.", "error")
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_logged_in():
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.authenticate(email, password)
        if user:
            session['user_id'] = user['id']
            session['name'] = user['name']
            session['email'] = user['email']
            session['role'] = user['role']
            
            flash(f"Welcome back, {user['name']}!", "success")
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password.", "error")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if not is_logged_in():
        flash("Please login to access your dashboard.", "error")
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    bookings = Booking.get_user_history(user_id)
    
    total = len(bookings)
    active = sum(1 for b in bookings if b['status'] == 'Confirmed')
    cancelled = sum(1 for b in bookings if b['status'] == 'Cancelled')
    
    return render_template(
        'dashboard.html', 
        name=session['name'], 
        email=session['email'],
        bookings=bookings, 
        total_bookings=total, 
        active_bookings=active, 
        cancelled_bookings=cancelled
    )

@app.route('/history')
def history():
    if not is_logged_in():
        flash("Please login to view booking history.", "error")
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    bookings = Booking.get_user_history(user_id)
    return render_template('history.html', bookings=bookings)

@app.route('/book/<int:hotel_id>', methods=['GET', 'POST'])
def booking_page(hotel_id):
    if not is_logged_in():
        flash("Please login to make a reservation.", "error")
        return redirect(url_for('login'))
        
    hotel = Hotel.get_by_id(hotel_id)
    if not hotel:
        flash("Hotel not found.", "error")
        return redirect(url_for('hotels'))
        
    if request.method == 'POST':
        checkin = request.form['checkin']
        checkout = request.form['checkout']
        guests = int(request.form['guests'])
        room_type = request.form['room_type']
        
        # Recalculate amount on backend for security
        try:
            checkin_dt = datetime.strptime(checkin, '%Y-%m-%d')
            checkout_dt = datetime.strptime(checkout, '%Y-%m-%d')
            nights = (checkout_dt - checkin_dt).days
            if nights <= 0:
                flash("Checkout date must be after checkin date.", "error")
                return redirect(url_for('booking_page', hotel_id=hotel_id))
        except ValueError:
            flash("Invalid date format.", "error")
            return redirect(url_for('booking_page', hotel_id=hotel_id))
            
        room_multipliers = {
            'Standard Room': 1.0,
            'Deluxe Room': 1.5,
            'Luxury Room': 2.2,
            'Suite': 3.5
        }
        multiplier = room_multipliers.get(room_type, 1.0)
        amount = int(round(hotel['price'] * multiplier * nights))
        
        booking_id, err = Booking.create(
            user_id=session['user_id'],
            hotel_id=hotel_id,
            checkin=checkin,
            checkout=checkout,
            guests=guests,
            room_type=room_type,
            amount=amount
        )
        
        if booking_id:
            flash("Reservation confirmed successfully! Transaction added to the blockchain.", "success")
            return redirect(url_for('history'))
        else:
            flash(f"Booking failed: {err}", "error")
            return redirect(url_for('booking_page', hotel_id=hotel_id))
            
    return render_template('booking.html', hotel=hotel)

@app.route('/booking/cancel/<int:booking_id>')
def cancel_booking_route(booking_id):
    if not is_logged_in():
        flash("Please login to perform this action.", "error")
        return redirect(url_for('login'))
        
    booking = Booking.get_by_id(booking_id)
    if not booking or (booking['user_id'] != session['user_id'] and session.get('role') != 'admin'):
        flash("Unauthorized request.", "error")
        return redirect(url_for('dashboard'))
        
    success, err = Booking.cancel(booking_id)
    if success:
        flash("Reservation cancelled successfully. Inventory restored.", "success")
    else:
        flash(f"Error cancelling reservation: {err}", "error")
        
    if session.get('role') == 'admin':
        return redirect(url_for('admin_bookings'))
    return redirect(url_for('dashboard'))

# --- ADMIN ROUTES ---

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if is_logged_in() and session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))
        
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.authenticate(email, password)
        if user and user['role'] == 'admin':
            session['user_id'] = user['id']
            session['name'] = user['name']
            session['email'] = user['email']
            session['role'] = user['role']
            flash("Welcome to Admin Dashboard.", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Access denied. Invalid administrator credentials.", "error")
            
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not is_admin():
        flash("Unauthorized. Admin access required.", "error")
        return redirect(url_for('login'))
        
    # Stats
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT SUM(amount) FROM bookings WHERE status = 'Confirmed'")
    total_revenue = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(*) FROM bookings")
    total_bookings = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM hotels")
    total_hotels = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    # Chart 1: Bookings count by hotel
    cursor.execute("""
        SELECT h.hotel_name, COUNT(b.id) as count 
        FROM hotels h 
        LEFT JOIN bookings b ON h.id = b.hotel_id 
        GROUP BY h.id
    """)
    hotels_bookings_data = [{"name": row['hotel_name'], "count": row['count']} for row in cursor.fetchall()]
    
    # Chart 2: Revenue by city
    cursor.execute("""
        SELECT h.city, SUM(b.amount) as revenue 
        FROM bookings b 
        JOIN hotels h ON b.hotel_id = h.id 
        WHERE b.status = 'Confirmed' 
        GROUP BY h.city
    """)
    city_revenue_data = [{"city": row['city'], "revenue": row['revenue'] or 0} for row in cursor.fetchall()]
    
    # Check chain integrity
    chain_healthy, _ = verify_chain(conn)
    conn.close()
    
    hotels_list = Hotel.get_all()
    
    return render_template(
        'admin_dashboard.html',
        total_revenue=total_revenue,
        total_bookings=total_bookings,
        total_hotels=total_hotels,
        total_users=total_users,
        hotels_bookings_data=hotels_bookings_data,
        city_revenue_data=city_revenue_data,
        chain_healthy=chain_healthy,
        hotels=hotels_list
    )

@app.route('/admin/bookings')
def admin_bookings():
    if not is_admin():
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))
        
    bookings = Booking.get_all()
    return render_template('bookings.html', bookings=bookings)

@app.route('/admin/users')
def admin_users():
    if not is_admin():
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))
        
    users = User.get_all()
    return render_template('users.html', users=users)

@app.route('/admin/hotel/add', methods=['GET', 'POST'])
def add_hotel():
    if not is_admin():
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))
        
    if request.method == 'POST':
        hotel_name = request.form['hotel_name']
        city = request.form['city']
        state = request.form['state']
        address = request.form['address']
        description = request.form['description']
        price = int(request.form['price'])
        rooms = int(request.form['rooms'])
        image = request.form['image']
        gallery = request.form['gallery']
        rating = float(request.form['rating'])
        amenities = request.form['amenities']
        contact_number = request.form['contact_number']
        maps_link = request.form['maps_link']
        
        hotel_id = Hotel.create(
            hotel_name, city, state, address, description, price, rooms, image, gallery, rating, amenities, contact_number, maps_link
        )
        if hotel_id:
            flash("Hotel added successfully to catalog inventory.", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Failed to add hotel.", "error")
            
    return render_template('add_hotel.html')

@app.route('/admin/hotel/edit/<int:hotel_id>', methods=['GET', 'POST'])
def edit_hotel(hotel_id):
    if not is_admin():
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))
        
    hotel = Hotel.get_by_id(hotel_id)
    if not hotel:
        flash("Hotel not found.", "error")
        return redirect(url_for('admin_dashboard'))
        
    if request.method == 'POST':
        hotel_name = request.form['hotel_name']
        city = request.form['city']
        state = request.form['state']
        address = request.form['address']
        description = request.form['description']
        price = int(request.form['price'])
        rooms = int(request.form['rooms'])
        image = request.form['image']
        gallery = request.form['gallery']
        rating = float(request.form['rating'])
        amenities = request.form['amenities']
        contact_number = request.form['contact_number']
        maps_link = request.form['maps_link']
        
        Hotel.update(
            hotel_id, hotel_name, city, state, address, description, price, rooms, image, gallery, rating, amenities, contact_number, maps_link
        )
        flash("Hotel catalog updated successfully.", "success")
        return redirect(url_for('admin_dashboard'))
        
    return render_template('edit_hotel.html', hotel=hotel)

@app.route('/admin/hotel/delete/<int:hotel_id>')
def delete_hotel_route(hotel_id):
    if not is_admin():
        flash("Unauthorized access.", "error")
        return redirect(url_for('login'))
        
    Hotel.delete(hotel_id)
    flash("Hotel removed from inventory catalog.", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/booking/approve/<int:booking_id>')
def approve_booking_route(booking_id):
    if not is_admin():
        flash("Unauthorized.", "error")
        return redirect(url_for('login'))
        
    success, err = Booking.approve(booking_id)
    if success:
        flash("Booking reservation approved.", "success")
    else:
        flash(f"Approval error: {err}", "error")
    return redirect(url_for('admin_bookings'))

@app.route('/admin/booking/cancel/<int:booking_id>')
def admin_cancel_booking_route(booking_id):
    return cancel_booking_route(booking_id)

@app.route('/admin/blockchain')
def view_blockchain():
    if not is_admin():
        flash("Unauthorized.", "error")
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    chain_healthy, validation_details = verify_chain(conn)
    conn.close()
    
    return render_template(
        'view_blockchain.html',
        chain_healthy=chain_healthy,
        validation_details=validation_details
    )

@app.route('/admin/simulate-tampering', methods=['POST'])
def simulate_tampering():
    if not is_admin():
        flash("Unauthorized.", "error")
        return redirect(url_for('login'))
        
    booking_id = request.form.get('booking_id')
    if not booking_id:
        flash("No booking selected.", "error")
        return redirect(url_for('view_blockchain'))
        
    # Alter the data in bookings table directly, bypassing the blockchain calculation
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Alter the amount by subtracting 5000 to simulate financial fraud
        cursor.execute("UPDATE bookings SET amount = amount - 5000 WHERE id = ?", (booking_id,))
        conn.commit()
        flash("DATABASE CORRUPTED: Modified booking price in SQL table. Verify blockchain to see validation break.", "warning")
    except Exception as e:
        flash(f"Tamper simulation failed: {e}", "error")
    finally:
        conn.close()
        
    return redirect(url_for('view_blockchain'))

@app.route('/admin/repair-blockchain')
def repair_blockchain():
    if not is_admin():
        flash("Unauthorized.", "error")
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    conn.execute("BEGIN TRANSACTION")
    cursor = conn.cursor()
    try:
        # Fetch all blocks
        cursor.execute("SELECT * FROM blockchain ORDER BY id ASC")
        blocks = [dict(row) for row in cursor.fetchall()]
        
        # Fetch all bookings
        cursor.execute("SELECT * FROM bookings")
        bookings = {row['id']: dict(row) for row in cursor.fetchall()}
        
        # Recompute Genesis Block Pointer
        genesis = blocks[0]
        genesis_timestamp = genesis['timestamp']
        genesis_hash = calculate_hash(1, None, "0", genesis_timestamp, "GENESIS_DATA")
        cursor.execute("UPDATE blockchain SET current_hash = ? WHERE id = 1", (genesis_hash,))
        
        prev_hash = genesis_hash
        
        # Recompute remaining blocks
        for i in range(1, len(blocks)):
            block = blocks[i]
            booking_id = block['booking_id']
            timestamp = block['timestamp']
            
            # Fetch booking data hash
            booking = bookings.get(booking_id)
            booking_data_hash = get_booking_data_hash(booking)
            
            # Compute new hash
            curr_hash = calculate_hash(block['id'], booking_id, prev_hash, timestamp, booking_data_hash)
            
            # Update block
            cursor.execute("""
                UPDATE blockchain 
                SET previous_hash = ?, current_hash = ? 
                WHERE id = ?
            """, (prev_hash, curr_hash, block['id']))
            
            prev_hash = curr_hash
            
        conn.commit()
        flash("Blockchain healed successfully! Cryptographic pointer hashes re-calculated and sealed.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Heal failed: {e}", "error")
    finally:
        conn.close()
        
    return redirect(url_for('view_blockchain'))

# --- ERROR HANDLERS ---
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
