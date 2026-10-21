import sqlite3
import time
import random
from database import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
from blockchain import calculate_hash, get_booking_data_hash

class User:
    @staticmethod
    def create(name, email, password, role='user'):
        conn = get_db_connection()
        cursor = conn.cursor()
        hashed_password = generate_password_hash(password)
        try:
            cursor.execute(
                "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                (name, email, hashed_password, role)
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()

    @staticmethod
    def authenticate(email, password):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            return dict(user)
        return None

    @staticmethod
    def get_by_id(user_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None

    @staticmethod
    def get_all():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, role FROM users ORDER BY id DESC")
        users = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return users

class Hotel:
    @staticmethod
    def get_all(search_query=None, city=None, rating=None, sort_by=None, min_price=None, max_price=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM hotels WHERE 1=1"
        params = []
        
        if search_query:
            query += " AND (hotel_name LIKE ? OR description LIKE ? OR city LIKE ?)"
            params.extend([f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"])
            
        if city:
            query += " AND city = ?"
            params.append(city)
            
        if rating:
            query += " AND rating >= ?"
            params.append(float(rating))

        if min_price:
            query += " AND price >= ?"
            params.append(int(min_price))
            
        if max_price:
            query += " AND price <= ?"
            params.append(int(max_price))
            
        if sort_by == 'price_asc':
            query += " ORDER BY price ASC"
        elif sort_by == 'price_desc':
            query += " ORDER BY price DESC"
        elif sort_by == 'rating_desc':
            query += " ORDER BY rating DESC"
        else:
            query += " ORDER BY id DESC"
            
        cursor.execute(query, params)
        hotels = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return hotels

    @staticmethod
    def get_by_id(hotel_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hotels WHERE id = ?", (hotel_id,))
        hotel = cursor.fetchone()
        conn.close()
        return dict(hotel) if hotel else None

    @staticmethod
    def get_cities():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT city FROM hotels ORDER BY city ASC")
        cities = [row['city'] for row in cursor.fetchall()]
        conn.close()
        return cities

    @staticmethod
    def create(hotel_name, city, state, address, description, price, rooms, image, gallery, rating, amenities, contact_number, maps_link):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO hotels (hotel_name, city, state, address, description, price, rooms, image, gallery, rating, amenities, contact_number, maps_link)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (hotel_name, city, state, address, description, price, rooms, image, gallery, rating, amenities, contact_number, maps_link))
        conn.commit()
        hotel_id = cursor.lastrowid
        conn.close()
        return hotel_id

    @staticmethod
    def update(hotel_id, hotel_name, city, state, address, description, price, rooms, image, gallery, rating, amenities, contact_number, maps_link):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE hotels SET hotel_name=?, city=?, state=?, address=?, description=?, price=?, rooms=?, image=?, gallery=?, rating=?, amenities=?, contact_number=?, maps_link=?
            WHERE id=?
        """, (hotel_name, city, state, address, description, price, rooms, image, gallery, rating, amenities, contact_number, maps_link, hotel_id))
        conn.commit()
        conn.close()

    @staticmethod
    def delete(hotel_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM hotels WHERE id = ?", (hotel_id,))
        conn.commit()
        conn.close()

class Booking:
    @staticmethod
    def create(user_id, hotel_id, checkin, checkout, guests, room_type, amount):
        conn = get_db_connection()
        conn.execute("BEGIN TRANSACTION")
        cursor = conn.cursor()
        
        try:
            # Check availability
            cursor.execute("SELECT rooms FROM hotels WHERE id = ?", (hotel_id,))
            hotel = cursor.fetchone()
            if not hotel or hotel['rooms'] <= 0:
                conn.rollback()
                return None, "No rooms available"
                
            # Decrement room availability by 1
            cursor.execute("UPDATE hotels SET rooms = rooms - 1 WHERE id = ?", (hotel_id,))
            
            # Generate Booking UID
            booking_uid = f"HB-{time.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
            booking_timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            
            # Create booking row
            cursor.execute("""
                INSERT INTO bookings (booking_uid, user_id, hotel_id, checkin, checkout, guests, room_type, amount, status, payment_status, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Confirmed', 'Paid', ?)
            """, (booking_uid, user_id, hotel_id, checkin, checkout, guests, room_type, amount, booking_timestamp))
            booking_id = cursor.lastrowid
            
            # Fetch the newly created booking to compute the booking data hash
            cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
            new_booking = dict(cursor.fetchone())
            booking_data_hash = get_booking_data_hash(new_booking)
            
            # Fetch latest blockchain block
            cursor.execute("SELECT * FROM blockchain ORDER BY id DESC LIMIT 1")
            latest_block = cursor.fetchone()
            
            new_block_id = latest_block['id'] + 1
            previous_hash = latest_block['current_hash']
            block_timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            
            # Compute block hash
            block_hash = calculate_hash(new_block_id, booking_id, previous_hash, block_timestamp, booking_data_hash)
            
            # Write to blockchain
            cursor.execute("""
                INSERT INTO blockchain (id, booking_id, previous_hash, current_hash, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (new_block_id, booking_id, previous_hash, block_hash, block_timestamp))
            
            conn.commit()
            return booking_id, None
        except Exception as e:
            conn.rollback()
            return None, str(e)
        finally:
            conn.close()

    @staticmethod
    def get_by_id(booking_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.*, u.name as customer_name, u.email as customer_email, h.hotel_name, h.city, h.address, h.contact_number, h.image
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            JOIN hotels h ON b.hotel_id = h.id
            WHERE b.id = ?
        """, (booking_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_user_history(user_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.*, h.hotel_name, h.city, h.image, h.address
            FROM bookings b
            JOIN hotels h ON b.hotel_id = h.id
            WHERE b.user_id = ?
            ORDER BY b.id DESC
        """, (user_id,))
        bookings = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return bookings

    @staticmethod
    def get_all():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.*, u.name as customer_name, h.hotel_name, h.city
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            JOIN hotels h ON b.hotel_id = h.id
            ORDER BY b.id DESC
        """)
        bookings = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return bookings

    @staticmethod
    def cancel(booking_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Get hotel_id to restore room availability
            cursor.execute("SELECT hotel_id, status FROM bookings WHERE id = ?", (booking_id,))
            booking = cursor.fetchone()
            if not booking:
                return False, "Booking not found"
            
            if booking['status'] == 'Cancelled':
                return True, None # already cancelled
                
            cursor.execute("UPDATE bookings SET status = 'Cancelled' WHERE id = ?", (booking_id,))
            cursor.execute("UPDATE hotels SET rooms = rooms + 1 WHERE id = ?", (booking['hotel_id'],))
            conn.commit()
            return True, None
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    @staticmethod
    def approve(booking_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE bookings SET status = 'Confirmed' WHERE id = ?", (booking_id,))
            conn.commit()
            return True, None
        except Exception as e:
            return False, str(e)
        finally:

            conn.close()
