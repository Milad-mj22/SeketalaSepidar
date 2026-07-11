import pyodbc

def delete_product_order(product_order_id, connection_string=None):
    """
    Delete a ProductOrder record by ID
    
    Args:
        product_order_id (int): The ID of the order to delete
        connection_string (str, optional): ODBC connection string
        
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'rows_affected': int,
            'error': str (if failed)
        }
    """
    
    # ===== DEFAULT CONNECTION STRING =====
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
        
        # ===== CHECK IF RECORD EXISTS =====
        cursor.execute(
            "SELECT COUNT(*) FROM [Sepidar01].[WKO].[ProductOrder] WHERE ProductOrderID = ?",
            [product_order_id]
        )
        count = cursor.fetchone()[0]
        
        if count == 0:
            cursor.close()
            conn.close()
            return {
                'success': False,
                'message': f'ProductOrder with ID {product_order_id} not found',
                'rows_affected': 0,
                'error': 'Record not found'
            }
        
        # ===== DELETE THE RECORD =====
        query = "DELETE FROM [Sepidar01].[WKO].[ProductOrder] WHERE ProductOrderID = ?"
        cursor.execute(query, [product_order_id])
        conn.commit()
        
        rows_affected = cursor.rowcount
        
        cursor.close()
        conn.close()
        
        return {
            'success': True,
            'message': f'ProductOrder with ID {product_order_id} deleted successfully',
            'rows_affected': rows_affected,
            'error': None
        }
        
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        return {
            'success': False,
            'message': 'Failed to delete ProductOrder',
            'rows_affected': 0,
            'error': str(e)
        }


# ===== TEST =====
result = delete_product_order(1951)
print(result)