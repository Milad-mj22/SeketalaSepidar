import pyodbc

def get_table_structure(connection_string=None):
    """
    Get the actual column structure of the ProductOrderBOMItem table
    """
    if connection_string is None:
        connection_string = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=DESKTOP-JKDSDCN\\SEPIDAR;"
            "DATABASE=Sepidar01;"
            "Trusted_Connection=yes;"
        )
    
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        # Get column information
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'WKO' 
            AND TABLE_NAME = 'ProductOrderBOMItem'
            ORDER BY ORDINAL_POSITION
        """)
        
        columns = cursor.fetchall()
        print("="*60)
        print("ACTUAL COLUMN STRUCTURE:")
        print("="*60)
        for col in columns:
            print(f"Column: {col[0]:<30} Type: {col[1]:<20} Nullable: {col[2]}")
        
        cursor.close()
        conn.close()
        return columns
        
    except Exception as e:
        print(f"❌ Error getting table structure: {str(e)}")
        return None

# First, let's check the actual table structure
print("Checking table structure...")
get_table_structure()