from datetime import datetime
import logging

from SekeSepidar.settings import CREATOR_SEPIDAR
from SepidarApp.databaseConnector import DatabaseConnection

logger = logging.getLogger(__name__)


def update_stock_batch(db_connection: DatabaseConnection,items,type:str = 'input',stock_ref=None):
    try:
        for item in items:
            update_stock_quantity(
                db_connection=db_connection,
                item_ref=item['item_ref'],
                value=item['withdrawal_amount'],
                operation_type=type,
                stock_ref = stock_ref
            )

        return {
            'success': True,
        }

    except:
        return {
            'success': False,
            'error': f'Error in {type} for {items} to db'
        }   


def update_stock_quantity(
    db_connection: DatabaseConnection,
    item_ref: int,
    stock_ref: int = 10,
    operation_type: str = 'input',  # 'input' or 'output'
    value: float = 0,
    fiscal_year_ref: int = 1,
    tracing_ref: int = None,
):
    """
    Update the stock quantity in ItemStockSummary table
    
    Parameters:
    - db_connection: Database connection object
    - item_ref: Item reference (required)
    - stock_ref: Stock reference (default 10)
    - operation_type: 'input' for adding to InputQuantity, 'output' for adding to OutputQuantity
    - value: Amount to add (positive float)
    - fiscal_year_ref: Fiscal year reference (default 1)
    - tracing_ref: Tracing reference (default None)
    
    Returns:
    - dict with success flag and updated data
    """
    try:
        conn = db_connection.get_connection()
        cursor = conn.cursor()
        
        # Validate parameters
        if not item_ref:
            return {
                'success': False,
                'error': 'item_ref is required'
            }
        
        if value <= 0:
            return {
                'success': False,
                'error': 'value must be greater than 0'
            }
        
        if operation_type not in ['input', 'output']:
            return {
                'success': False,
                'error': "operation_type must be 'input' or 'output'"
            }
        

        from decimal import Decimal
        decimal_value = Decimal(str(value))


        # First, check if the record exists
        cursor.execute("""
            SELECT 
                ItemStockSummaryID,
                StockRef,
                ItemRef,
                TracingRef,
                [Order],
                UnitRef,
                InputQuantity,
                OutputQuantity,
                Quantity,
                SaleQuantity,
                FiscalYearRef,
                SaleWithReserveQuantity,
                FeedFromClosingOperation
            FROM [Sepidar01].[INV].[ItemStockSummary]
            WHERE ItemRef = ? 
                AND StockRef = ? 
                AND FiscalYearRef = ?
                AND (TracingRef = ? OR (TracingRef IS NULL AND ? IS NULL))
        """, (item_ref, stock_ref, fiscal_year_ref, tracing_ref, tracing_ref))
        
        result = cursor.fetchone()
        
        now = datetime.now()
        
        if result:
            # Record exists - UPDATE
            item_stock_summary_id = result[0]
            current_input_quantity = result[6] or 0
            current_output_quantity = result[7] or 0
            current_quantity = result[8] or 0

            
            # Calculate new values
            new_input_quantity = current_input_quantity
            new_output_quantity = current_output_quantity
            new_quantity = current_quantity
            
            if operation_type == 'input':
                new_input_quantity = current_input_quantity + decimal_value
                # new_quantity = current_quantity + value
            else:  # output
                new_output_quantity = current_output_quantity + decimal_value
                # new_quantity = current_quantity - value
            
            # Update the record
            cursor.execute("""
                UPDATE [Sepidar01].[INV].[ItemStockSummary]
                SET 
                    InputQuantity = ?,
                    OutputQuantity = ?

                WHERE ItemStockSummaryID = ?
            """, (
                new_input_quantity,
                new_output_quantity,

                item_stock_summary_id
            ))
            
            conn.commit()
            
            logger.info(f"Updated stock for ItemRef={item_ref}, StockRef={stock_ref}: "
                       f"{operation_type} +{value}, New Quantity={new_quantity}")
            
            return {
                'success': True,
                'operation': operation_type,
                'item_ref': item_ref,
                'stock_ref': stock_ref,
                'old_quantity': current_quantity,
                'new_quantity': new_quantity,
                'old_input_quantity': current_input_quantity,
                'new_input_quantity': new_input_quantity,
                'old_output_quantity': current_output_quantity,
                'new_output_quantity': new_output_quantity,
                'updated_value': value,
                'item_stock_summary_id': item_stock_summary_id,
                'message': f'Stock updated successfully'
            }
            
        else:

            return {
                'success': False,
                'error': 'Item Not Exist'
            }

            # Record doesn't exist - INSERT new record
            # Get max ItemStockSummaryID
            cursor.execute("""
                SELECT ISNULL(MAX(ItemStockSummaryID), 0) 
                FROM [Sepidar01].[INV].[ItemStockSummary]
            """)
            max_result = cursor.fetchone()
            new_id = (max_result[0] + 1) if max_result else 1
            
            # Get unit reference for the item
            cursor.execute("""
                SELECT UnitRef
                FROM [Sepidar01].[INV].[Item]
                WHERE ItemID = ?
            """, (item_ref,))
            
            unit_result = cursor.fetchone()
            unit_ref = unit_result[0] if unit_result else 1
            
            # Set initial quantities based on operation type
            input_quantity = value if operation_type == 'input' else 0
            output_quantity = value if operation_type == 'output' else 0
            quantity = value if operation_type == 'input' else -value
            
            # Insert new record
            cursor.execute("""
                INSERT INTO [Sepidar01].[INV].[ItemStockSummary] (
                    ItemStockSummaryID,
                    StockRef,
                    ItemRef,
                    TracingRef,
                    [Order],
                    UnitRef,
                    InputQuantity,
                    OutputQuantity,
                    Quantity,
                    SaleQuantity,
                    FiscalYearRef,
                    SaleWithReserveQuantity,
                    FeedFromClosingOperation,
                    Creator,
                    CreationDate,
                    LastModifier,
                    LastModificationDate,
                    Version
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                new_id,
                stock_ref,
                item_ref,
                tracing_ref,
                1,  # Order (default 1)
                unit_ref,
                input_quantity,
                output_quantity,
                quantity,
                0,  # SaleQuantity (default 0)
                fiscal_year_ref,
                0,  # SaleWithReserveQuantity (default 0)
                0,  # FeedFromClosingOperation (default 0)
                CREATOR_SEPIDAR,
                now,
                CREATOR_SEPIDAR,
                now,
                1  # Version (default 1)
            ))
            
            conn.commit()
            
            logger.info(f"Created new stock record for ItemRef={item_ref}, StockRef={stock_ref}: "
                       f"{operation_type} +{value}, Quantity={quantity}")
            
            return {
                'success': True,
                'operation': operation_type,
                'item_ref': item_ref,
                'stock_ref': stock_ref,
                'new_quantity': quantity,
                'input_quantity': input_quantity,
                'output_quantity': output_quantity,
                'item_stock_summary_id': new_id,
                'message': f'New stock record created successfully'
            }
            
    except Exception as e:
        logger.error(f"Error updating stock quantity: {e}")
        if hasattr(conn, 'rollback'):
            conn.rollback()
        return {
            'success': False,
            'error': str(e)
        }


def get_stock_quantity(
    db_connection: DatabaseConnection,
    item_ref: int,
    stock_ref: int = 10,
    fiscal_year_ref: int = 1,
    tracing_ref: int = None
):
    """
    Get current stock quantity for an item
    
    Parameters:
    - db_connection: Database connection object
    - item_ref: Item reference
    - stock_ref: Stock reference (default 10)
    - fiscal_year_ref: Fiscal year reference (default 1)
    - tracing_ref: Tracing reference (optional)
    
    Returns:
    - dict with stock information
    """
    try:
        conn = db_connection.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                ItemStockSummaryID,
                StockRef,
                ItemRef,
                InputQuantity,
                OutputQuantity,
                Quantity,
                SaleQuantity,
                UnitRef
            FROM [Sepidar01].[INV].[ItemStockSummary]
            WHERE ItemRef = ? 
                AND StockRef = ? 
                AND FiscalYearRef = ?
                AND (TracingRef = ? OR (TracingRef IS NULL AND ? IS NULL))
        """, (item_ref, stock_ref, fiscal_year_ref, tracing_ref, tracing_ref))
        
        result = cursor.fetchone()
        
        if result:
            return {
                'success': True,
                'exists': True,
                'item_stock_summary_id': result[0],
                'stock_ref': result[1],
                'item_ref': result[2],
                'input_quantity': result[3] or 0,
                'output_quantity': result[4] or 0,
                'quantity': result[5] or 0,
                'sale_quantity': result[6] or 0,
                'unit_ref': result[7]
            }
        else:
            return {
                'success': True,
                'exists': False,
                'item_ref': item_ref,
                'stock_ref': stock_ref,
                'quantity': 0,
                'message': 'No stock record found'
            }
            
    except Exception as e:
        logger.error(f"Error getting stock quantity: {e}")
        return {
            'success': False,
            'error': str(e)
        }