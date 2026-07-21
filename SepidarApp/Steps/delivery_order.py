
from datetime import datetime
from venv import logger

from SekeSepidar.settings import CREATOR_SEPIDAR
from SepidarApp.databaseConnector import DatabaseConnection


def save_inventory_delivery_db(
    db_connection: DatabaseConnection,
    product_order_ref :int,
    stock_ref: int = 10,
    receiver_dl_ref: int = 5,
    destination_stock_ref: int = None,
    description: str = None,
    creator: int = CREATOR_SEPIDAR,
    type: int = 2,
    is_return: int = 0,
    total_price: float = 0,
    items:dict=None
):
    """
    ایجاد یک رسید جدید در جدول InventoryDelivery
    
    پارامترها:
    - db_connection: اتصال به دیتابیس
    - stock_ref: شناسه انبار مبدا (پیش‌فرض 10)
    - receiver_dl_ref: شناسه مرکز هزینه گیرنده (پیش‌فرض 5)
    - destination_stock_ref: شناسه انبار مقصد (اختیاری)
    - description: توضیحات
    - creator: شناسه کاربر ایجاد کننده (پیش‌فرض 16)
    - type: نوع رسید (پیش‌فرض 2)
    - is_return: آیا برگشتی است (پیش‌فرض 0)
    - total_price: قیمت کل (پیش‌فرض 0)
    
    بازگشت:
    - دیکشنری شامل اطلاعات رسید جدید
    """
    try:
        conn = db_connection.get_connection()
        cursor = conn.cursor()
        
        # 1. دریافت بزرگترین InventoryDeliveryID و Number
       
        cursor.execute("""
        UPDATE FMK.IDGeneration
        SET LastId = LastId + 1
        OUTPUT inserted.LastId
        WHERE TableName = ?
        """, ("INV.InventoryDelivery",))

        new_id = cursor.fetchone()[0]       
        
        inventory_delivery_id = new_id

        # 1. دریافت بزرگترین InventoryDeliveryID و Number
        cursor.execute("""
            SELECT 
                ISNULL(MAX(Number), 0) as MaxNumber
            FROM [Sepidar01].[INV].[InventoryDelivery]
            Where StockRef = ?
        """, (stock_ref, )
        )
        result = cursor.fetchone()

        if result:
            max_number = result[0]
            new_number = max_number + 1
        else:
            new_number = 1
        
        # 2. دریافت FiscalYearRef پیش‌فرض
        # cursor.execute("""
        #     SELECT TOP 1
        #         FiscalYearRef
        #     FROM [Sepidar01].[GNR].[FiscalYear]
        #     WHERE IsActive = 1
        #     ORDER BY FiscalYearRef DESC
        # """)
        
        # fiscal_year = cursor.fetchone()
        fiscal_year_ref =  1
        
        # 3. ساخت رکورد جدید
        now = datetime.now()
        
        new_record = {
            'InventoryDeliveryID': new_id,
            'IsReturn': is_return,
            'Type': type,
            'StockRef': stock_ref,
            'ReceiverDLRef': receiver_dl_ref,
            'Number': new_number,
            'Date': now,
            'TotalPrice': total_price,
            'AccountingVoucherRef': None,
            'FiscalYearRef': fiscal_year_ref,
            'DestinationStockRef': destination_stock_ref,
            'CreatorForm': 1,
            'Creator': creator,
            'CreationDate': now,
            'LastModifier': creator,
            'LastModificationDate': now,
            'Version': 1,
            'Description': description
        }
        
        # 4. ساخت کوئری INSERT
        columns = ', '.join(new_record.keys())
        placeholders = ', '.join(['?' for _ in new_record.keys()])
        
        query = f"""
            INSERT INTO [Sepidar01].[INV].[InventoryDelivery] ({columns})
            VALUES ({placeholders})
        """
        
        # اجرای کوئری
        cursor.execute(query, list(new_record.values()))
        conn.commit()
        
        logger.info(f"InventoryDelivery جدید با شناسه {new_id} و شماره {new_number} ایجاد شد")
        

        results = save_inventory_delivery_items_batch(db_connection=db_connection,inventory_delivery_ref=inventory_delivery_id,items=items,product_order_ref=product_order_ref)

        if not results['success']:
            if hasattr(conn, 'rollback'):
                conn.rollback()
            return {
                'success': False,
                'error': str(e)
            }


        return {
            'success': True,
            'inventory_delivery_id': new_id,
            'number': new_number,
            'data': new_record
        }
        
    except Exception as e:
        logger.error(f"Error saving inventory delivery: {e}")
        if hasattr(conn, 'rollback'):
            conn.rollback()
        return {
            'success': False,
            'error': str(e)
        }
    













