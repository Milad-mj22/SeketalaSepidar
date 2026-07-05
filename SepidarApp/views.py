import json

from django.shortcuts import render

# Create your views here.
from django.contrib.auth.decorators import login_required

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
        
        return render(request, 'formula_list.html', {
            'formulas': formula_list,
            'total_formulas': total_formulas,
            'active_formulas': active_formulas,
            'total_items': total_items,
            'inactive_formulas': total_formulas - active_formulas
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
    """
    try:
        # دریافت داده از درخواست
        data = json.loads(request.body)
        values = data.get('values', [])
        
        if not values:
            return JsonResponse({
                'success': False,
                'error': 'هیچ مقداری برای ثبت وجود ندارد'
            }, status=400)
        
        # اعتبارسنجی مقادیر
        for item in values:
            formula_id = item.get('formula_id')
            value = item.get('value')
            
            if not formula_id:
                return JsonResponse({
                    'success': False,
                    'error': 'شناسه فرمول الزامی است'
                }, status=400)
            
            if value is None or not isinstance(value, (int, float)):
                return JsonResponse({
                    'success': False,
                    'error': f'مقدار فرمول {formula_id} نامعتبر است'
                }, status=400)
            
            if value < 0:
                return JsonResponse({
                    'success': False,
                    'error': f'مقدار فرمول {formula_id} نمی‌تواند منفی باشد'
                }, status=400)
        
        # اتصال به دیتابیس
        db.connect()
        
        # دیکشنری برای جمع‌آوری مواد اولیه مورد نیاز
        required_materials = defaultdict(float)
        formula_details = []
        
        # برای هر فرمول، مواد اولیه را محاسبه کن
        for item in values:
            formula_id = item.get('formula_id')
            requested_quantity = item.get('value')
            
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
                
                # محاسبه مقدار مورد نیاز = مقدار درخواستی * مقدار در هر واحد
                required_quantity = requested_quantity * quantity_per_unit
                
                formula_materials.append({
                    'item_ref': item_ref,
                    'item_name': item_name,
                    'unit_ref': unit_ref,
                    'unit_name': unit_name,
                    'quantity_per_unit': quantity_per_unit,
                    'required_quantity': required_quantity
                })
                
                # جمع‌آوری در دیکشنری اصلی
                key = f"{item_ref}_{unit_ref}"
                required_materials[key] += required_quantity
            
            formula_details.append({
                'formula_id': formula_id,
                'requested_quantity': requested_quantity,
                'materials': formula_materials
            })
        
        # بررسی موجودی مواد اولیه
        stock_status = check_materials_stock(db, required_materials)
        
        # بستن اتصال دیتابیس
        db.close()
        
        # ذخیره مقادیر در دیتابیس (اگر نیاز دارید)
        saved_count = save_formula_values(values)
        
        # برگرداندن نتیجه
        return JsonResponse({
            'success': True,
            'saved_count': saved_count,
            'message': f'{saved_count} مقدار با موفقیت ثبت شد',
            'data': {
                'formula_details': formula_details,
                'required_materials': dict(required_materials),
                'stock_status': stock_status,
                'summary': {
                    'total_materials': len(required_materials),
                    'available_materials': sum(1 for s in stock_status.values() if s['available']),
                    'unavailable_materials': sum(1 for s in stock_status.values() if not s['available'])
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
                fbi.ItemRef,
                fbi.Quantity,
                fbi.UnitRef,
                fbi.SecondaryQuantity,
                fbi.Description,
                itm.Title as ItemName,
                itm.Code as ItemCode,
                unt.Title as UnitName,
                unt.Code as UnitCode
            FROM [Sepidar01].[WKO].[FormulaBomItem] fbi
            LEFT JOIN [Sepidar01].[INV].[Item] itm
                ON fbi.ItemRef = itm.ItemID
            LEFT JOIN [Sepidar01].[INV].[Unit] unt
                ON fbi.UnitRef = unt.UnitID
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
                'UnitCode': row.UnitCode
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
                FROM [Sepidar01].[INV].[InventoryItem]
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
                'required_quantity': required_qty,
                'available_stock': available_stock,
                'available': available_stock >= required_qty,
                'shortage': max(0, required_qty - available_stock),
                'status': 'موجود' if available_stock >= required_qty else 'کمبود'
            }
        
        return stock_status
        
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