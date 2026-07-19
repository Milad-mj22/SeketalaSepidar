import pyodbc
import csv
import os

# ============================
# Database connection settings
# ============================
server = r'localhost'
database = 'Sepidar01'
driver = '{ODBC Driver 17 for SQL Server}'

connection_string = (
    f"DRIVER={driver};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"Trusted_Connection=yes;"
)

# ============================
# Function to export table data to CSV
# ============================
def export_table_to_csv(cursor, schema, table, output_dir="table_exports2"):
    """
    Exports all data from a table to a CSV file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    full_table_name = f"[{schema}].[{table}]"
    csv_filename = f"{schema}_{table}.csv"
    csv_path = os.path.join(output_dir, csv_filename)
    
    try:
        # Get column names
        cursor.execute(f"""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = '{schema}' 
            AND TABLE_NAME = '{table}'
            ORDER BY ORDINAL_POSITION
        """)
        columns = [row[0] for row in cursor.fetchall()]
        
        # Get all data
        cursor.execute(f"SELECT * FROM {full_table_name}")
        
        # Write to CSV
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(columns)  # Write header
            
            # Write rows
            row_count = 0
            for row in cursor.fetchall():
                writer.writerow(row)
                row_count += 1
        
        return csv_path, row_count
    
    except Exception as e:
        print(f"❌ Error exporting {schema}.{table}: {e}")
        return None, 0

# ============================
# Export all tables
# ============================
try:
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    print("✅ SQL Server connection successful")
    
    # Get all tables (not views)
    cursor.execute("""
        SELECT TABLE_SCHEMA, TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
    """)
    
    tables = cursor.fetchall()
    print(f"📊 Found {len(tables)} tables")
    
    output_dir = "table_exports2"
    summary_file = "export_summary.txt"
    
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write(f"Database: {database}\n")
        f.write("=" * 80 + "\n")
        f.write(f"{'Schema.Table':50} | {'Records':10} | {'File'}\n")
        f.write("-" * 80 + "\n")
        
        total_tables = 0
        total_records = 0
        
        for schema, table in tables:
            print(f"📤 Exporting {schema}.{table}...")
            
            csv_path, row_count = export_table_to_csv(cursor, schema, table, output_dir)
            
            if csv_path:
                total_tables += 1
                total_records += row_count
                f.write(f"{schema}.{table:48} | {row_count:10} | {csv_path}\n")
                print(f"   ✅ Exported {row_count} rows to {csv_path}")
            else:
                f.write(f"{schema}.{table:48} | {'ERROR':10} | Failed\n")
                print(f"   ❌ Failed to export {schema}.{table}")
        
        f.write("-" * 80 + "\n")
        f.write(f"\nTotal tables exported: {total_tables}\n")
        f.write(f"Total records exported: {total_records}\n")
    
    print(f"\n✅ Export complete! Summary saved to: {summary_file}")
    print(f"📁 All CSV files saved in: {output_dir}/")

except Exception as e:
    print("❌ Error:", e)
    import traceback
    traceback.print_exc()

finally:
    if 'conn' in locals():
        conn.close()
        print("🔒 Connection closed")