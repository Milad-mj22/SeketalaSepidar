import pyodbc
from datetime import datetime
from decimal import Decimal
import logging

from SekeSepidar.settings import CREATOR_SEPIDAR
from SepidarApp.Steps.delivery_order import save_inventory_delivery_db
from SepidarApp.Steps.recepi_order import save_inventory_receipt_db
from SepidarApp.Steps.update_quantity import update_stock_batch
from SepidarApp.databaseConnector import DatabaseConnection

logger = logging.getLogger(__name__)

def save_product_order_db(db_connection:DatabaseConnection, formula_id, product_id, withdrawal_amount, material_details, quantity=1,
                          stock_source_ref=None , stock_dest_ref=None):
    """
    ذخیره یک رکورد جدید در جدول ProductOrder
    
    پارامترها:
    - conn: اتصال به دیتابیس
    - formula_id: شناسه فرمول
    - product_id: شناسه محصول
    - withdrawal_amount: میزان برداشتی (مقدار مصرفی)
    - product_name: نام محصول (اختیاری)
    - quantity: تعداد (پیش‌فرض 1)
    
    بازگشت:
    - دیکشنری شامل اطلاعات رکورد جدید
    """
    try:
        conn = db_connection.get_connection()
        cursor = conn.cursor()
        
        # 1. دریافت آخرین ProductOrderID و Number
        cursor.execute("""
            SELECT TOP 1 
                ProductOrderID,
                Number
            FROM [Sepidar01].[WKO].[vwProductOrder]
            ORDER BY ProductOrderID DESC
        """)
        
        last_record = cursor.fetchone()
        
        if last_record:
            new_id = last_record[0] + 1
            new_number = last_record[1] + 1
        else:
            new_id = 1
            new_number = 1


        cursor.execute("""
        UPDATE FMK.IDGeneration
        SET LastId = LastId + 1
        OUTPUT inserted.LastId
        WHERE TableName = ?
        """, ("WKO.ProductOrder",))

        new_id = cursor.fetchone()[0]




        product_order_ref = new_id
        # 2. دریافت اطلاعات فرمول و محصول از دیتابیس
        cursor.execute("""
            SELECT 
                f.Code as FormulaCode,
                f.Title as FormulaTitle,
                f.Quantity as FormulaQuantity,
                f.ItemUnitRef as FormulaUnitRef,
                u.Title as FormulaUnitTitle,
                f.EstimatedLabour,
                f.EstimatedOverhead,
                f.TracingCategoryRef,
                f.TracingTitle,
                p.Code as ProductCode,
                p.Title as ProductTitle,
                p.UnitRef as ProductUnitRef,
                pu.Title as ProductUnitTitle,
                p.ItemID as ProductID    
            FROM [Sepidar01].[WKO].[vwProductFormula] f
            LEFT JOIN [Sepidar01].[INV].[Unit] u ON f.ItemUnitRef = u.UnitID
            LEFT JOIN [Sepidar01].[INV].[vwItem] p ON f.ItemRef = p.ItemID  
            LEFT JOIN [Sepidar01].[INV].[Unit] pu ON p.UnitRef = pu.UnitID
            WHERE f.ProductFormulaID = ?
        """, (formula_id,))
        
        formula_data = cursor.fetchone()
        
        if not formula_data:
            raise ValueError(f"فرمول با شناسه {formula_id} یافت نشد")
        
        # 3. دریافت اطلاعات اضافی محصول
        product_id = formula_data[-1]
        if product_id:
            cursor.execute("""
                SELECT 
                    ItemID,
                    Code,
                    Title,
                    UnitRef
                FROM [Sepidar01].[INV].[vwItem]
                WHERE ItemID = ?
            """, (product_id,))
            product_data = cursor.fetchone()
        else:
            product_data = None
        
        # # 4. دریافت اطلاعات CostCenter پیش‌فرض
        # cursor.execute("""
        #     SELECT TOP 1
        #         CostCenterid,
        #         DLRef,
        #         CostCenterDLTitle,
        #         CostCenterDLTitle_En,
        #         CostCenterDLCode
        #     FROM [Sepidar01].[GNR].[CostCenter]
    
        #     ORDER BY CostCenterRef
        # """)
        
        # cost_center =(1,5,'توليدي (آماده سازي)','توليدي (آماده سازي)',1101)
        cost_center =(7,18,'واحد عمومي توليد (آشپزخانه)','واحد عمومي توليد (آشپزخانه)',1103)


        
        # 5. ساخت رکورد جدید
        now = datetime.now()
        fiscal_year = now.year  # یا از تنظیمات سیستم بگیرید
        
        # محاسبه هزینه‌ها بر اساس میزان برداشتی
        base_cost =quantity
        
        # محاسبه هزینه‌های تخمینی
        estimated_labour = formula_data[5] or 0  # EstimatedLabour
        estimated_overhead = formula_data[6] or 0  # EstimatedOverhead
        if product_data==None:
            return None

        # ایجاد دیکشنری داده‌ها
        new_record = {
            'ProductOrderID': new_id,
            'Number': new_number,
            'Date': now,
            'BaseProductOrderRef': None,
            # 'BaseProductOrderNumber': None,
            'CostCenterRef': cost_center[0] if cost_center else None,
            # 'CostCenterDLRef': cost_center[1] if cost_center else None,
            # 'CostCenterDLTitle': cost_center[2] if cost_center else None,
            # 'CostCenterDLTitle_En': cost_center[3] if cost_center else None,
            # 'CostCenterDLCode': cost_center[4] if cost_center else None,
            'ProductRef': product_data[0] if product_data else None,
            # 'ProductCode': product_data[1] if product_data else None,
            # 'ProductTitle': product_data[2] if product_data else None,
            # 'ProductTitle_En': product_data[2] if product_data else None,
            'ProductFormulaRef': formula_id,
            # 'ProductFormulaCode': formula_data[0],
            # 'ProductFormulaTitle': formula_data[1],
            # 'ProductFormulaQuantity': 1,  # مقدار برداشتی
            # 'ProductFormulaUnitRef': formula_data[3],
            # 'ProductFormulaUnitTitle_En' : formula_data[3],
            # 'ProductFormulaUnitTitle': formula_data[4],
            # 'CustomerPartyRef': None,
            # 'CustomerPartyDLCode': None,
            # 'CustomerPartyDLTitle': None,
            # 'CustomerPartyTitle_En': None,
            'Quantity': quantity,
            # 'ActualQuantity': quantity,
            # 'AbNormalWastageQuantity': 0,
            'WastageQuantity': 0,
            'CustomerPartyRef': None,
            'State': 1,  # 1 = فعال
            # 'RemainingBOMCost': None,
            # 'BOMCost': None,
            # 'EstimatedLabourCost': estimated_labour * withdrawal_amount if estimated_labour else 0,
            # 'EstimatedOverheadCost': estimated_overhead * withdrawal_amount if estimated_overhead else 0,
            # 'TransferedBOMCost': None,
            'BOMCost': None,
            'RemainingBOMCost': None,
            # 'BOMPercent': 0,
            # 'CurrentYearBOMCost': None,
            'EstimatedLabourCost': None,
            'EstimatedOverheadCost':None ,# estimated_overhead * withdrawal_amount if estimated_overhead else 0,
            # 'Cost': 0,
            # 'EstimatedLabourPercent': 0,
            # 'EstimatedOverheadPercent': 0,
            # 'IndirectMaterialsPercent': 0,
            # 'IndirectMaterialsCost': 0,
            # 'BaseQuotationItemNumber': None,
            # 'BaseQuotationItemRef': None,
            # 'TracingCategoryRef':None,# formula_data[7] if len(formula_data) > 7 else None,
            # 'TracingTitle': None,#formula_data[8] if len(formula_data) > 8 else None,
            'FiscalYearRef': 1,
            'CanTransferNextPeriod': 0,
            'IsInitial': 0,
            'Creator': CREATOR_SEPIDAR,  # یا کاربر فعلی
            'CreationDate': now,
            'LastModifier': CREATOR_SEPIDAR,
            'LastModificationDate': now,
            'Version': 1,
            # 'ProductFormulaEstimatedLabour': estimated_labour,
            # 'ProductFormulaEstimatedOverhead': estimated_overhead,
            # 'ProdcutOperationNumber': None,
            # 'CostPerUnit':  0,
            # 'ActualAndWastageQuantity': quantity,
            # 'BOMRate': 0,
            # 'EstimatedLabourRate': 0,
            # 'IndirectMaterialsRate': 0,
            # 'EstimatedOverheadRate': 0
            'IndirectMaterialsCost':None,
            'BaseQuotationItemRef':None,
            'TracingTitle': None,#formula_data[8] if len(formula_data) > 8 else None,

            'ProductFormulaUnitRef': formula_data[3],

        }


        # 6. ساخت کوئری INSERT
        columns = ', '.join(new_record.keys())
        placeholders = ', '.join(['?' for _ in new_record.keys()])
        
        query = f"""
            INSERT INTO [Sepidar01].[WKO].[ProductOrder] ({columns})
            VALUES ({placeholders})
        """
        
        # تبدیل داده‌ها به لیست برای اجرا
        values = list(new_record.values())
        

        

        # اجرای کوئری
        cursor.execute(query, values)
        conn.commit()
        


        logger.info(f"[Sepidar01].[WKO].[ProductOrder] جدید با شناسه {new_id} و شماره {new_number} ایجاد شد")




        # ===== ذخیره مواد اولیه =====
        if material_details:
            material_result = save_material_of_order_db(
                db_connection=db_connection,
                product_order_id=new_id,
                formula_id = formula_id,
                material_details=material_details
            )
            
            if not material_result['success']:
                logger.warning(f"خطا در ذخیره مواد اولیه: {material_result.get('error')}")
                # می‌توانید تصمیم بگیرید که آیا در صورت خطا، کل تراکنش را rollback کنید
                conn.rollback()
                return {
                    'success': False,
                    'error': f"خطا در ذخیره مواد: {material_result.get('error')}"
                }
        
        logger.info(f"ProductOrder جدید با شناسه {new_id} و شماره {new_number} ایجاد شد")



        ############### STEP2 ############# CREATE INVENTORY DELIVERY RECORD
        description = f'مربوط به سفارش توليد محصول شماره {product_order_ref}'
        delivery =  save_inventory_delivery_db(db_connection=db_connection,product_order_ref=product_order_ref, stock_ref=stock_source_ref, receiver_dl_ref=5, total_price=0, is_return=0, type=1, destination_stock_ref=None, creator=15, description=description,items=material_details)
        if not delivery['success']:
            logger.warning(f"خطا در ذخیره InventoryDelivery: {delivery.get('error')}")
            conn.rollback()
            return {
                'success': False,
                'error': f"خطا در ذخیره InventoryDelivery: {delivery.get('error')}"
            }
        
        
        
        ############### STEP3 ########### CREATE RECEPI ORDER
        TEMP_STOCK_REF = 10
        TEMP_DELIVERER_REF = 5
        items = {'item_ref':product_id,quantity:quantity}
        recepi = save_inventory_receipt_db(db_connection=db_connection,product_order_ref=product_order_ref,stock_ref=stock_dest_ref,deliverer_dl_ref=TEMP_DELIVERER_REF,items=material_details,number_product_order_ref=new_number)
        if not recepi['success']:
            logger.warning(f"خطا در ذخیره recepi: {recepi.get('error')}")
            conn.rollback()
            return {
                'success': False,
                'error': f"خطا در ذخیره recepi: {recepi.get('error')}"
            }
        
        
        ############# STEP4 ############# UPDATE INVOICE QUANTITY

        ret_update = update_stock_batch(db_connection=db_connection,items=material_details,type='output',stock_ref=stock_source_ref)
        if not ret_update['success']:
            logger.warning(f"خطا در ذخیره update: {ret_update.get('error')}")
            conn.rollback()
            return {
                'success': False,
                'error': f"خطا در ذخیره update: {ret_update.get('error')}"
            }


        final_product = [{'item_ref':product_id,'withdrawal_amount':quantity}]
        ret_update = update_stock_batch(db_connection=db_connection,items=final_product,type='input',stock_ref=stock_dest_ref)
        if not ret_update['success']:
            logger.warning(f"خطا در ذخیره update: {ret_update.get('error')}")
            conn.rollback()
            return {
                'success': False,
                'error': f"خطا در ذخیره update: {ret_update.get('error')}"
            }





        return {
            'success': True,
            'product_order_id': new_id,
            'product_name' : product_data[2] if product_data else None,
            'number': new_number,
            'data': new_record
        }
        
    except Exception as e:
        logger.error(f"Error saving product order: {e}")
        conn.rollback()
        return {
            'success': False,
            'error': str(e)
        }


