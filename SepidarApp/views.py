import json

from django.shortcuts import render

# Create your views here.
from django.contrib.auth.decorators import login_required

from SepidarApp.Steps.save_order import save_multiple_product_orders
from SepidarApp.models import WarehouseRelation

@login_required(login_url='authentication:sign-in')
def first_page(request):
    context = {
        "active_page":"home"
    }
    return render(request, 
                  'main_page.html',
                  context
                  )






from django.shortcuts import render
from django.http import JsonResponse
from django.db import connection
import pyodbc
import logging

from .databaseConnector import db

logger = logging.getLogger(__name__)
def formula_list(request):
    """
    Display all formulas with their boom items in a table
    """
    try:
        # Connect to database
        db.connect()
        
        # Get all formulas with items
        results = db.get_formulas_with_items()
        
        # Process results into a structured format
        formulas = {}
        for row in results:
            formula_id = row.ProductFormulaID
            if formula_id not in formulas:
                formulas[formula_id] = {
                    'id': formula_id,
                    'code': row.Code,
                    'title': row.Title,
                    'item_ref': row.ItemRef,
                    'product_name': row.ProductName if hasattr(row, 'ProductName') else None,
                    'product_code': row.ProductCode if hasattr(row, 'ProductCode') else None,
                    'item_unit_ref': row.ItemUnitRef,
                    'quantity': float(row.FormulaQuantity) if row.FormulaQuantity else 0,
                    'is_active': row.IsActive,
                    'estimated_labour': float(row.EstimatedLabour) if row.EstimatedLabour else 0,
                    'estimated_overhead': float(row.EstimatedOverhead) if row.EstimatedOverhead else 0,
                    'description': row.FormulaDescription,
                    'tracing_title': row.TracingTitle,
                    'main_item_stock': float(row.MainItemStockQuantity) if hasattr(row, 'MainItemStockQuantity') and row.MainItemStockQuantity else 0,
                    'main_item_stock_unit': row.MainItemStockUnitName if hasattr(row, 'MainItemStockUnitName') else None,
                    'items': []
                }
            
            # Add item if exists
            if row.FormulaBomItemID:
                formulas[formula_id]['items'].append({
                    'id': row.FormulaBomItemID,
                    'item_ref': row.BomItemRef,
                    'item_name': row.BomItemName if hasattr(row, 'BomItemName') else None,
                    'item_code': row.BomItemCode if hasattr(row, 'BomItemCode') else None,
                    'quantity': float(row.BomQuantity) if row.BomQuantity else 0,
                    'secondary_quantity': float(row.SecondaryQuantity) if row.SecondaryQuantity else 0,
                    'description': row.ItemDescription,
                    'tracing_ref': row.ItemTracingRef,
                    'stock_quantity': float(row.StockQuantity) if hasattr(row, 'StockQuantity') and row.StockQuantity else 0,
                    'stock_unit': row.StockUnitName if hasattr(row, 'StockUnitName') else None,
                })
        
        # Convert to list for template
        formula_list = list(formulas.values())
        
        # Get summary statistics
        total_formulas = len(formula_list)
        active_formulas = sum(1 for f in formula_list if f['is_active'])
        total_items = sum(len(f['items']) for f in formula_list)
        
        relations = WarehouseRelation.objects.select_related('source_warehouse', 'destination_warehouse').all()


        return render(request, 'formula_list.html', {
            'formulas': formula_list,
            'total_formulas': total_formulas,
            'active_formulas': active_formulas,
            'total_items': total_items,
            'inactive_formulas': total_formulas - active_formulas,
            'relations': relations,  # اضافه کردن روابط به context
        })
        
    except pyodbc.Error as e:
        error_message = f"Database error: {str(e)}"
        logger.error(error_message)
        return render(request, 'error.html', {'error': error_message})
    except Exception as e:
        error_message = f"Error: {str(e)}"
        logger.error(error_message)
        return render(request, 'error.html', {'error': error_message})
    finally:
        db.close()
