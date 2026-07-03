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
                    'tracing_ref': row.ItemTracingRef
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
                    'tracing_ref': row.ItemTracingRef
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

@require_http_methods(["POST"])
def submit_all_formula_values(request):
    """
    دریافت تمام مقادیر فرمول‌ها به صورت یکجا
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
        
        # ذخیره در دیتابیس
        saved_count = 0
        errors = []
        
        try:
            db.connect()
            cursor = db.get_cursor()
            
            for item in values:
                formula_id = item.get('formula_id')
                value = item.get('value')
                
                try:
                    # ذخیره مقدار در دیتابیس
                    # اینجا می‌توانید هر عملیات ذخیره‌سازی که نیاز دارید انجام دهید
                    # query = """
                    #     INSERT INTO [Sepidar01].[WKO].[FormulaValues] 
                    #     (ProductFormulaRef, Value, CreationDate)
                    #     VALUES (?, ?, GETDATE())
                    # """
                    # cursor.execute(query, [formula_id, value])
                    saved_count += 1
                    
                except pyodbc.Error as e:
                    errors.append(f"فرمول {formula_id}: {str(e)}")
                    continue
            
            cursor.commit()
            cursor.close()
            db.close()
            
            if errors:
                return JsonResponse({
                    'success': True,
                    'saved_count': saved_count,
                    'errors': errors,
                    'message': f'{saved_count} مقدار ثبت شد و {len(errors)} خطا رخ داد'
                })
            
            logger.info(f"{saved_count} values saved successfully")
            
            return JsonResponse({
                'success': True,
                'saved_count': saved_count,
                'message': f'{saved_count} مقدار با موفقیت ثبت شد'
            })
            
        except pyodbc.Error as e:
            logger.error(f"Database error: {e}")
            db.close()
            return JsonResponse({
                'success': False,
                'error': f'خطای دیتابیس: {str(e)}'
            }, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'فرمت داده نامعتبر است'
        }, status=400)
    except Exception as e:
        logger.error(f"Error in submit_all_formula_values: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)