def save_multiple_product_orders(conn, orders_data,stock_source_ref,stock_dest_ref):
    """
    ذخیره چندین سفارش محصول به صورت همزمان
    
    پارامترها:
    - conn: اتصال به دیتابیس
    - orders_data: لیستی از دیکشنری‌ها شامل:
        {
            'formula_id': 55,
            'product_id': 2196,
            'withdrawal_amount': 2.5,
            'product_name': 'سس سالاد ژامبون و پنير',
            'quantity': 86
        }
    
    بازگشت:
    - دیکشنری شامل نتایج
    """
    results = []
    all_success = True
    
    for order in orders_data:

        

        result = save_product_order_db(
            db_connection=conn,
            formula_id=order.get('formula_id'),
            product_id=order.get('product_id'),
            withdrawal_amount=order.get('total_withdrawal'),
            material_details=order.get('withdrawal_items'),
            quantity=order.get('consumption_value', 0),
            stock_source_ref = stock_source_ref,
            stock_dest_ref = stock_dest_ref,
        )
        
        results.append(result)
        if not result['success']:
            all_success = False
    

    


    return {
        'success': all_success,
        'results': results,
        'total': len(orders_data),
        'saved': sum(1 for r in results if r['success']),
        'failed': sum(1 for r in results if not r['success']),
        
    }