def formula_detail(request, formula_id):
    """
    Display a single formula with its items
    """
    try:
        db.connect()
        results = db.get_formulas_with_items(formula_id)
        
        if not results:
            return render(request, 'error.html', {'error': 'Formula not found'})
        
        formula = {
            'id': results[0].ProductFormulaID,
            'code': results[0].Code,
            'title': results[0].Title,
            'item_ref': results[0].ItemRef,
            'item_unit_ref': results[0].ItemUnitRef,
            'quantity': float(results[0].FormulaQuantity) if results[0].FormulaQuantity else 0,
            'is_active': results[0].IsActive,
            'estimated_labour': float(results[0].EstimatedLabour) if results[0].EstimatedLabour else 0,
            'estimated_overhead': float(results[0].EstimatedOverhead) if results[0].EstimatedOverhead else 0,
            'description': results[0].FormulaDescription,
            'tracing_title': results[0].TracingTitle,
            'items': []
        }
        
        for row in results:
            if row.FormulaBomItemID:
                formula['items'].append({
                    'id': row.FormulaBomItemID,
                    'item_ref': row.BomItemRef,
                    'quantity': float(row.BomQuantity) if row.BomQuantity else 0,
                    'secondary_quantity': float(row.SecondaryQuantity) if row.SecondaryQuantity else 0,
                    'description': row.ItemDescription,
                    'tracing_ref': row.ItemTracingRef,
                    'stock_quantity': float(row.StockQuantity) if hasattr(row, 'StockQuantity') and row.StockQuantity else 0,
                    'stock_unit': row.StockUnitName if hasattr(row, 'StockUnitName') else None,
                })
        
        return render(request, 'formula_detail.html', {'formula': formula})
        
    except pyodbc.Error as e:
        return render(request, 'error.html', {'error': f"Database error: {str(e)}"})
    except Exception as e:
        return render(request, 'error.html', {'error': f"Error: {str(e)}"})
    finally:
        db.close()