def save_inventory_delivery_item_db(
    db_connection: DatabaseConnection,
    inventory_delivery_ref: int,
    item_ref: int,
    quantity: float,
    price: float = 0,
    description: str = None,
    product_order_ref: int = None,
    tracing_ref: str = None,
    secondary_quantity: float = None,
    remaining_quantity: float = None,
    sl_account_ref: int = None,
    fee: float = None,
    is_return: int = 0,
    parity_check: int = None,
    version: int = 1
):
    """
    اضافه کردن یک آیتم به رسید انبار
    
    پارامترها:
    - db_connection: اتصال به دیتابیس
    - inventory_delivery_ref: شناسه رسید انبار
    - item_ref: شناسه آیتم
    - quantity: مقدار
    - price: قیمت (پیش‌فرض 0)
    - description: توضیحات
    - product_order_ref: شناسه سفارش محصول (اختیاری)
    - tracing_ref: شناسه ردیابی (اختیاری)
    - secondary_quantity: مقدار ثانویه (اختیاری)
    - remaining_quantity: مقدار باقیمانده (اختیاری)
    - sl_account_ref: شناسه حساب (اختیاری)
    - fee: هزینه (اختیاری)
    - is_return: آیا برگشتی است (پیش‌فرض 0)
    - parity_check: چک برابری (پیش‌فرض 1)
    - version: نسخه (پیش‌فرض 1)
    
    بازگشت:
    - دیکشنری شامل اطلاعات آیتم جدید
    """
    try:
        conn = db_connection.get_connection()
        cursor = conn.cursor()
        
        # 1. دریافت آخرین InventoryDeliveryItemID        
        cursor.execute("""
        UPDATE FMK.IDGeneration
        SET LastId = LastId + 1
        OUTPUT inserted.LastId
        WHERE TableName = ?
        """, ("INV.InventoryDeliveryItem",))

        new_item_id = cursor.fetchone()[0]



        
        # 2. دریافت آخرین RowNumber برای این رسید
        cursor.execute("""
            SELECT ISNULL(MAX(RowNumber), 0) as MaxRowNumber
            FROM [Sepidar01].[INV].[InventoryDeliveryItem]
            WHERE InventoryDeliveryRef = ?
        """, (inventory_delivery_ref,))
        
        result = cursor.fetchone()
        row_number = result[0] + 1 if result else 1
        
        # 3. دریافت اطلاعات آیتم از دیتابیس (اختیاری)
        cursor.execute("""
            SELECT 
                ItemID,
                Code,
                Title
            FROM [Sepidar01].[INV].[Item]
            WHERE ItemID = ?
        """, (item_ref,))
        
        item_data = cursor.fetchone()
        item_title = item_data[2] if item_data else None
        
        # 4. ساخت رکورد جدید
        now = datetime.now()
        
        new_record = {
            'InventoryDeliveryItemID': new_item_id,
            'InventoryDeliveryRef': inventory_delivery_ref,
            'IsReturn': is_return,
            'RowNumber': row_number,
            'BaseInvoiceItem': None,
            'BaseInventoryDeliveryItem': None,
            'BaseReturnedInvoiceItem': None,
            'ItemRef': item_ref,
            'TracingRef': tracing_ref,
            'Quantity': quantity,
            'SecondaryQuantity': secondary_quantity,
            'RemainingQuantity': remaining_quantity if remaining_quantity is not None else quantity,
            'RemainingSecondaryQuantity': None,
            'SLAccountRef': sl_account_ref,
            'Price': price,
            'Description': description,
            'Description_En': None,
            'Version': version,
            'ParityCheck': parity_check,
            'QuotationItemRef': None,
            'ProductOrderRef': product_order_ref,
            'WeighingRef': None,
            'ItemRequestItemRef': None,
            'ItemDescription': item_title,
            # 'Fee': fee
        }
        
        # 5. ساخت کوئری INSERT
        columns = ', '.join(new_record.keys())
        placeholders = ', '.join(['?' for _ in new_record.keys()])
        
        query = f"""
            INSERT INTO [Sepidar01].[INV].[InventoryDeliveryItem] ({columns})
            VALUES ({placeholders})
        """
        
        # اجرای کوئری
        cursor.execute(query, list(new_record.values()))
        conn.commit()
        
        # 6. به‌روزرسانی TotalPrice در جدول InventoryDelivery
        # cursor.execute("""
        #     UPDATE [Sepidar01].[INV].[InventoryDelivery]
        #     SET TotalPrice = (
        #         SELECT ISNULL(SUM(Quantity * Price), 0)
        #         FROM [Sepidar01].[INV].[InventoryDeliveryItem]
        #         WHERE InventoryDeliveryRef = ?
        #     )
        #     WHERE InventoryDeliveryID = ?
        # """, (inventory_delivery_ref, inventory_delivery_ref))
        # conn.commit()
        
        logger.info(f"InventoryDeliveryItem جدید با شناسه {new_item_id} برای رسید {inventory_delivery_ref} ایجاد شد")
        
        return {
            'success': True,
            'inventory_delivery_item_id': new_item_id,
            'inventory_delivery_ref': inventory_delivery_ref,
            'row_number': row_number,
            'data': new_record
        }
        
    except Exception as e:
        logger.error(f"Error saving inventory delivery item: {e}")
        if hasattr(conn, 'rollback'):
            conn.rollback()
        return {
            'success': False,
            'error': str(e)
        }


