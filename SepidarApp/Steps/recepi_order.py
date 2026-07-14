from datetime import datetime
from venv import logger

from SekeSepidar.settings import CREATOR_SEPIDAR
from SepidarApp.databaseConnector import DatabaseConnection


def save_inventory_receipt_db(
    db_connection: DatabaseConnection,
    product_order_ref : int,
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
            SELECT MAX(InventoryReceiptID)
            FROM [Sepidar01].[INV].[InventoryReceipt]
        """)
        result = cursor.fetchone()
        last_id = result[0] if result[0] is not None else 0

        if last_id:
            new_id = last_id + 1
        else:
            new_id = 1

        # 2. FiscalYearRef (default 1, or query active fiscal year)
        fiscal_year_ref = 1   # adjust as needed



        # 1. دریافت بزرگترین InventoryDeliveryID و Number
        cursor.execute("""
            SELECT 
                ISNULL(MAX(Number), 0) as MaxNumber
            FROM [Sepidar01].[INV].[InventoryReceipt]
            Where StockRef = ?
        """, (stock_ref, )
        )
        result = cursor.fetchone()

        if result:
            max_number = result[0]
            new_number = max_number + 1
        else:
            new_number = 1
        



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
        if items:
            items_result = save_inventory_receipt_items_batch(
                db_connection=db_connection,
                inventory_receipt_ref=new_id,
                items=items,
                product_order_ref = product_order_ref

                # you may also pass other needed parameters (e.g., product_order_ref)
            )
            if not items_result.get('success', False):
                conn.rollback()
                return {
                    'success': False,
                    'error': f"Failed to insert items: {items_result.get('error')}"
                }

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
    











def save_inventory_receipt_items_batch(
    db_connection: DatabaseConnection,
    inventory_receipt_ref: int,
    items: list = None,
    product_order_ref: int = None,
    is_return: int = 0,
    currency_ref: int = 1,  # Default currency (e.g., IRR)
    currency_rate: float = 1.0,
    version: int = 1
):
    """
    Insert multiple items into InventoryReceiptItem table in batch
    
    Parameters:
    - db_connection: Database connection object
    - inventory_receipt_ref: Reference to the parent InventoryReceipt
    - items: List of dictionaries, each containing item data:
        {
            'item_ref': int,           # ItemRef (required)
            'quantity': float,         # Quantity (required)
            'price': float,            # Unit price (required)
            'secondary_quantity': float, # Optional
            'tax': float,              # Optional
            'duty': float,             # Optional
            'transport_price': float,  # Optional
            'description': str,        # Optional
            'base_purchase_invoice_item_ref': int, # Optional
            'inventory_delivery_item_ref': int, # Optional
            # Any other fields as needed
        }
    - product_order_ref: Reference to product order (optional)
    - is_return: Is this a return item (default 0)
    - currency_ref: Currency reference (default 1)
    - currency_rate: Currency rate (default 1.0)
    - version: Version number (default 1)
    
    Returns:
    - dict with success flag, inserted count, and list of IDs
    """
    try:
        conn = db_connection.get_connection()
        cursor = conn.cursor()
        
        if not items:
            logger.warning("No items provided for inventory receipt items batch")
            return {
                'success': True,
                'inserted_count': 0,
                'items': []
            }
        
        # Get max InventoryReceiptItemID
        cursor.execute("""
            SELECT ISNULL(MAX(InventoryReceiptItemID), 0) 
            FROM [Sepidar01].[INV].[InventoryReceiptItem]
        """)
        result = cursor.fetchone()
        max_id = result[0] if result else 0
        
        inserted_items = []
        now = datetime.now()
        
        # Prepare query
        query = """
            INSERT INTO [Sepidar01].[INV].[InventoryReceiptItem] (
                InventoryReceiptItemID,
                InventoryReceiptRef,
                IsReturn,
                RowNumber,
                Base,
                ReturnBase,
                ItemRef,
                TracingRef,
                Quantity,
                SecondaryQuantity,
                RemainingQuantity,
                RemainingSecondaryQuantity,
                CurrencyRef,
                CurrencyRate,
                CurrencyValue,
                Price,
                Tax,
                Duty,
                TransportPrice,
                TransportTax,
                TransportDuty,
                TransportDescription,
                Description,
                Description_En,
                Version,
                BasePurchaseInvoiceItemRef,
                ParityCheck,
                ProductOrderRef,
                InventoryDeliveryItemRef,
                WeighingRef,
                TaxCurrencyValue,
                DutyCurrencyValue,
                ReturnedPrice,
                Fee,
                ReturnedFee,
                OtherCostsAmount,
                ServiceInventoryPurchaseInvoiceRef,
                ImportOrderFinalFee,
                BaseImportPurchaseInvoiceItemRef,
                AllotmenedOtherCostInBaseCurrency,
                NetPrice,
                ReturnedNetPrice
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """
        
        # Process each item
        for idx, item in enumerate(items):
            item_id = max_id + idx + 1
            
            # Calculate derived values
            quantity = item.get('quantity', 0)
            price = item.get('price', 0)
            tax = item.get('tax', 0)
            duty = item.get('duty', 0)
            transport_price = item.get('transport_price', 0)
            
            # Calculate net price: Price + Tax + Duty + TransportPrice
            net_price = price + tax + duty + transport_price
            
            # Calculate remaining quantities (usually same as initial)
            remaining_quantity = item.get('remaining_quantity', quantity)
            remaining_secondary_quantity = item.get('remaining_secondary_quantity', 
                                                     item.get('secondary_quantity', 0))
            
            # Base values (for returns)
            base = item.get('base', 0)
            return_base = item.get('return_base', 0)
            
            # Currency values
            currency_value = price * currency_rate if price else 0
            
            # Other calculated fields
            tax_currency_value = tax * currency_rate if tax else 0
            duty_currency_value = duty * currency_rate if duty else 0
            returned_price = item.get('returned_price', 0)
            returned_net_price = item.get('returned_net_price', 0)
            fee = item.get('fee', 0)
            returned_fee = item.get('returned_fee', 0)
            other_costs_amount = item.get('other_costs_amount', 0)
            import_order_final_fee = item.get('import_order_final_fee', 0)
            allotmened_other_cost_in_base_currency = item.get('allotmened_other_cost_in_base_currency', 0)
            
            # Values to insert
            values = (
                item_id,                                    # InventoryReceiptItemID
                inventory_receipt_ref,                     # InventoryReceiptRef
                is_return,                                 # IsReturn
                idx + 1,                                   # RowNumber
                base,                                      # Base
                return_base,                               # ReturnBase
                item.get('item_ref'),                      # ItemRef
                item.get('tracing_ref'),                   # TracingRef
                quantity,                                  # Quantity
                item.get('secondary_quantity', 0),         # SecondaryQuantity
                remaining_quantity,                        # RemainingQuantity
                remaining_secondary_quantity,              # RemainingSecondaryQuantity
                currency_ref,                              # CurrencyRef
                currency_rate,                             # CurrencyRate
                currency_value,                            # CurrencyValue
                price,                                     # Price
                tax,                                       # Tax
                duty,                                      # Duty
                transport_price,                           # TransportPrice
                item.get('transport_tax', 0),              # TransportTax
                item.get('transport_duty', 0),             # TransportDuty
                item.get('transport_description'),         # TransportDescription
                item.get('description'),                   # Description
                item.get('description_en'),                # Description_En
                version,                                   # Version
                item.get('base_purchase_invoice_item_ref'), # BasePurchaseInvoiceItemRef
                item.get('parity_check'),                  # ParityCheck
                product_order_ref,                         # ProductOrderRef
                item.get('inventory_delivery_item_ref'),   # InventoryDeliveryItemRef
                item.get('weighing_ref'),                  # WeighingRef
                tax_currency_value,                        # TaxCurrencyValue
                duty_currency_value,                       # DutyCurrencyValue
                returned_price,                            # ReturnedPrice
                fee,                                       # Fee
                returned_fee,                              # ReturnedFee
                other_costs_amount,                        # OtherCostsAmount
                item.get('service_inventory_purchase_invoice_ref'), # ServiceInventoryPurchaseInvoiceRef
                import_order_final_fee,                    # ImportOrderFinalFee
                item.get('base_import_purchase_invoice_item_ref'), # BaseImportPurchaseInvoiceItemRef
                allotmened_other_cost_in_base_currency,    # AllotmenedOtherCostInBaseCurrency
                net_price,                                 # NetPrice
                returned_net_price                         # ReturnedNetPrice
            )
            
            cursor.execute(query, values)
            inserted_items.append({
                'inventory_receipt_item_id': item_id,
                'row_number': idx + 1,
                'item_ref': item.get('item_ref'),
                'quantity': quantity,
                'price': price,
                'net_price': net_price
            })
        
        conn.commit()
        logger.info(f"Inserted {len(inserted_items)} items for InventoryReceipt {inventory_receipt_ref}")
        
        return {
            'success': True,
            'inserted_count': len(inserted_items),
            'items': inserted_items
        }
        
    except Exception as e:
        logger.error(f"Error saving inventory receipt items: {e}")
        if hasattr(conn, 'rollback'):
            conn.rollback()
        return {
            'success': False,
            'error': str(e),
            'inserted_count': 0
        }