def get_last_order_numbers(conn):
    """
    دریافت آخرین ProductOrderID و Number
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                ISNULL(MAX(ProductOrderID), 0) as LastID,
                ISNULL(MAX(Number), 0) as LastNumber
            FROM ProductOrder
        """)
        
        result = cursor.fetchone()
        return {
            'last_id': result[0] if result else 0,
            'last_number': result[1] if result else 0,
            'next_id': (result[0] + 1) if result else 1,
            'next_number': (result[1] + 1) if result else 1
        }
    except Exception as e:
        logger.error(f"Error getting last order numbers: {e}")
        return {
            'last_id': 0,
            'last_number': 0,
            'next_id': 1,
            'next_number': 1
        }


def get_formula_details_by_id(conn, formula_id):
    """
    دریافت جزئیات کامل فرمول برای استفاده در سفارش
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                f.FormulaID,
                f.Code,
                f.Title,
                f.Quantity,
                f.UnitRef,
                u.Title as UnitTitle,
                f.EstimatedLabour,
                f.EstimatedOverhead,
                f.TracingCategoryRef,
                f.TracingTitle,
                f.ProductRef,
                p.Code as ProductCode,
                p.Title as ProductTitle,
                p.ItemRef as ProductItemRef
            FROM Formulas f
            LEFT JOIN Units u ON f.UnitRef = u.UnitRef
            LEFT JOIN Products p ON f.ProductRef = p.ProductRef
            WHERE f.FormulaID = ?
        """, (formula_id,))
        
        result = cursor.fetchone()
        if result:
            return {
                'success': True,
                'data': {
                    'formula_id': result[0],
                    'code': result[1],
                    'title': result[2],
                    'quantity': result[3],
                    'unit_ref': result[4],
                    'unit_title': result[5],
                    'estimated_labour': result[6],
                    'estimated_overhead': result[7],
                    'tracing_category_ref': result[8],
                    'tracing_title': result[9],
                    'product_ref': result[10],
                    'product_code': result[11],
                    'product_title': result[12],
                    'product_item_ref': result[13]
                }
            }
        else:
            return {
                'success': False,
                'error': f'فرمول با شناسه {formula_id} یافت نشد'
            }
    except Exception as e:
        logger.error(f"Error getting formula details: {e}")
        return {
            'success': False,
            'error': str(e)
        }
    


