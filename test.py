# simple_sqlite.py
import sqlite3
import os

# 1. Database path (change this to your actual path)
DB_PATH = 'my_database_copy.db'  # or your full path like '/path/to/your/database.db'

# 2. Connect to database
def get_connection():
    """Create and return a database connection"""
    # Create directory if it doesn't exist
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
    
    # Connect to SQLite
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    return conn

# 3. Read all records from ProductFormula
def read_product_formula():
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Execute query
        cursor.execute("SELECT * FROM ProductFormula")
        
        # Fetch all results
        rows = cursor.fetchall()
        
        # Display results
        print(f"\n✅ Found {len(rows)} records in ProductFormula table:\n")
        print("-" * 80)
        
        if rows:
            # Get column names
            columns = [description[0] for description in cursor.description]
            print(" | ".join(columns))
            print("-" * 80)
            
            for row in rows:
                # Convert row to dict for easy access
                record = dict(row)
                print(f"ID: {record.get('ProductFormulaID')}")
                print(f"Code: {record.get('Code')}")
                print(f"Title: {record.get('Title')}")
                print(f"Quantity: {record.get('Quantity')}")
                print(f"Active: {record.get('IsActive')}")
                print("-" * 40)
        
        return rows
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

# 4. Main function
def main():
    print("🔄 Connecting to SQLite database...")
    
    # Check if database file exists
    if not os.path.exists(DB_PATH):
        print(f"⚠️ Database file not found: {DB_PATH}")
        print("Creating new database file...")
    
    # Read data
    results = read_product_formula()
    
    if results:
        print(f"\n✅ Successfully read {len(results)} records")
    else:
        print("\n⚠️ No records found or table doesn't exist")
    
    print("\n🔒 Connection closed.")

# Run it
if __name__ == "__main__":
    main()