def save_inventory_delivery_items_batch(
    db_connection: DatabaseConnection,
    inventory_delivery_ref: int,
    items: list,
    product_order_ref: int = None,
    default_price: float = 0,
    default_description: str = None
):
    """
    اضافه کردن چندین آیتم به رسید انبار به صورت دسته‌ای
    
    پارامترها:
    - db_connection: اتصال به دیتابیس
    - inventory_delivery_ref: شناسه رسید انبار
    - items: لیستی از دیکشنری‌ها شامل اطلاعات آیتم‌ها
    - product_order_ref: شناسه سفارش محصول (اختیاری)
    - default_price: قیمت پیش‌فرض
    - default_description: توضیحات پیش‌فرض
    
    ساختار items:
    [
        {
            'item_ref': 1958,
            'quantity': 33,
            'price': 0,
            'description': 'مربوط به سفارش تولید محصول شماره 2171',
            'product_order_ref': 2171
        }
    ]
    
    بازگشت:
    - دیکشنری شامل نتایج
    """
    try:
        results = []
        all_success = True
        
        for item in items:
            result = save_inventory_delivery_item_db(
                db_connection=db_connection,
                inventory_delivery_ref=inventory_delivery_ref,
                item_ref=item.get('item_ref'),
                quantity=item.get('withdrawal_amount', 0),
                price=item.get('price', default_price),
                description=item.get('description', default_description),
                product_order_ref=item.get('product_order_ref', product_order_ref),
                tracing_ref=item.get('tracing_ref'),
                secondary_quantity=item.get('secondary_quantity'),
                remaining_quantity=item.get('remaining_quantity'),
                sl_account_ref=item.get('sl_account_ref'),
                fee=item.get('fee'),
                is_return=item.get('is_return', 0)
            )
            
            results.append(result)
            if not result['success']:
                all_success = False
        
        return {
            'success': all_success,
            'results': results,
            'total': len(items),
            'saved': sum(1 for r in results if r['success']),
            'failed': sum(1 for r in results if not r['success']),
            'inventory_delivery_ref': inventory_delivery_ref
        }
        
    except Exception as e:
        logger.error(f"Error saving batch items: {e}")
        return {
            'success': False,
            'error': str(e)
        }