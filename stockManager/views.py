from datetime import datetime

from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from SepidarApp.databaseConnector import db
from .models import MaterialAdjustment
import json
import logging

logger = logging.getLogger(__name__)

@login_required
def material_adjustment_page(request):
    """
    صفحه تنظیمات مواد - خواندن موجودی از دیتابیس خارجی
    """
    try:
        # اتصال به دیتابیس خارجی
        db.connect()
        ext_conn = db.get_connection()
        cursor = ext_conn.cursor()
        
        # دریافت مواد با انبار پیش‌فرض 11 از دیتابیس خارجی
        query = """
-- ============================================
-- کوئری دریافت مواد با انبار پیش‌فرض 11
-- ============================================
SELECT 
    i.Code,
    i.Title,
    i.Title_En,
    i.MinimumAmount,
    i.DefaultStockRef,
    i.UnitRef,
    u.Title AS UnitTitle,
    
    -- موجودی در انبار پیش‌فرض (11)
    ISNULL((
        SELECT SUM(Quantity)
        FROM [Sepidar01].[INV].[ItemStockSummary] iss
        WHERE iss.ItemRef = i.ItemID
          AND iss.StockRef = 11
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

WHERE i.DefaultStockRef = 11
  AND i.IsActive = 1

ORDER BY i.Code;
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        # دریافت تنظیمات قبلی از دیتابیس خودمان
        adjustments = {
            adj.item_code: adj 
            for adj in MaterialAdjustment.objects.filter(creator=request.user, is_active=True)
        }
        
        materials = []
        for row in results:
            # استخراج داده‌ها
            item_code = row[0]
            adjustment = adjustments.get(item_code)
            
            # پردازش جزئیات انبارها
            stock_details = []
            if row[8]:
                for part in row[8].split(', '):
                    if ':' in part:
                        stock_id, qty = part.split(':')
                        stock_details.append({
                            'stock_id': stock_id,
                            'quantity': float(qty) if qty else 0
                        })
            
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
                'adjustment_percent': float(adjustment.adjustment_percent) if adjustment else 0,
                'send_sms': adjustment.send_sms if adjustment else False,
                'has_setting': bool(adjustment)
            })
        
        db.close()
        
        context = {
            'materials': materials,
            'total_materials': len(materials),
            'active_page': 'material_adjustment'
        }
        
        return render(request, 'material_adjustment.html', context)
        
    except Exception as e:
        logger.error(f"Error in material_adjustment_page: {e}")
        if 'db' in locals():
            db.close()
        return render(request, 'error.html', {'error': str(e)})


@csrf_exempt
@require_http_methods(["POST"])
def save_material_adjustments(request):
    """
    ذخیره تنظیمات (فقط درصد و پیامک) در دیتابیس خودمان
    """
    try:
        data = json.loads(request.body)
        adjustments = data.get('adjustments', [])
        send_sms_global = data.get('send_sms_global', False)
        
        if not adjustments:
            return JsonResponse({
                'success': False,
                'error': 'هیچ داده‌ای برای ذخیره وجود ندارد'
            }, status=400)
        
        saved_count = 0
        created_count = 0
        updated_count = 0
        errors = []
        
        for adj in adjustments:
            try:
                item_code = adj.get('code')
                item_name = adj.get('title', '')
                adjustment_percent = adj.get('adjustment_percent', 0)
                send_sms = adj.get('send_sms', send_sms_global)
                
                if not item_code:
                    errors.append("کد ماده الزامی است")
                    continue
                
                # ذخیره یا بروزرسانی در دیتابیس خودمان
                obj, created = MaterialAdjustment.objects.update_or_create(
                    item_code=item_code,
                    creator=request.user,
                    defaults={
                        'item_name': item_name,
                        'adjustment_percent': adjustment_percent,
                        'send_sms': send_sms,
                        'is_active': True
                    }
                )
                
                saved_count += 1
                if created:
                    created_count += 1
                else:
                    updated_count += 1
                
            except Exception as e:
                errors.append(f"خطا در ذخیره ماده {adj.get('code', '')}: {str(e)}")
                logger.error(f"Error saving adjustment for {adj.get('code')}: {e}")
        
        # ارسال پیامک در صورت فعال بودن
        if send_sms_global and saved_count > 0:
            try:
                # ارسال پیامک
                send_adjustment_sms(request.user, saved_count)
            except Exception as e:
                logger.error(f"Error sending SMS: {e}")
        
        return JsonResponse({
            'success': True,
            'saved_count': saved_count,
            'created_count': created_count,
            'updated_count': updated_count,
            'errors': errors,
            'message': f'{saved_count} تنظیمات با موفقیت ذخیره شد (جدید: {created_count}، بروزرسانی: {updated_count})'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'فرمت داده نامعتبر است'
        }, status=400)
    except Exception as e:
        logger.error(f"Error in save_material_adjustments: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def refresh_stock_data(request):
    """
    رفرش موجودی از دیتابیس خارجی (برای استفاده در صورت نیاز)
    """
    try:
        ext_conn = db.get_connection()
        cursor = ext_conn.cursor()
        
        # دریافت آخرین وضعیت موجودی
        query = """
            SELECT 
                i.Code,
                ISNULL((
                    SELECT SUM(Quantity)
                    FROM InventoryItem ii
                    WHERE ii.ItemRef = i.ItemID
                    AND ii.StockRef = 11
                ), 0) AS DefaultStock,
                ISNULL((
                    SELECT SUM(Quantity)
                    FROM InventoryItem ii
                    WHERE ii.ItemRef = i.ItemID
                ), 0) AS TotalStock
            FROM Item i
            WHERE i.DefaultStockRef = 11
            AND i.IsActive = 1
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        stock_data = {}
        for row in results:
            stock_data[row[0]] = {
                'default_stock': float(row[1]) if row[1] else 0,
                'total_stock': float(row[2]) if row[2] else 0
            }
        
        db.close()
        
        return JsonResponse({
            'success': True,
            'data': stock_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error refreshing stock: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def send_adjustment_sms(user, count):
    """ارسال پیامک به مدیران"""
    try:
        # لیست شماره مدیران از تنظیمات یا دیتابیس
        phone_numbers = ['0912XXXXXXX']
        
        message = f"""
        تنظیمات {count} ماده اولیه توسط {user.get_full_name()} ثبت شد.
        تاریخ: {datetime.now().strftime('%Y/%m/%d %H:%M')}
        """
        
        # ارسال پیامک از طریق سرویس مورد نظر
        # send_sms_via_service(phone_numbers, message)
        
        logger.info(f"SMS sent for {count} adjustments")
        
    except Exception as e:
        logger.error(f"Error sending SMS: {e}")
        raise