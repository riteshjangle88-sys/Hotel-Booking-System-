# Vedic Stay - Blockchain-Based Hotel Booking System

A secure, premium hotel booking web application built with Python Flask, SQLite, and custom SHA-256 blockchain verification logic. Vedic Stay ensures transaction data integrity, blocking unauthorized database tampering or fraud.

---

## 🏛️ Architectural Overview

Vedic Stay addresses database integrity by locking booking agreements inside a cryptographic ledger:

1. **SQLite Core Tables**: Holds standard tables for `users`, `hotels`, and `bookings` to manage business logic.
2. **SHA-256 Ledger Table**: A `blockchain` table where every row references a booking transaction, sealing its immutable fields (UID, customer, hotel, dates, and price in INR) alongside the `previous_hash` of the preceding block.
3. **Chain Verification**: An audit loop checks that:
   - Block pointer sequences are continuous (block `i`'s previous hash pointer matches block `i-1`'s current hash).
   - Local table records match the sealed hash value.
   - Genesis conditions are valid.
4. **Simulator**: Allows administrators to bypass controllers to corrupt database rows (simulating SQL injection or direct DB manipulation), instantly flagging the specific block in red.

---

## 🛠️ Technology Stack

- **Backend**: Python 3, Flask
- **Database**: SQLite 3
- **Frontend**: HTML5, CSS3 (Vanilla Custom Theme), Bootstrap 5, FontAwesome Icons
- **Integrations**: 
  - [Chart.js](https://www.chartjs.org/) (Admin metrics graphs)
  - [html2pdf.js](https://github.com/eKoopmans/html2pdf.js/) (Client-side invoice PDF generation)
  - [qrcode.js](https://github.com/davidshimjs/qrcodejs) (Cryptographic verification QR codes)

---

## 📁 File Structure

```text
HotelBookingBlockchain/
├── .env.example            # Sample environment variables template
├── .gitignore              # Git ignore rules for Python, DB & venv
├── app.py                  # Main Flask controller & views
├── blockchain.py           # Block creation & verification ledger logic
├── database.py             # SQLite schemas & seed values
├── download_images.py      # Utility to fetch royalty-free hotel imagery
├── models.py               # User, Hotel, and Booking database models
├── requirements.txt        # PIP dependencies
├── README.md               # Setup & architectural documentation
├── view_db.py              # CLI helper to inspect database records
├── hotel.db                # Auto-generated database file (excluded from git)
├── static/
│   ├── css/
│   │   └── style.css       # Custom premium Royal India hotel theme
│   ├── js/
│   │   └── script.js       # Form validation, live booking calculator, QR, PDF
│   └── images/             # Preloaded luxury hotel assets
│       ├── logo.png
│       ├── hero.jpg
│       ├── hotel1.jpg
│       ├── hotel2.jpg
│       ├── hotel3.jpg
│       ├── hotel4.jpg
│       ├── room1.jpg
│       ├── room2.jpg
│       ├── room3.jpg
│       └── banner.jpg
└── templates/              # HTML layout blocks and views
    ├── layout.html
    ├── index.html
    ├── register.html
    ├── login.html
    ├── dashboard.html
    ├── hotels.html
    ├── booking.html
    ├── history.html
    ├── admin_login.html
    ├── admin_dashboard.html
    ├── add_hotel.html
    ├── edit_hotel.html
    ├── view_blockchain.html
    ├── bookings.html
    ├── users.html
    └── 404.html
```

---

## 🚀 Installation & Running

### 1. Install Dependencies
Install dependencies from the workspace directory:
```bash
pip install -r requirements.txt
```

### 2. Run the Web Server
Launch the Flask development server:
```bash
python app.py
```

### 3. Open the Application
Navigate your browser to:
[http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🔑 Demo Account Credentials

The application initializes with sample data, including standard and administrative accounts:

### 👤 Guest User
- **Email**: `rohan@gmail.com`
- **Password**: `user123`

### 🔑 Administrator Portal
- **Email**: `admin@hotelchain.in`
- **Password**: `admin123`

---

## 🔒 Verification & Tampering Walkthrough

To experience the security features of the ledger:

1. **Book a stay**: Log in as `rohan@gmail.com` and book a deluxe room at **Taj Mahal Palace**.
2. **Access Admin Panel**: Log out, then log in as `admin@hotelchain.in`.
3. **Audit Ledger**: Click **Blockchain Ledger** in the navbar. All blocks will show in green as **VALID**.
4. **Simulate Tampering**: 
   - Scroll to the **Database Tampering Simulator** panel.
   - Choose Rohan's booking from the list and click **Hack Price**.
   - This subtracts ₹5,000 directly from the booking record in the SQL database without recalculating the blockchain block's hash.
5. **View Integrity Alerts**: 
   - The status banner will change to **CORRUPT / TAMPERED**.
   - The altered block is highlighted in red, indicating that the database price has been tampered with.
6. **Heal the Chain**: Click **Re-seal Chain (Repair)**. The admin controller will re-calculate the cryptographic pointer hashes to seal the new state, bringing the ledger back to a healthy green state.
