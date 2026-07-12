
import pyodbc

# ============================
# Database connection settings
# ============================
# Replace with your server and database details
server = 'DESKTOP-JKDSDCN\SEPIDAR' # E.g., 'localhost' or 'server_name\instance_name'
database ='Sepidar01'
driver = '{ODBC Driver 17 for SQL Server}' # Make sure you have the correct driver installed


connection_string = (
    f"DRIVER={driver};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"Trusted_Connection=yes;"
)

print('first')

output_file = "database_tables_record_count_4.txt"

try:
    # Connect to SQL Server
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    print("✅ SQL Server connection successful")
    print('first')

    # Get all base tables
    cursor.execute("""
        SELECT TABLE_SCHEMA, TABLE_NAME
        FROM INFORMATION_SCHEMA.Views

    """)

    tables = cursor.fetchall()
    print('first')

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"Database: {database}\n")
        f.write("=" * 60 + "\n")
        f.write(f"{'Schema.Table':40} | Records\n")
        f.write("-" * 60 + "\n")

        for schema, table in tables:
            full_table_name = f"[{schema}].[{table}]"

            try:
                cursor.execute(f"SELECT COUNT(*) FROM {full_table_name}")
                row_count = cursor.fetchone()[0]
            except Exception as count_error:
                row_count = f"ERROR: {count_error}"

            f.write(f"{schema}.{table:36} | {row_count}\n")

    print(f"📄 Table record counts saved to: {output_file}")

except Exception as e:
    print("❌ Error:", e)

finally:
    if 'conn' in locals():
        conn.close()
