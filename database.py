import sqlite3
import os
import time
from werkzeug.security import generate_password_hash
from blockchain import calculate_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'hotel.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        )
    """)
    
    # 2. Hotels Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hotels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hotel_name TEXT NOT NULL,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            address TEXT NOT NULL,
            description TEXT NOT NULL,
            price INTEGER NOT NULL,
            rooms INTEGER NOT NULL,
            image TEXT,
            gallery TEXT,
            rating REAL NOT NULL DEFAULT 4.0,
            amenities TEXT,
            contact_number TEXT,
            maps_link TEXT
        )
    """)
    
    # 3. Bookings Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_uid TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            hotel_id INTEGER NOT NULL,
            checkin TEXT NOT NULL,
            checkout TEXT NOT NULL,
            guests INTEGER NOT NULL,
            room_type TEXT NOT NULL,
            amount INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            payment_status TEXT NOT NULL DEFAULT 'Paid',
            timestamp TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (hotel_id) REFERENCES hotels (id)
        )
    """)
    
    # 4. Blockchain Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blockchain (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER,
            previous_hash TEXT NOT NULL,
            current_hash TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    
    conn.commit()
    
    # --- SEED DATA ---
    
    # Seed Users (if empty)
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        admin_pass = generate_password_hash("admin123")
        user_pass = generate_password_hash("user123")
        cursor.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                       ("Admin User", "admin@hotelchain.in", admin_pass, "admin"))
        cursor.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                       ("Rohan Sharma", "rohan@gmail.com", user_pass, "user"))
        conn.commit()
        
    # Seed Hotels (if empty)
    cursor.execute("SELECT COUNT(*) FROM hotels")
    if cursor.fetchone()[0] == 0:
        sample_hotels = [
            (
                "Taj Mahal Palace", "Mumbai", "Maharashtra", 
                "Apollo Bandar, Colaba, Mumbai, Maharashtra 400001",
                "World-famous luxury heritage hotel overlooking the Arabian Sea and the Gateway of India. A legendary symbol of Indian hospitality since 1903.",
                18500, 15, "images/hotel1.jpg", 
                "images/room1.jpg,images/room2.jpg,images/room3.jpg",
                5.0, "Swimming Pool, Sea View, Luxury Spa, Free WiFi, 9 Fine Dining Restaurants, Fitness Center, 24/7 Butler Service",
                "+91-22-66653366", "https://maps.google.com/?q=Taj+Mahal+Palace+Mumbai"
            ),
            (
                "The Oberoi", "New Delhi", "Delhi",
                "Dr Zakir Hussain Marg, New Delhi, Delhi 110003",
                "Offering sweeping views of the Delhi Golf Club and Humayun's Tomb, this modern luxury hotel represents the gold standard of luxury hotel stays.",
                14500, 20, "images/hotel2.jpg",
                "images/room2.jpg,images/room3.jpg,images/room1.jpg",
                4.9, "Heated Pools, High-speed WiFi, Spa & Wellness, Business Lounge, 24/7 Room Service, Gourmet Restaurant",
                "+91-11-24363030", "https://maps.google.com/?q=The+Oberoi+New+Delhi"
            ),
            (
                "ITC Grand Chola", "Chennai", "Tamil Nadu",
                "63, Anna Salai, Guindy, Chennai, Tamil Nadu 600032",
                "An architectural tribute to the ancient Chola Dynasty, this palace hotel stands as one of India's largest luxury hotels with stunning stone carvings and royal grandeur.",
                9500, 25, "images/hotel3.jpg",
                "images/room3.jpg,images/room1.jpg,images/room2.jpg",
                4.8, "3 Swimming Pools, Spa, 10 Dining Outlets, Free WiFi, Fitness Hub, Royal Banquet Halls",
                "+91-44-22200000", "https://maps.google.com/?q=ITC+Grand+Chola+Chennai"
            ),
            (
                "The Leela Palace", "Bengaluru", "Karnataka",
                "23, HAL Old Airport Rd, Bengaluru, Karnataka 560008",
                "Nestled in nine acres of lush, tranquil gardens, this resort-style palace hotel features architectural styling inspired by the Royal Palace of Mysore.",
                12500, 18, "images/hotel4.jpg",
                "images/room1.jpg,images/room3.jpg,images/room2.jpg",
                4.9, "Mysore Palace Architecture, Royal Spa, Lush Gardens, Free WiFi, Outdoor Pool, Fine Dining Restaurants, Lounge Bar",
                "+91-80-25211234", "https://maps.google.com/?q=The+Leela+Palace+Bengaluru"
            ),
            (
                "Rambagh Palace", "Jaipur", "Rajasthan",
                "Bhawani Singh Rd, Jaipur, Rajasthan 302005",
                "The former residence of the Maharaja of Jaipur, Rambagh Palace offers rich heritage, manicured lawns, and opulent suites. Experience the true royal treatment.",
                24000, 8, "images/hotel1.jpg",
                "images/room2.jpg,images/room3.jpg,images/room1.jpg",
                5.0, "Heritage Palace Rooms, Royal Welcomes, Peacocks on Gardens, Indoor Pool, Spa, Polo Bar, Vintage Horse Carriage Ride",
                "+91-141-2385700", "https://maps.google.com/?q=Rambagh+Palace+Jaipur"
            ),
            (
                "Novotel Candolim", "Goa", "Goa",
                "Anna Waddo, Main Candolim Rd, Candolim, Goa 403515",
                "Located close to the pristine Candolim beach in North Goa, this resort offers a relaxing tropical vibe, poolside bars, and vibrant nightlife nearby.",
                7500, 30, "images/hotel2.jpg",
                "images/room3.jpg,images/room1.jpg,images/room2.jpg",
                4.5, "Close to Beach, Pool with Sunken Bar, Free WiFi, Kids Area, Spa, All-Day Buffet, Beach Activities",
                "+91-832-7110000", "https://maps.google.com/?q=Novotel+Candolim+Goa"
            ),
            (
                "Sterling Ooty Elk Hill", "Ooty", "Tamil Nadu",
                "Ramakrishna Puram, Elk Hill, Ooty, Tamil Nadu 643004",
                "Perched high on the mist-covered slopes of Elk Hill, this beautiful resort offers spectacular views of Ooty town and the surrounding valley.",
                5200, 20, "images/hotel3.jpg",
                "images/room1.jpg,images/room2.jpg,images/room3.jpg",
                4.4, "Scenic Mountain Views, Organic Garden Tour, Campfire Nights, Indoor Gaming, Multi-cuisine Restaurant, WiFi",
                "+91-423-2452848", "https://maps.google.com/?q=Sterling+Ooty+Elk+Hill"
            ),
            (
                "Vivanta Dal View", "Srinagar", "Jammu & Kashmir",
                "Kralsangri, Brein, Srinagar, Jammu and Kashmir 190001",
                "Perched on Kralsangri hill, Vivanta Dal View offers panoramic vistas of the Dal Lake and the Zabarwan range. The ultimate Kashmiri luxury retreat.",
                11500, 12, "images/hotel4.jpg",
                "images/room2.jpg,images/room1.jpg,images/room3.jpg",
                4.8, "Dal Lake View, Heated Pool, Kashmiri Wazwan Dining, Outdoor Terrace, Free WiFi, Shikara Booking Desk",
                "+91-194-2461111", "https://maps.google.com/?q=Vivanta+Dal+View+Srinagar"
            )
        ]
        cursor.executemany("""
            INSERT INTO hotels (
                hotel_name, city, state, address, description, price, rooms, image, gallery, rating, amenities, contact_number, maps_link
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_hotels)
        conn.commit()
        
    # Seed Genesis Block in Blockchain (if empty)
    cursor.execute("SELECT COUNT(*) FROM blockchain")
    if cursor.fetchone()[0] == 0:
        genesis_timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        # calculate genesis hash: index = 1, booking_id = None, prev_hash = "0"
        genesis_hash = calculate_hash(1, None, "0", genesis_timestamp, "GENESIS_DATA")
        cursor.execute("""
            INSERT INTO blockchain (id, booking_id, previous_hash, current_hash, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (1, None, "0", genesis_hash, genesis_timestamp))
        conn.commit()
        
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database successfully initialized and seeded!")
