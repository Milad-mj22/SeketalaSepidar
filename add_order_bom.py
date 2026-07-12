import pyodbc

def insert_all_bom_items(connection_string=None):
    """
    Insert all 12 BOM items directly from your sample data
    Using the actual column structure
    """
    
    if connection_string is None:
        connection_string = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=DESKTOP-JKDSDCN\\SEPIDAR;"
            "DATABASE=Sepidar01;"
            "Trusted_Connection=yes;"
        )
    
    # Your exact data from the sample
    # Format: (ItemRef, FormulaBOMItemRef, StandardConsumptionQuantity, RemainingConsumptionQuantity, Description, TransferedQuantity, ItemTracingRef)
    items = [
        (1859, 502, 2377.0000, None, None, 0.0000, None),
        (1863, 504, 21.3930, None, None, 0.0000, None),
        (1922, 500, 95.0800, None, None, 0.0000, None),
        (1971, 497, 35.6550, None, None, 0.0000, None),
        (1979, 498, 71.3100, None, None, 0.0000, None),
        (1980, 499, 83.1950, None, None, 0.0000, None),
        (2021, 508, 2377.0000, None, None, 0.0000, None),
        (2105, 501, 2377.0000, None, None, 0.0000, None),
        (2175, 507, 213.9300, None, None, 0.0000, None),
        (2180, 506, 166.3900, None, None, 0.0000, None),
        (2187, 505, 2377.0000, None, None, 0.0000, None),
        (2221, 503, 2377.0000, None, None, 0.0000, None)
    ]
    
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        
        # Get next ID
        cursor.execute("SELECT ISNULL(MAX(ProductOrderBOMItemID), 0) FROM [Sepidar01].[WKO].[ProductOrderBOMItem]")
        next_id = cursor.fetchone()[0]
        print(f"Starting ProductOrderBOMItemID: {next_id + 1}")
        print("="*60)
        
        # Insert query with actual columns
        insert_query = """
            INSERT INTO [Sepidar01].[WKO].[ProductOrderBOMItem] (
                ProductOrderBOMItemID,
                ProductOrderRef,
                ItemRef,
                FormulaBOMItemRef,
                StandardConsumptionQuantity,
                RemainingConsumptionQuantity,
                Description,
                TransferedQuantity,
                ItemTracingRef
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        inserted_count = 0
        for idx, item in enumerate(items):
            bom_id = next_id + idx + 1
            
            params = (
                bom_id,                    # ProductOrderBOMItemID
                2189,                      # ProductOrderRef (you can change this)
                item[0],                   # ItemRef
                item[1],                   # FormulaBOMItemRef
                item[2],                   # StandardConsumptionQuantity
                item[3],                   # RemainingConsumptionQuantity
                item[4],                   # Description
                item[5],                   # TransferedQuantity
                item[6]                    # ItemTracingRef
            )
            
            cursor.execute(insert_query, params)
            inserted_count += 1
            print(f"✅ Inserted item {inserted_count}: ItemRef={item[0]}, FormulaBOMItemRef={item[1]}, Quantity={item[2]} (ID: {bom_id})")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("="*60)
        print(f"✅ Successfully inserted all {inserted_count} BOM items for ProductOrderRef=2134!")
        return {'success': True, 'count': inserted_count}
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return {'success': False, 'error': str(e)}

# Run it
result = insert_all_bom_items()
print(f"\nFinal result: {result}")