import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'hotel.db')

def view_database():
    if not os.path.exists(DB_PATH):
        print(f"Database file not found at: {DB_PATH}")
        return
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # List of tables to display
    tables = ['users', 'hotels', 'bookings', 'blockchain']
    
    for table in tables:
        print("\n" + "="*50)
        print(f" TABLE: {table.upper()} ")
        print("="*50)
        
        try:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            
            if not rows:
                print("No records found.")
                continue
                
            # Get columns
            columns = rows[0].keys()
            print(" | ".join(columns))
            print("-" * 60)
            
            for row in rows:
                row_values = []
                for col in columns:
                    val = str(row[col])
                    # Truncate long descriptions or hashes for cleaner view
                    if len(val) > 30:
                        val = val[:27] + "..."
                    row_values.append(val)
                print(" | ".join(row_values))
                
        except sqlite3.OperationalError as e:
            print(f"Error querying table {table}: {e}")
            
    conn.close()

if __name__ == '__main__':
    view_database()