def api_formulas(request,formula_id):
    """
    API endpoint to return formulas as JSON
    """
    try:
        db.connect()
        results = db.get_formulas_with_items()
        
        formulas = {}
        for row in results:
            formula_id = row.ProductFormulaID
            if formula_id not in formulas:
                formulas[formula_id] = {
                    'id': formula_id,
                    'code': row.Code,
                    'title': row.Title,
                    'item_ref': row.ItemRef,
                    'item_unit_ref': row.ItemUnitRef,
                    'quantity': float(row.FormulaQuantity) if row.FormulaQuantity else 0,
                    'is_active': row.IsActive,
                    'estimated_labour': float(row.EstimatedLabour) if row.EstimatedLabour else 0,
                    'estimated_overhead': float(row.EstimatedOverhead) if row.EstimatedOverhead else 0,
                    'description': row.FormulaDescription,
                    'tracing_title': row.TracingTitle,
                    'items': []
                }
            
            if row.FormulaBomItemID:
                formulas[formula_id]['items'].append({
                    'id': row.FormulaBomItemID,
                    'item_ref': row.BomItemRef,
                    'quantity': float(row.BomQuantity) if row.BomQuantity else 0,
                    'secondary_quantity': float(row.SecondaryQuantity) if row.SecondaryQuantity else 0,
                    'description': row.ItemDescription,
                    'tracing_ref': row.ItemTracingRef
                })
        
        return JsonResponse({
            'success': True,
            'data': list(formulas.values())
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
    finally:
        db.close()

def search_formulas(request):
    """
    Search formulas by code or title
    """
    search_term = request.GET.get('q', '')
    if not search_term:
        return JsonResponse({'success': False, 'error': 'Search term required'})
    
    try:
        db.connect()
        query = """
            SELECT 
                pf.ProductFormulaID,
                pf.Code,
                pf.Title,
                pf.IsActive,
                COUNT(fbi.FormulaBomItemID) as ItemCount
            FROM [Sepidar01].[WKO].[ProductFormula] pf
            LEFT JOIN [Sepidar01].[WKO].[FormulaBomItem] fbi 
                ON pf.ProductFormulaID = fbi.ProductFormulaRef
            WHERE pf.Code LIKE ? OR pf.Title LIKE ?
            GROUP BY pf.ProductFormulaID, pf.Code, pf.Title, pf.IsActive
            ORDER BY pf.Code
        """
        search_pattern = f"%{search_term}%"
        results = db.execute_query(query, [search_pattern, search_pattern])
        
        formulas = []
        for row in results:
            formulas.append({
                'id': row.ProductFormulaID,
                'code': row.Code,
                'title': row.Title,
                'is_active': row.IsActive,
                'item_count': row.ItemCount
            })
        
        return JsonResponse({
            'success': True,
            'data': formulas
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
    finally:
        db.close()

from django.views.decorators.http import require_http_methods

import json
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from collections import defaultdict

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def submit_all_formula_values(request):
    """
    دریافت تمام مقادیر فرمول‌ها و محاسبه مواد اولیه مورد نیاز
    شامل: product_id, product_unit, consumption_value و withdrawal_items
    """
    try:
        # دریافت داده از درخواست
        data = json.loads(request.body)
        formulas = data.get('formulas', [])
        relation_id = data.get('relation_id', [])
        
        
        if not formulas:
            return JsonResponse({
                'success': False,
                'error': 'هیچ مقداری برای ثبت وجود ندارد'
            }, status=400)
        

        
        if not relation_id:
            return JsonResponse({
                'success': False,
                'error': 'هیچ مقداری برای رابطه مورد نظر وجود ندارد'
            }, status=400)
        
        relation = WarehouseRelation.objects.filter(id=relation_id)

        
        if not relation:
            return JsonResponse({
                'success': False,
                'error': 'رابطه مورد نظر یافت نشد'
            }, status=400)
        
        relation = relation.first()
        stock_source_ref = relation.source_warehouse.number
        stock_dest_ref = relation.destination_warehouse.number

        # اعتبارسنجی مقادیر
        for item in formulas:
            formula_id = item.get('formula_id')
            consumption_value = item.get('consumption_value') or item.get('value')  # پشتیبانی از هر دو نام
            
            if not formula_id:
                return JsonResponse({
                    'success': False,
                    'error': 'شناسه فرمول الزامی است'
                }, status=400)
            
            if consumption_value is None or not isinstance(consumption_value, (int, float)):
                return JsonResponse({
                    'success': False,
                    'error': f'مقدار مصرفی فرمول {formula_id} نامعتبر است'
                }, status=400)
            
            if consumption_value < 0:
                return JsonResponse({
                    'success': False,
                    'error': f'مقدار مصرفی فرمول {formula_id} نمی‌تواند منفی باشد'
                }, status=400)
            
            # اعتبارسنجی آیتم‌های برداشتی
            withdrawal_items = item.get('withdrawal_items', [])
            for w_item in withdrawal_items:
                withdrawal_amount = w_item.get('withdrawal_amount', 0)
                if withdrawal_amount < 0:
                    return JsonResponse({
                        'success': False,
                        'error': f'میزان برداشتی برای فرمول {formula_id} نمی‌تواند منفی باشد'
                    }, status=400)
        
        # اتصال به دیتابیس
        db.connect()
        
        # دیکشنری برای جمع‌آوری مواد اولیه مورد نیاز
        required_materials = defaultdict(lambda: {
            'total_required': 0,
            'item_name': '',
            'unit_name': '',
            'item_ref': '',
            'bom_item_id': None
        })
        
        formula_details = []
        all_withdrawal_details = []
        
        # برای هر فرمول، مواد اولیه را محاسبه کن
        for item in formulas:
            formula_id = item.get('formula_id')
            consumption_value = item.get('consumption_value') or item.get('value', 0)
            product_id = item.get('product_id')
            product_unit = item.get('product_unit', '')
            withdrawal_items = item.get('withdrawal_items', [])
            total_withdrawal = item.get('total_withdrawal', 0)
            
            # دریافت مواد اولیه فرمول از دیتابیس
            recipe_items = get_formula_recipe(db, formula_id)
            
            if not recipe_items:
                logger.warning(f"No recipe found for formula {formula_id}")
                continue
            
            # محاسبه مقدار مورد نیاز برای هر ماده
            formula_materials = []
            for recipe in recipe_items:
                item_ref = recipe.get('ItemRef')
                item_name = recipe.get('ItemName')
                unit_ref = recipe.get('UnitRef')
                unit_name = recipe.get('UnitName')
                quantity_per_unit = recipe.get('Quantity', 0)
                
                # محاسبه مقدار مورد نیاز = مقدار مصرفی * مقدار در هر واحد
                required_quantity = consumption_value * quantity_per_unit
                
                formula_materials.append({
                    'item_ref': item_ref,
                    'item_name': item_name,
                    'unit_ref': unit_ref,
                    'unit_name': unit_name,
                    'quantity_per_unit': quantity_per_unit,
                    'required_quantity': required_quantity,
                    'withdrawal_amount': next(
                        (w.get('withdrawal_amount', 0) for w in withdrawal_items if w.get('item_ref') == item_ref),
                        0
                    )
                })
                
                # جمع‌آوری در دیکشنری اصلی
                key = f"{item_ref}_{unit_ref}"
                required_materials[key]['total_required'] += required_quantity
                required_materials[key]['item_name'] = item_name
                required_materials[key]['unit_name'] = unit_name
                required_materials[key]['item_ref'] = item_ref
                required_materials[key]['bom_item_id'] = recipe.get('BOMItemID')
            
            # ذخیره جزئیات فرمول
            formula_details.append({
                'formula_id': formula_id,
                'product_id': product_id,
                'product_unit': product_unit,
                'consumption_value': consumption_value,
                'total_withdrawal': total_withdrawal,
                'withdrawal_items': withdrawal_items,
                'materials': formula_materials
            })
            
            # جمع‌آوری جزئیات برداشت
            if withdrawal_items:
                for w_item in withdrawal_items:
                    all_withdrawal_details.append({
                        'formula_id': formula_id,
                        'product_id': product_id,
                        'product_unit': product_unit,
                        'item_ref': w_item.get('item_ref'),
                        'item_name': w_item.get('item_name'),
                        'quantity': w_item.get('quantity', 0),
                        'withdrawal_amount': w_item.get('withdrawal_amount', 0),
                        'is_manually_edited': w_item.get('is_manually_edited', False)
                    })
        
        # بررسی موجودی مواد اولیه
        all_exist, stock_status = check_materials_stock(db, required_materials)
        



        # ذخیره مقادیر در دیتابیس
        saved_formulas = []
        all_exist = True
        if all_exist:
            pass

            # for item in formulas:
            save_results  = save_multiple_product_orders(db,formulas,stock_source_ref,stock_dest_ref)

            saved_results = save_results.get('results', [])
            saved_count = save_results.get('saved', 0)
            


            # saved_count = save_formula_values_with_details(
            #     db, 
            #     formulas, 
            #     required_materials, 
            #     all_withdrawal_details
            # )
            
            # # ثبت عملیات برداشت
            # withdrawal_records = save_withdrawal_records(db, all_withdrawal_details)
            withdrawal_records = True
        else:
            saved_count = 0
            saved_results = []
            withdrawal_records = []
        
        # بستن اتصال دیتابیس
        db.close()
        
        if all_exist:
            return JsonResponse({
                'success': True,
                'saved_count': saved_count,
                'message': f'{saved_count} فرمول با موفقیت ثبت شد',
                'results': saved_results,  # ADD THIS LINE - pass the results
                'data': {
                    'formula_details': formula_details,
                    'required_materials': dict(required_materials),
                    'stock_status': stock_status,
                    'withdrawal_records': withdrawal_records,
                    'summary': {
                        'total_formulas': len(formulas),
                        'saved_formulas': saved_count,
                        'total_materials': len(required_materials),
                        'available_materials': sum(1 for s in stock_status.values() if s['available']),
                        'unavailable_materials': sum(1 for s in stock_status.values() if not s['available']),
                        'total_withdrawal_items': len(all_withdrawal_details)
                    }
                }
            })
        else:
            # استخراج مواد ناموجود با جزئیات کامل
            unavailable_materials = []
            for key, status in stock_status.items():
                if not status.get('available', False):
                    unavailable_materials.append({
                        'material_name': status.get('material_name', key),
                        'material_code': status.get('material_code', ''),
                        'required_quantity': status.get('required_quantity', 0),
                        'available_quantity': status.get('available_quantity', 0),
                        'shortage': status.get('required_quantity', 0) - status.get('available_quantity', 0),
                        'unit': status.get('unit', ''),
                        'bom_item_id': status.get('bom_item_id'),
                        'item_ref': status.get('item_ref')
                    })
            
            # ساخت پیام خطای دقیق
            error_message = 'کمبود کالا در انبار:\n'
            for item in unavailable_materials[:5]:  # فقط ۵ مورد اول
                error_message += f"• {item['material_name']}: نیاز {item['required_quantity']:.2f} {item['unit']} - موجودی {item['available_quantity']:.2f} {item['unit']} (کمبود: {item['shortage']:.2f} {item['unit']})\n"
            
            if len(unavailable_materials) > 5:
                error_message += f"\nو {len(unavailable_materials) - 5} مورد دیگر..."
            
            return JsonResponse({
                'success': False,
                'message': 'کمبود کالا در انبار',
                'error': error_message,
                'data': {
                    'formula_details': formula_details,
                    'required_materials': dict(required_materials),
                    'stock_status': stock_status,
                    'unavailable_materials': unavailable_materials,
                    'withdrawal_records': withdrawal_records,
                    'summary': {
                        'total_formulas': len(formulas),
                        'total_materials': len(required_materials),
                        'available_materials': sum(1 for s in stock_status.values() if s['available']),
                        'unavailable_materials': sum(1 for s in stock_status.values() if not s['available']),
                        'total_shortage': sum(
                            status.get('required_quantity', 0) - status.get('available_quantity', 0)
                            for status in stock_status.values()
                            if not status.get('available', False)
                        )
                    }
                }
            })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'فرمت داده نامعتبر است'
        }, status=400)
    except Exception as e:
        logger.error(f"Error in submit_all_formula_values: {e}")
        if 'db' in locals():
            db.close()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    


def get_formula_recipe(db, formula_id):
    """
    دریافت مواد اولیه یک فرمول از دیتابیس
    """
    try:
        query = """
            SELECT 
                fbi.FormulaBomItemID,
                fbi.ItemRef,
                fbi.Quantity,
                fbi.SecondaryQuantity,
                fbi.Description,
                fbi.ItemTracingRef,
                itm.Title as ItemName,
                itm.Code as ItemCode,
                itm.UnitRef as ItemUnitRef  -- استفاده از UnitRef از جدول Item
            FROM [Sepidar01].[WKO].[FormulaBomItem] fbi
            LEFT JOIN [Sepidar01].[INV].[Item] itm
                ON fbi.ItemRef = itm.ItemID
            WHERE fbi.ProductFormulaRef = ?
            ORDER BY fbi.FormulaBomItemID
        """
        results = db.execute_query(query, [formula_id])
        
        recipe = []
        for row in results:
            recipe.append({
                'FormulaBomItemID': row.FormulaBomItemID,
                'ItemRef': row.ItemRef,
                'Quantity': float(row.Quantity) if row.Quantity else 0,
                'SecondaryQuantity': float(row.SecondaryQuantity) if row.SecondaryQuantity else 0,
                'Description': row.Description,
                'ItemTracingRef': row.ItemTracingRef,
                'ItemName': row.ItemName,
                'ItemCode': row.ItemCode,
                'UnitRef': row.ItemUnitRef  # استفاده از UnitRef از جدول Item
            })
        
        return recipe
        
    except Exception as e:
        logger.error(f"Error getting recipe for formula {formula_id}: {e}")
        return []

def check_materials_stock(db, required_materials):
    """
    بررسی موجودی مواد اولیه در انبار
    """
    stock_status = {}

    all_exist = True
    
    try:
        for key, required_qty in required_materials.items():
            # جداسازی ItemRef و UnitRef
            parts = key.split('_')
            if len(parts) == 2:
                item_ref = parts[0]
                unit_ref = parts[1]
            else:
                continue
            
            # دریافت موجودی از دیتابیس
            query = """
                SELECT 
                    ItemRef,
                    UnitRef,
                    SUM(Quantity) as TotalStock
                FROM [Sepidar01].[INV].[ItemStockSummary]
                WHERE ItemRef = ? AND UnitRef = ?
                GROUP BY ItemRef, UnitRef
            """
            results = db.execute_query(query, [item_ref, unit_ref])
            
            available_stock = 0
            if results and len(results) > 0:
                available_stock = float(results[0].TotalStock) if results[0].TotalStock else 0
            
            stock_status[key] = {
                'item_ref': item_ref,
                'unit_ref': unit_ref,
                'required_quantity': required_qty['total_required'],
                'available_stock': available_stock,
                'available': available_stock >= required_qty['total_required'],
                'shortage': max(0, required_qty['total_required'] - available_stock),
                'status': 'موجود' if available_stock >= required_qty['total_required'] else 'کمبود'
            }
        
            if available_stock < required_qty['total_required'] :
                all_exist = False


        return all_exist , stock_status
        
    except Exception as e:
        logger.error(f"Error checking stock: {e}")
        return {}


def get_formula_recipe_with_stock(db, formula_id):
    """
    دریافت مواد اولیه فرمول با اطلاعات موجودی
    """
    try:
        query = """
            SELECT 
                fbi.ItemRef,
                fbi.Quantity,
                fbi.UnitRef,
                fbi.SecondaryQuantity,
                fbi.Description,
                itm.Title as ItemName,
                itm.Code as ItemCode,
                unt.Title as UnitName,
                unt.Code as UnitCode,
                ISNULL(stock.TotalStock, 0) as AvailableStock
            FROM [Sepidar01].[WKO].[FormulaBomItem] fbi
            LEFT JOIN [Sepidar01].[INV].[Item] itm
                ON fbi.ItemRef = itm.ItemID
            LEFT JOIN [Sepidar01].[INV].[Unit] unt
                ON fbi.UnitRef = unt.UnitID
            LEFT JOIN (
                SELECT 
                    ItemRef,
                    UnitRef,
                    SUM(Quantity) as TotalStock
                FROM [Sepidar01].[INV].[InventoryItem]
                GROUP BY ItemRef, UnitRef
            ) stock ON fbi.ItemRef = stock.ItemRef 
            WHERE fbi.ProductFormulaRef = ?
            ORDER BY fbi.FormulaBomItemID
        """
        results = db.execute_query(query, [formula_id])
        
        recipe = []
        for row in results:
            recipe.append({
                'ItemRef': row.ItemRef,
                'Quantity': float(row.Quantity) if row.Quantity else 0,
                'UnitRef': row.UnitRef,
                'SecondaryQuantity': float(row.SecondaryQuantity) if row.SecondaryQuantity else 0,
                'Description': row.Description,
                'ItemName': row.ItemName,
                'ItemCode': row.ItemCode,
                'UnitName': row.UnitName,
                'UnitCode': row.UnitCode,
                'AvailableStock': float(row.AvailableStock) if row.AvailableStock else 0
            })
        
        return recipe
        
    except Exception as e:
        logger.error(f"Error getting recipe with stock for formula {formula_id}: {e}")
        return []


def save_formula_values(values):
    """
    ذخیره مقادیر فرمول در دیتابیس
    """
    saved_count = 0
    errors = []
    return 0
    
    try:
        db.connect()
        cursor = db.get_cursor()
        
        for item in values:
            formula_id = item.get('formula_id')
            value = item.get('value')
            
            try:
                # ذخیره در جدول FormulaValues
                query = """
                    INSERT INTO [Sepidar01].[WKO].[FormulaValues] 
                    (ProductFormulaRef, Value, CreationDate)
                    VALUES (?, ?, GETDATE())
                """
                cursor.execute(query, [formula_id, value])
                saved_count += 1
                
            except Exception as e:
                errors.append(f"فرمول {formula_id}: {str(e)}")
                continue
        
        cursor.commit()
        cursor.close()
        db.close()
        
        if errors:
            logger.warning(f"Saved {saved_count} values with {len(errors)} errors")
        
        return saved_count
        
    except Exception as e:
        logger.error(f"Error saving formula values: {e}")
        db.close()
        return 0


def get_formula_recipe_summary(db, formula_id):
    """
    دریافت خلاصه مواد اولیه یک فرمول
    """
    try:
        query = """
            SELECT 
                COUNT(*) as TotalItems,
                SUM(fbi.Quantity) as TotalQuantity,
                COUNT(DISTINCT fbi.ItemRef) as UniqueItems
            FROM [Sepidar01].[WKO].[FormulaBomItem] fbi
            WHERE fbi.ProductFormulaRef = ?
        """
        results = db.execute_query(query, [formula_id])
        
        if results and len(results) > 0:
            return {
                'total_items': results[0].TotalItems if results[0].TotalItems else 0,
                'total_quantity': float(results[0].TotalQuantity) if results[0].TotalQuantity else 0,
                'unique_items': results[0].UniqueItems if results[0].UniqueItems else 0
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting recipe summary for formula {formula_id}: {e}")
        return None