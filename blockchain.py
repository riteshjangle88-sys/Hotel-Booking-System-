import hashlib
import time

class Block:
    def __init__(self, index, booking_id, previous_hash, timestamp, current_hash=None):
        self.index = index
        self.booking_id = booking_id
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.current_hash = current_hash or self.calculate_block_hash("")

    def calculate_block_hash(self, booking_data_hash):
        return calculate_hash(self.index, self.booking_id, self.previous_hash, self.timestamp, booking_data_hash)

def calculate_hash(index, booking_id, previous_hash, timestamp, booking_data_hash):
    """
    Generates a SHA-256 hash for a block.
    """
    # Use string representations to avoid None values causing errors
    b_id = str(booking_id) if booking_id is not None else "0"
    header_string = f"{index}-{b_id}-{previous_hash}-{timestamp}-{booking_data_hash}"
    return hashlib.sha256(header_string.encode('utf-8')).hexdigest()

def get_booking_data_hash(booking_row):
    """
    Computes a cryptographic hash of the critical booking details to bind them to the blockchain.
    booking_row is expected to be a dictionary-like object (sqlite3.Row or dict) containing:
    booking_uid, user_id, hotel_id, checkin, checkout, guests, room_type, amount, status
    """
    if not booking_row:
        return ""
    
    # Capture critical fields that should not be tampered with
    booking_str = (
        f"{booking_row['booking_uid']}-"
        f"{booking_row['user_id']}-"
        f"{booking_row['hotel_id']}-"
        f"{booking_row['checkin']}-"
        f"{booking_row['checkout']}-"
        f"{booking_row['guests']}-"
        f"{booking_row['room_type']}-"
        f"{booking_row['amount']}-"
        f"{booking_row['status']}"
    )
    return hashlib.sha256(booking_str.encode('utf-8')).hexdigest()

def verify_chain(conn):
    """
    Validates the entire blockchain stored in the database.
    Returns: (is_valid, list of verification status details)
    """
    cursor = conn.cursor()
    
    # Fetch all blockchain entries ordered by id
    cursor.execute("SELECT * FROM blockchain ORDER BY id ASC")
    blocks = [dict(row) for row in cursor.fetchall()]
    
    # Fetch all bookings with user name and hotel name for visual display
    cursor.execute("""
        SELECT b.*, u.name as customer_name, h.hotel_name 
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        JOIN hotels h ON b.hotel_id = h.id
    """)
    bookings = {row['id']: dict(row) for row in cursor.fetchall()}
    
    validation_details = []
    
    if not blocks:
        return False, [{"status": "Error", "message": "Blockchain is empty! No Genesis Block found."}]
    
    is_valid = True
    
    # Verify Genesis Block (first block, index should be 1)
    genesis = blocks[0]
    genesis_id = genesis['id']
    genesis_booking_id = genesis['booking_id']
    genesis_prev_hash = genesis['previous_hash']
    genesis_curr_hash = genesis['current_hash']
    genesis_timestamp = genesis['timestamp']
    
    # Genesis should have previous_hash = "0" and booking_id = None or 0
    computed_genesis_hash = calculate_hash(genesis_id, genesis_booking_id, genesis_prev_hash, genesis_timestamp, "GENESIS_DATA")
    
    genesis_status = {
        "id": genesis_id,
        "booking_id": genesis_booking_id,
        "previous_hash": genesis_prev_hash,
        "current_hash": genesis_curr_hash,
        "computed_hash": computed_genesis_hash,
        "timestamp": genesis_timestamp,
        "status": "Valid",
        "message": "Genesis Block is valid."
    }
    
    if genesis_prev_hash != "0":
        genesis_status["status"] = "Tampered"
        genesis_status["message"] = f"Genesis Block previous hash is '{genesis_prev_hash}' instead of '0'."
        is_valid = False
    elif genesis_curr_hash != computed_genesis_hash:
        genesis_status["status"] = "Tampered"
        genesis_status["message"] = f"Genesis Block hash is invalid. Expected: {computed_genesis_hash}, Found: {genesis_curr_hash}"
        is_valid = False
        
    validation_details.append(genesis_status)
    
    # Verify subsequent blocks
    for i in range(1, len(blocks)):
        prev_block = blocks[i-1]
        block = blocks[i]
        
        b_id = block['id']
        booking_id = block['booking_id']
        prev_hash = block['previous_hash']
        curr_hash = block['current_hash']
        timestamp = block['timestamp']
        
        block_status = {
            "id": b_id,
            "booking_id": booking_id,
            "previous_hash": prev_hash,
            "current_hash": curr_hash,
            "timestamp": timestamp,
            "status": "Valid",
            "message": "Block is valid."
        }
        
        # 1. Check if previous hash links match
        if prev_hash != prev_block['current_hash']:
            block_status["status"] = "Tampered"
            block_status["message"] = f"Chain link broken! Block previous_hash ({prev_hash[:12]}...) doesn't match preceding block current_hash ({prev_block['current_hash'][:12]}...)."
            is_valid = False
            validation_details.append(block_status)
            continue
            
        # 2. Check if booking exists and data hash matches
        booking = bookings.get(booking_id)
        if not booking:
            block_status["status"] = "Tampered"
            block_status["message"] = f"Booking records missing for Booking ID {booking_id} reference."
            is_valid = False
            booking_data_hash = ""
        else:
            booking_data_hash = get_booking_data_hash(booking)
            block_status["booking_uid"] = booking["booking_uid"]
            block_status["hotel_name"] = booking["hotel_name"]
            block_status["customer_name"] = booking["customer_name"]
            block_status["amount"] = booking["amount"]
            
        # 3. Calculate current block hash and verify integrity
        computed_hash = calculate_hash(b_id, booking_id, prev_hash, timestamp, booking_data_hash)
        block_status["computed_hash"] = computed_hash
        
        if curr_hash != computed_hash:
            block_status["status"] = "Tampered"
            block_status["message"] = f"Booking record data has been tampered! Stored data does not match blockchain transaction hash."
            is_valid = False
            
        validation_details.append(block_status)
        
    return is_valid, validation_details
    