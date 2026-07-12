import pyodbc

def insert_product_order(data=None, connection_string=None):
    """
    Insert a new record into ProductOrder table
    
    Args:
        data (dict, optional): Dictionary containing field values to override defaults
        connection_string (str, optional): ODBC connection string
        
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'order_id': int (if success),
            'number': int (if success),
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
        
        # ===== GET NEXT ProductOrderID =====
        cursor.execute("SELECT ISNULL(MAX(ProductOrderID), 0) + 1 FROM [Sepidar01].[WKO].[ProductOrder]")
        next_id = cursor.fetchone()[0]
        print(f"Next ProductOrderID: {next_id}")
        
        # ===== GET NEXT Number =====
        cursor.execute("SELECT ISNULL(MAX(Number), 0) + 1 FROM [Sepidar01].[WKO].[ProductOrder]")
        next_number = cursor.fetchone()[0]
        print(f"Next Number: {next_number}")
        
        # ===== DEFAULT VALUES =====
        default_values = {
            'ProductOrderID': next_id,
            'Number': next_number,  # ✅ مقدار خودکار برای Number
            'Date': 'GETDATE()',
            'BaseProductOrderRef': None,
            'CostCenterRef': 7,
            'ProductRef': 2084,
            'ProductFormulaRef': 69,
            'Quantity': 1.0000,
            'WastageQuantity': 0.0000,
            'CustomerPartyRef': None,
            'State': 1,
            'RemainingBOMCost': None,
            'BOMCost': None,
            'EstimatedLabourCost': None,
            'EstimatedOverheadCost': None,
            'FiscalYearRef': 1,
            'CanTransferNextPeriod': 0,
            'IsInitial': 0,
            'Creator': 10,
            'CreationDate': 'GETDATE()',
            'LastModifier': 10,
            'LastModificationDate': 'GETDATE()',
            'Version': 1,
            'IndirectMaterialsCost': None,
            'BaseQuotationItemRef': None,
            'TracingTitle': None,
            'ProductFormulaUnitRef': 2,
            # 'Cost': 0.0000  # ❌ Computed Column - حذف شده
        }
        
        # ===== MERGE WITH PROVIDED DATA =====
        if data:
            # حذف فیلدهای محاسباتی از داده‌های ورودی
            computed_columns = ['Cost']
            filtered_data = {k: v for k, v in data.items() 
                           if v is not None and k not in computed_columns}
            
            # اگر ProductOrderID در داده‌ها باشد، از آن استفاده کن
            if 'ProductOrderID' in filtered_data:
                default_values['ProductOrderID'] = filtered_data.pop('ProductOrderID')
            
            # اگر Number در داده‌ها باشد، از آن استفاده کن
            if 'Number' in filtered_data:
                default_values['Number'] = filtered_data.pop('Number')
            
            default_values.update(filtered_data)
        
        # ===== BUILD QUERY =====
        fields = []
        values = []
        params = []
        sql_functions = ['GETDATE()']
        
        for field, value in default_values.items():
            fields.append(field)
            
            if isinstance(value, str) and value in sql_functions:
                values.append(value)
            else:
                values.append('?')
                params.append(value)
        
        query = f"""
            INSERT INTO [Sepidar01].[WKO].[ProductOrder] (
                {', '.join(fields)}
            )
            VALUES (
                {', '.join(values)}
            )
        """
        
        print(f"Executing query: {query}")
        print(f"Params: {params}")
        
        cursor.execute(query, params)
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return {
            'success': True,
            'message': f'ProductOrder created successfully with ID: {next_id} and Number: {next_number}',
            'order_id': next_id,
            'number': next_number,
            'error': None
        }
        
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        return {
            'success': False,
            'message': 'Failed to create ProductOrder',
            'order_id': None,
            'number': None,
            'error': str(e)
        }


# ===== TEST =====
a = insert_product_order()
print(a)