def save_material_of_order_db(db_connection: DatabaseConnection, product_order_id: int,formula_id:int, material_details: list):
    """
    ذخیره مواد اولیه یک سفارش در جدول ProductOrderBOMItem
    
    پارامترها:
    - db_connection: اتصال به دیتابیس
    - product_order_id: شناسه سفارش محصول (ProductOrderID)
    - material_details: لیستی از دیکشنری‌های شامل اطلاعات مواد
    
    ساختار material_details:
    [
        {
            'item_ref': '1958',
            'item_name': 'كاهو',
            'quantity': 1.5,  # مقدار در هر واحد فرمول
            'withdrawal_amount': 33  # مقدار برداشتی کل
        }
    ]
    
    بازگشت:
    - دیکشنری شامل نتایج
    """
    try:
        conn = db_connection.get_connection()
        cursor = conn.cursor()
        
        if not material_details:
            logger.warning("هیچ ماده‌ای برای ذخیره وجود ندارد")
            return {
                'success': True,
                'message': 'هیچ ماده‌ای برای ذخیره وجود ندارد',
                'saved_count': 0
            }
        
        saved_count = 0
        saved_items = []
        




        
        # 2. برای هر ماده، اطلاعات کامل را از دیتابیس دریافت کن
        for idx, material in enumerate(material_details):
            item_ref = material.get('item_ref')
            item_name = material.get('item_name')
            quantity_per_unit = material.get('quantity', 0)  # مقدار در هر واحد فرمول
            withdrawal_amount = material.get('withdrawal_amount', 0)  # مقدار برداشتی کل
            
            if not item_ref:
                logger.warning(f"ماده {idx} دارای item_ref نمی‌باشد، رد شد")
                continue
            
            # دریافت اطلاعات کامل آیتم از دیتابیس
            cursor.execute("""
                SELECT 
                    i.ItemID,
                    i.Code,
                    i.Title,
                    i.Title_En,
                    i.UnitRef,
                    u.Title as UnitTitle,
                    u.Title_En as UnitTitle_En,
                    i.TracingCategoryRef,
                    i.SecondaryUnitRef,
                    i.SerialTracking
                FROM [Sepidar01].[INV].[Item] i
                LEFT JOIN [Sepidar01].[INV].[Unit] u ON i.UnitRef = u.UnitID
                WHERE i.ItemID = ?
            """, (item_ref,))
            
            item_data = cursor.fetchone()
            
            if not item_data:
                logger.warning(f"آیتم با شناسه {item_ref} یافت نشد")
                continue
            
            # محاسبه مقادیر
            # StandardConsumptionQuantity = quantity_per_unit * تعداد (در اینجا تعداد = 1)
            standard_quantity = withdrawal_amount
            
            # ActualConsumptionQuantity = withdrawal_amount (مقدار برداشتی کل)
            actual_quantity = withdrawal_amount
            
            # RemainingConsumptionQuantity = standard_quantity - actual_quantity
            remaining_quantity = None
            



            # دریافت اطلاعات کامل آیتم از دیتابیس
            cursor.execute("""
                SELECT 
                    i.FormulaBomItemID
                FROM [Sepidar01].[WKO].[FormulaBomItem] i
                WHERE i.ProductFormulaRef = ? AND i.ItemRef = ?
            """, (formula_id,item_data[0],))
            
            formul_item_ref = cursor.fetchone()
            
            if not formul_item_ref:
                logger.warning(f"آیتم با شناسه {formul_item_ref} یافت نشد")
                continue
            



            # 1. دریافت آخرین ProductOrderBOMItemID
            cursor.execute("""
            UPDATE FMK.IDGeneration
            SET LastId = LastId + 1
            OUTPUT inserted.LastId
            WHERE TableName = ?
            """, ("WKO.ProductOrderBOMItem",))

            next_id = cursor.fetchone()[0]






            # ایجاد رکورد جدید
            new_record = {
                'ProductOrderBOMItemID': next_id,
                'ProductOrderRef': product_order_id,
                'ItemRef': item_data[0],
                # 'ItemCode': item_data[1],
                # 'ItemTitle': item_data[2] if item_data[2] else item_name,
                # 'ItemTitle_En': item_data[3],
                # 'ItemUnitRef': item_data[4],
                # 'ItemUnitTitle': item_data[5],
                # 'ItemUnitTitle_En': item_data[6],
                # 'ItemUnitsRatio': None,
                # 'IsUnitRatioConstant': 1,
                # 'ItemTracingCategoryRef': item_data[7],
                # 'ItemSecondaryUnitRef': item_data[8],
                # 'ItemSerialTracking': item_data[9] or 0,
                'FormulaBOMItemRef': formul_item_ref[0],  # اگر نیاز دارید می‌توانید تنظیم کنید
                # 'ActualConsumptionQuantity': actual_quantity,
                'StandardConsumptionQuantity': standard_quantity,
                'RemainingConsumptionQuantity': remaining_quantity,
                'Description': None,
                # 'FomulaBOMItemQuantity': quantity_per_unit,
                # 'RemainingBOMCost': None,
                # 'ItemTracingTitle': None,
                'TransferedQuantity': None,
                'ItemTracingRef': None,

                # 'RemainingRequestedQuantity': 0,
                # 'RegisteredRequestedQuantity': 0
            }
            
            # ساخت کوئری INSERT
            columns = ', '.join(new_record.keys())
            placeholders = ', '.join(['?' for _ in new_record.keys()])
            
            query = f"""
                INSERT INTO [Sepidar01].[WKO].[ProductOrderBOMItem] ({columns})
                VALUES ({placeholders})
            """
            
            # اجرای کوئری
            cursor.execute(query, list(new_record.values()))
            saved_count += 1
            saved_items.append({
                'item_ref': item_ref,
                'item_name': item_name,
                'product_order_bom_item_id': next_id + idx,
                'actual_consumption_quantity': actual_quantity,
                'standard_consumption_quantity': standard_quantity,
                'remaining_consumption_quantity': remaining_quantity
            })
        
        # commit همه تغییرات
        conn.commit()
        
        logger.info(f"{saved_count} ماده برای سفارش {product_order_id} ذخیره شد")
        
        return {
            'success': True,
            'product_order_id': product_order_id,
            'saved_count': saved_count,
            'saved_items': saved_items,
            'message': f'{saved_count} ماده با موفقیت ذخیره شد'
        }
        
    except Exception as e:
        logger.error(f"Error saving material details: {e}")
        if hasattr(conn, 'rollback'):
            conn.rollback()
        return {
            'success': False,
            'error': str(e),
            'product_order_id': product_order_id
        }