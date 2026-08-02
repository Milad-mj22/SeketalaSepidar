

from SepidarApp.databaseConnector import db
from stockManager.models import MaterialAdjustment
import logging
from decimal import Decimal


def prepare_materiasl2send_sms():

    material_objs = MaterialAdjustment.objects.filter(send_sms=True)
    if not material_objs:
        return {
            'status' : False,
            'Messafge': 'There is no Item to send SMS'
        }

    ret_dict = get_quantity_bulk(product_codes=[obj.item_code for obj in material_objs],stock_code=11)

    item_names2send_sms = ''

    for item in ret_dict.values():
        

        if item['minimum_amount'] <= item['specific_stock_quantity']:
            item_names2send_sms+=item['title'] 

    print(item_names2send_sms)

    return {
        'success':True
    }



logger = logging.getLogger(__name__)


def get_quantity_bulk(product_codes, stock_code=None):
    """
    دریافت موجودی برای چندین کد محصول به صورت همزمان
    
    پارامترها:
    - product_codes: لیست کدهای محصول
    - stock_code: (اختیاری) کد انبار خاص - اگر وارد شود، فقط موجودی آن انبار برگردانده می‌شود
    
    بازگشت:
    - دیکشنری با کلید کد محصول و مقدار اطلاعات موجودی
    """
    if not product_codes:
        return {}
    
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # ساخت پارامترهای کوئری
        placeholders = ','.join(['?' for _ in product_codes])
        
        # ============================================
        # کوئری اصلی با قابلیت فیلتر انبار
        # ============================================
        if stock_code:
            # اگر انبار خاص وارد شده، موجودی آن انبار را محاسبه کن
            query = f"""
                SELECT 
                    i.Code,
                    i.Title,
                    i.MinimumAmount,
                    i.DefaultStockRef,
                    i.UnitRef,
                    u.Title AS UnitTitle,
                    
                    -- موجودی در انبار مشخص شده
                    ISNULL((
                        SELECT SUM(Quantity)
                        FROM [Sepidar01].[INV].[ItemStockSummary] iss
                        WHERE iss.ItemRef = i.ItemID
                          AND iss.StockRef = ?
                    ), 0) AS SpecificStockQuantity,
                    
                    -- موجودی در تمام انبارها
                    ISNULL((
                        SELECT SUM(Quantity)
                        FROM [Sepidar01].[INV].[ItemStockSummary] iss
                        WHERE iss.ItemRef = i.ItemID
                    ), 0) AS TotalStockQuantity,

                    -- لیست موجودی در همه انبارها
                    STUFF((
                        SELECT ', ' + 
                            CAST(s.Code AS VARCHAR) + ':' + 
                            CAST(ISNULL(iss.Quantity, 0) AS VARCHAR)
                        FROM [Sepidar01].[INV].[Stock] s
                        INNER JOIN [Sepidar01].[INV].[ItemStockSummary] iss 
                            ON iss.StockRef = s.StockID 
                            AND iss.ItemRef = i.ItemID
                        WHERE s.IsActive = 1
                        ORDER BY s.Code
                        FOR XML PATH('')
                    ), 1, 2, '') AS StockDetails

                FROM [Sepidar01].[INV].[Item] i
                LEFT JOIN [Sepidar01].[INV].[Unit] u 
                    ON i.UnitRef = u.UnitID

                WHERE i.Code IN ({placeholders})
                  AND i.IsActive = 1
            """
            
            # پارامترها: stock_code اول، سپس product_codes
            params = [stock_code] + product_codes
            cursor.execute(query, params)
            
        else:
            # کوئری قبلی (بدون فیلتر انبار خاص)
            query = f"""
                SELECT 
                    i.Code,
                    i.Title,
                    i.MinimumAmount,
                    i.DefaultStockRef,
                    i.UnitRef,
                    u.Title AS UnitTitle,
                    
                    ISNULL((
                        SELECT SUM(Quantity)
                        FROM [Sepidar01].[INV].[ItemStockSummary] iss
                        WHERE iss.ItemRef = i.ItemID
                          AND iss.StockRef = i.DefaultStockRef
                    ), 0) AS DefaultStockQuantity,
                    
                    ISNULL((
                        SELECT SUM(Quantity)
                        FROM [Sepidar01].[INV].[ItemStockSummary] iss
                        WHERE iss.ItemRef = i.ItemID
                    ), 0) AS TotalStockQuantity,

                    STUFF((
                        SELECT ', ' + 
                            CAST(s.Code AS VARCHAR) + ':' + 
                            CAST(ISNULL(iss.Quantity, 0) AS VARCHAR)
                        FROM [Sepidar01].[INV].[Stock] s
                        INNER JOIN [Sepidar01].[INV].[ItemStockSummary] iss 
                            ON iss.StockRef = s.StockID 
                            AND iss.ItemRef = i.ItemID
                        WHERE s.IsActive = 1
                        ORDER BY s.Code
                        FOR XML PATH('')
                    ), 1, 2, '') AS StockDetails

                FROM [Sepidar01].[INV].[Item] i
                LEFT JOIN [Sepidar01].[INV].[Unit] u 
                    ON i.UnitRef = u.UnitID

                WHERE i.Code IN ({placeholders})
                  AND i.IsActive = 1
            """
            
            cursor.execute(query, product_codes)
        
        rows = cursor.fetchall()
        
        result = {}
        for row in rows:
            stock_details = []
            if row[8]:  # StockDetails
                for part in row[8].split(', '):
                    if ':' in part:
                        stock_code_val, qty = part.split(':')
                        stock_details.append({
                            'stock_code': stock_code_val,
                            'quantity': float(qty) if qty else 0
                        })
            
            # ساخت دیکشنری نتیجه
            result[row[0]] = {
                'code': row[0],
                'title': row[1] or '',
                'minimum_amount': float(row[2]) if row[2] else 0,
                'default_stock_ref': row[3],
                'unit_ref': row[4],
                'unit': row[5] or '',
                'total_stock_quantity': float(row[7]) if row[7] else 0,
                'stock_details': stock_details
            }
            
            # اگر انبار خاص وارد شده بود، موجودی آن را اضافه کن
            if stock_code:
                result[row[0]]['specific_stock_quantity'] = float(row[6]) if row[6] else 0
                result[row[0]]['specific_stock_ref'] = stock_code
            else:
                result[row[0]]['default_stock_quantity'] = float(row[6]) if row[6] else 0
        
        logger.info(f"✅ Retrieved quantity for {len(result)} products" + 
                   (f" (stock: {stock_code})" if stock_code else ""))
        return result
        
    except Exception as e:
        logger.error(f"❌ Error getting bulk quantities: {e}")
        return {}
    finally:
        db.close()


def get_quantity(product_code, stock_code=None):
    """
    دریافت موجودی یک محصول بر اساس کد محصول
    
    پارامترها:
    - product_code: کد محصول
    - stock_code: (اختیاری) کد انبار خاص
    
    بازگشت:
    - دیکشنری شامل اطلاعات موجودی، یا None در صورت خطا
    """
    result = get_quantity_bulk([product_code], stock_code)
    return result.get(product_code) if result else None


def get_total_stock(product_code, stock_code=None):
    """
    دریافت موجودی کل یا موجودی انبار خاص
    
    پارامترها:
    - product_code: کد محصول
    - stock_code: (اختیاری) کد انبار خاص
    
    بازگشت:
    - عدد float موجودی
    """
    result = get_quantity(product_code, stock_code)
    if result:
        if stock_code:
            return result.get('specific_stock_quantity', 0)
        return result.get('total_stock_quantity', 0)
    return 0.0


def send_sms():
    return