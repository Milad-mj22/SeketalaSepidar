import pyodbc



def delete_bom_items_by_order(product_order_ref, connection_string=None):
    """
    Delete all BOM items for a specific ProductOrderRef
    
    Args:
        product_order_ref: The ProductOrderRef to delete (e.g., 2189)
        connection_string: Optional connection string
        
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'deleted_count': int,
            'error': str (if failed)
        }
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
        
        # First, check how many records will be deleted
        cursor.execute(
            "SELECT COUNT(*) FROM [Sepidar01].[WKO].[ProductOrderBOMItem] WHERE ProductOrderRef = ?",
            (product_order_ref,)
        )
        count = cursor.fetchone()[0]
        
        if count == 0:
            cursor.close()
            conn.close()
            return {
                'success': True,
                'message': f'No BOM items found for ProductOrderRef={product_order_ref}',
                'deleted_count': 0,
                'error': None
            }
        
        print(f"Found {count} BOM items for ProductOrderRef={product_order_ref}")
        print("="*60)
        
        # Show what will be deleted
        cursor.execute(
            "SELECT ProductOrderBOMItemID, ItemRef, StandardConsumptionQuantity FROM [Sepidar01].[WKO].[ProductOrderBOMItem] WHERE ProductOrderRef = ?",
            (product_order_ref,)
        )
        items = cursor.fetchall()
        for item in items:
            print(f"  - ID: {item[0]}, ItemRef: {item[1]}, Quantity: {item[2]}")
        
        print("="*60)
        
        # Confirm deletion (optional - remove this if you want automatic deletion)
        confirm = input(f"Are you sure you want to delete these {count} items? (yes/no): ")
        if confirm.lower() != 'yes':
            cursor.close()
            conn.close()
            return {
                'success': False,
                'message': 'Deletion cancelled by user',
                'deleted_count': 0,
                'error': None
            }
        
        # Delete the records
        cursor.execute(
            "DELETE FROM [Sepidar01].[WKO].[ProductOrderBOMItem] WHERE ProductOrderRef = ?",
            (product_order_ref,)
        )
        
        conn.commit()
        deleted_count = cursor.rowcount
        
        cursor.close()
        conn.close()
        
        print(f"✅ Successfully deleted {deleted_count} BOM items for ProductOrderRef={product_order_ref}")
        
        return {
            'success': True,
            'message': f'Successfully deleted {deleted_count} BOM items for ProductOrderRef={product_order_ref}',
            'deleted_count': deleted_count,
            'error': None
        }
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return {
            'success': False,
            'message': 'Failed to delete BOM items',
            'deleted_count': 0,
            'error': str(e)
        }


if __name__=='__main__':
    delete_bom_items_by_order(product_order_ref=2189)