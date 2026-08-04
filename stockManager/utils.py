

import os
from random import random

from Constants import SEND_SMS
from SepidarApp.databaseConnector import db
from otp_manager.models import OTPVar_Enum, SMS_Recievers, SMS_Template, SMSServiceTemplate_Enum
from otp_manager.service import send_sms
from stockManager.models import MaterialAdjustment
import logging
from decimal import Decimal


def check_send_sms(product_code):

    obj = MaterialAdjustment.objects.filter(item_code=int(product_code))
    if not obj:
        return False
    obj = obj.last()
    return obj.send_sms



def prepare_materials2send_sms():
    """
    آماده‌سازی مواد برای ارسال پیامک:
    1. دریافت موادی که تنظیمات ارسال پیامک دارند
    2. محاسبه اختلاف موجودی با حداقل
    3. مرتب‌سازی بر اساس بیشترین اختلاف
    4. ایجاد رشته متنی از نام مواد
    5. برش به ۳۵ کاراکتر + سه نقطه
    6. ارسال پیامک
    """
    try:
        # ============================================
        # 1. دریافت مواد با تنظیمات ارسال پیامک
        # ============================================

        stock_data = get_quantity_bulk(stock_code=10)
        
        if not stock_data:
            logger.warning("⚠️ No stock data retrieved")
            return {
                'status': False,
                'message': 'No stock data available'
            }

        # ============================================
        # 3. محاسبه اختلاف و مرتب‌سازی
        # ============================================
        items_with_diff = []
        
        for  data in stock_data['materials']:

            ret = check_send_sms(product_code = data['code'])
            if not ret:
                continue


            minimum_amount = data['minimum_amount']
            specific_stock = data['default_stock_quantity']
            
            # محاسبه اختلاف (موجودی - حداقل)
            diff = specific_stock - minimum_amount
            
            items_with_diff.append({
                'code': data['code'],
                'title': data['title'],
                'minimum_amount': minimum_amount,
                'stock_quantity': specific_stock,
                'difference': diff,
                'status': 'موجود' if specific_stock >= minimum_amount else 'کمبود'
            })
        
        # مرتب‌سازی بر اساس بیشترین اختلاف (نزولی)
        items_with_diff.sort(key=lambda x: x['difference'], reverse=True)

        # ============================================
        # 4. ایجاد رشته متنی از نام مواد
        # ============================================
        item_names = []
        count = 0
        
        for item in items_with_diff:
            # فقط موادی که موجودی آنها از حداقل بیشتر است

            minimum_amount = item.get('minimum_amount', 0)
            specific_stock = item.get('stock_quantity', 0)

            
            if minimum_amount>specific_stock :
                # اضافه کردن نام با اختلاف
                item_names.append(f"{item['title']}")
                count += 1
        
        # اتصال اسامی با کاما
        full_text = '، '.join(item_names)

        print('Full text : ',full_text)
        
        # ============================================
        # 5. برش به ۳۵ کاراکتر + سه نقطه
        # ============================================
        if len(full_text) > 22:
            trimmed_text = full_text[:22] + '...'
        else:
            trimmed_text = full_text
        
        logger.info(f"📝 Prepared text: {trimmed_text} ({count} items)")

        # ============================================
        # 6. ارسال پیامک
        # ============================================
        sms_template = SMS_Template.objects.filter(
            name=SMSServiceTemplate_Enum.BUY_NOTIFICATION
        ).first()
        
        if not sms_template:
            logger.warning("⚠️ SMS template not found")
            return {
                'status': False,
                'message': 'SMS template not found'
            }
        
        # دریافت گیرندگان
        sms_receivers = SMS_Recievers.objects.filter(template=sms_template)
        
        if not sms_receivers.exists():
            logger.warning("⚠️ No SMS receivers found")
            return {
                'status': False,
                'message': 'No SMS receivers found'
            }
        
        # ارسال پیامک به همه گیرندگان
        sent_count = 0

        if  SEND_SMS:
            for sms_rec in sms_receivers:
                phone = sms_rec.persons.phone
                
                # ارسال پیامک
                result = send_sms(
                    sms_template,
                    phone_number=phone,
                    vars={
                        OTPVar_Enum.ITEMS_COUNT: count,
                        OTPVar_Enum.ITEMS_NAME: trimmed_text,

                    }
                )
                
                if result:
                    sent_count += 1
                    logger.info(f"📱 SMS sent to {phone}")
                else:
                    logger.error(f"❌ Failed to send SMS to {phone}: {result}")
        
        return {
            'success': True,
            'message': f'SMS sent to {sent_count} receivers',
            'data': {
                'items_count': count,
                'trimmed_text': trimmed_text,
                'full_text': full_text,
                'items': items_with_diff,
                'sent_count': sent_count,
                'total_receivers': sms_receivers.count()
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error in prepare_materials2send_sms: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            'status': False,
            'message': str(e)
        }


logger = logging.getLogger(__name__)


def get_quantity_bulk( stock_code=None):
    """
    دریافت موجودی برای چندین کد محصول به صورت همزمان
    
    پارامترها:
    - product_codes: لیست کدهای محصول
    - stock_code: (اختیاری) کد انبار خاص - اگر وارد شود، فقط موجودی آن انبار برگردانده می‌شود
    
    بازگشت:
    - دیکشنری با کلید کد محصول و مقدار اطلاعات موجودی
    """

    
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        

        
        # ============================================
        # کوئری اصلی با قابلیت فیلتر انبار
        # ============================================
        query = """
-- ============================================
-- کوئری دریافت مواد با انبار پیش‌فرض 10
-- ============================================
SELECT 
    i.Code,
    i.Title,
    i.Title_En,
    i.MinimumAmount,
    i.DefaultStockRef,
    i.UnitRef,
    u.Title AS UnitTitle,
    
    -- موجودی در انبار پیش‌فرض (10)
    ISNULL((
        SELECT SUM(Quantity)
        FROM [Sepidar01].[INV].[ItemStockSummary] iss
        WHERE iss.ItemRef = i.ItemID
          AND iss.StockRef = 10
          AND iss.FiscalYearRef = (
              SELECT MAX(FiscalYearRef) 
              FROM [Sepidar01].[INV].[ItemStockSummary] 
              WHERE ItemRef = i.ItemID
          )
    ), 0) AS DefaultStockQuantity,
    
    -- موجودی در تمام انبارها (آخرین سال مالی)
    ISNULL((
        SELECT SUM(Quantity)
        FROM [Sepidar01].[INV].[ItemStockSummary] iss
        WHERE iss.ItemRef = i.ItemID
          AND iss.FiscalYearRef = (
              SELECT MAX(FiscalYearRef) 
              FROM [Sepidar01].[INV].[ItemStockSummary] 
              WHERE ItemRef = i.ItemID
          )
    ), 0) AS TotalStockQuantity,
    
    -- لیست موجودی در همه انبارها با جزئیات
    STUFF((
        SELECT ', ' + 
            CAST(s.Code AS VARCHAR) + ':' + 
            CAST(ISNULL(iss.Quantity, 0) AS VARCHAR)
        FROM [Sepidar01].[INV].[Stock] s
        INNER JOIN [Sepidar01].[INV].[ItemStockSummary] iss 
            ON iss.StockRef = s.StockID 
            AND iss.ItemRef = i.ItemID
            AND iss.FiscalYearRef = (
                SELECT MAX(FiscalYearRef) 
                FROM [Sepidar01].[INV].[ItemStockSummary] 
                WHERE ItemRef = i.ItemID
            )
        WHERE s.IsActive = 1
        ORDER BY s.Code
        FOR XML PATH('')
    ), 1, 2, '') AS StockDetails

FROM [Sepidar01].[INV].[Item] i
LEFT JOIN [Sepidar01].[INV].[Unit] u 
    ON i.UnitRef = u.UnitID

WHERE i.DefaultStockRef = 10
  AND i.IsActive = 1

ORDER BY i.Code;
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        # دریافت تنظیمات قبلی از دیتابیس خودمان

        materials = []
        for row in results:
            # استخراج داده‌ها
            item_code = row[0]

            
            # پردازش جزئیات انبارها
            stock_details = []
            # if row[8]:
            #     for part in row[8].split(', '):
            #         if ':' in part:
            #             stock_id, qty = part.split(':')
            #             stock_details.append({
            #                 'stock_id': stock_id,
            #                 'quantity': float(qty) if qty else 0
            #             })
            
            materials.append({
                'code': item_code,
                'title': row[1] or '',
                'title_en': row[2] or '',
                'minimum_amount': float(row[3]) if row[3] else 0,
                'default_stock_ref': row[4],
                'unit_ref': row[5],
                'unit_title': row[6] or '',
                'default_stock_quantity': float(row[7]) if row[7] else 0,
                'total_stock_quantity': float(row[8]) if row[8] else 0,
                'stock_details': stock_details,

            })
        
        db.close()
        
        context = {
            'materials': materials,
            'total_materials': len(materials),
            'active_page': 'material_adjustment'
        }

        return context
        
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

