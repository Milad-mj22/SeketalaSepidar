from datetime import datetime
from venv import logger

from SekeSepidar.settings import CREATOR_SEPIDAR
from SepidarApp.databaseConnector import DatabaseConnection


def save_inventory_receipt_db(
    db_connection: DatabaseConnection,
    stock_ref: int,
    deliverer_dl_ref: int,
    sl_account_ref: int = None,
    purchase_type: int = 1,          # Default, adjust as needed
    is_return: int = 0,
    type: int = 1,                   # Default receipt type
    total_price: float = 0,
    total_tax: float = 0,
    total_duty: float = 0,
    total_transport_price: float = 0,
    total_net_price: float = 0,
    total_returned_price: float = 0,
    total_returned_net_price: float = 0,
    total_other_cost: float = 0,
    is_wastage: int = 0,
    description: str = None,
    creator: int = CREATOR_SEPIDAR,
    payment_header_ref: int = None,
    transport_broker_sl_account_ref: int = None,
    transporter_dl_ref: int = None,
    base_purchase_invoice_ref: int = None,
    base_inventory_delivery_ref: int = None,
    base_import_purchase_invoice_ref: int = None,
    items: dict = None               # optional items for detail insertion
):
    """
    Create a new receipt record in the InventoryReceipt table.

    Parameters:
    - db_connection: Database connection object
    - stock_ref: Warehouse reference (source)
    - deliverer_dl_ref: Deliverer / supplier DL reference
    - sl_account_ref: Related SL account (optional)
    - purchase_type: Type of purchase (default 1)
    - is_return: Is this a return receipt (default 0)
    - type: Receipt type (default 1)
    - total_price, total_tax, total_duty, total_transport_price, total_net_price,
      total_returned_price, total_returned_net_price, total_other_cost: totals
    - is_wastage: Wastage flag (default 0)
    - description: Optional description
    - creator: User ID who creates the record
    - payment_header_ref, transport_broker_sl_account_ref, transporter_dl_ref,
      base_purchase_invoice_ref, base_inventory_delivery_ref,
      base_import_purchase_invoice_ref: optional foreign keys
    - items: Dictionary of items to be inserted via a separate batch function

    Returns:
    - dict with success flag, new ID, number, and inserted data
    """
    try:
        conn = db_connection.get_connection()
        cursor = conn.cursor()

        # 1. Get max InventoryReceiptID and Number (per StockRef)
        cursor.execute("""
            SELECT 
                ISNULL(MAX(InventoryReceiptID), 0) as MaxID,
                ISNULL(MAX(Number), 0) as MaxNumber
            FROM [Sepidar01].[INV].[InventoryReceipt]
            WHERE StockRef = ?
        """, (stock_ref,))
        result = cursor.fetchone()

        if result:
            max_id = result[0]
            new_id = max_id + 1
            max_number = result[1]
            new_number = max_number + 1
        else:
            new_id = 1
            new_number = 1

        # 2. FiscalYearRef (default 1, or query active fiscal year)
        fiscal_year_ref = 1   # adjust as needed

        # 3. Current timestamp
        now = datetime.now()

        # 4. Build the new record dictionary
        new_record = {
            'InventoryReceiptID': new_id,
            'IsReturn': is_return,
            'Type': type,
            'PurchaseType': purchase_type,
            'StockRef': stock_ref,
            'DelivererDLRef': deliverer_dl_ref,
            'SLAccountRef': sl_account_ref,
            'Number': new_number,
            'Date': now,
            'AccountingVoucherRef': None,   # can be set later
            'PaymentHeaderRef': payment_header_ref,
            'TransportBrokerSLAccountRef': transport_broker_sl_account_ref,
            'TransporterDLRef': transporter_dl_ref,
            'TotalPrice': total_price,
            'TotalTax': total_tax,
            'TotalDuty': total_duty,
            'TotalTransportPrice': total_transport_price,
            'TotalNetPrice': total_net_price,
            'FiscalYearRef': fiscal_year_ref,
            'CreatorForm': 1,
            'Creator': creator,
            'CreationDate': now,
            'LastModifier': creator,
            'LastModificationDate': now,
            'Version': 1,
            'BasePurchaseInvoiceRef': base_purchase_invoice_ref,
            'BaseInventoryDeliveryRef': base_inventory_delivery_ref,
            'TotalReturnedPrice': total_returned_price,
            'TotalReturnedNetPrice': total_returned_net_price,
            'BaseImportPurchaseInvoiceRef': base_import_purchase_invoice_ref,
            'Description': description,
            'TotalOtherCost': total_other_cost,
            'IsWastage': is_wastage
        }

        # 5. Insert the header
        columns = ', '.join(new_record.keys())
        placeholders = ', '.join(['?' for _ in new_record])
        query = f"""
            INSERT INTO [Sepidar01].[INV].[InventoryReceipt] ({columns})
            VALUES ({placeholders})
        """
        cursor.execute(query, list(new_record.values()))
        conn.commit()

        logger.info(f"InventoryReceipt created with ID {new_id}, Number {new_number}")

        # 6. If items are provided, insert them via a batch function
        # if items:
        #     items_result = save_inventory_receipt_items_batch(
        #         db_connection=db_connection,
        #         inventory_receipt_ref=new_id,
        #         items=items
        #         # you may also pass other needed parameters (e.g., product_order_ref)
        #     )
        #     if not items_result.get('success', False):
        #         conn.rollback()
        #         return {
        #             'success': False,
        #             'error': f"Failed to insert items: {items_result.get('error')}"
        #         }

        return {
            'success': True,
            'inventory_receipt_id': new_id,
            'number': new_number,
            'data': new_record
        }

    except Exception as e:
        logger.error(f"Error saving inventory receipt: {e}")
        if hasattr(conn, 'rollback'):
            conn.rollback()
        return {
            'success': False,
            'error': str(e)
        }