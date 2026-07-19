import csv
import os

def read_csv_content(file_path):
    """
    Reads CSV file and returns content as list of dictionaries
    """
    data = []
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None
    return data

def compare_table_contents(dir1, dir2, table_name):
    """
    Compares content of two CSV files for a specific table
    """
    file1 = os.path.join(dir1, table_name)
    file2 = os.path.join(dir2, table_name)
    
    if not os.path.exists(file1) or not os.path.exists(file2):
        return f"Missing file: {file1} or {file2}"
    
    data1 = read_csv_content(file1)
    data2 = read_csv_content(file2)
    
    if data1 is None or data2 is None:
        return "Error reading files"
    
    # Compare
    if len(data1) != len(data2):
        return f"Row count differs: {len(data1)} vs {len(data2)}"
    
    differences = []
    for i, (row1, row2) in enumerate(zip(data1, data2)):
        if row1 != row2:
            differences.append(f"Row {i+1} differs: {row1} vs {row2}")
    
    return differences

# Example usage:
# Compare two export directories
dir1 = "table_exports"
dir2 = "table_exports2"

# Get list of CSV files
tables1 = [f for f in os.listdir(dir1) if f.endswith('.csv')]
tables2 = [f for f in os.listdir(dir2) if f.endswith('.csv')]

common_tables = set(tables1) & set(tables2)

for table in common_tables:
    # print(f"\n📊 Comparing {table}:")
    result = compare_table_contents(dir1, dir2, table)
    if isinstance(result, list):
        if result:
            print(f"   ⚠️ Differences found:")
            for diff in result[:5]:  # Show first 5 differences
                print(f"      {diff}")
            if len(result) > 5:
                print(f"      ... and {len(result)-5} more differences")
        # else:
        #     print(f"   ✅ No differences found")
    else:
        print(f"   ❌ {result}")