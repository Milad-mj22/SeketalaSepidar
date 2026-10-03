from datetime import datetime
import json

from django.contrib.sites import requests
from django.shortcuts import render

# Create your views here.
from django.contrib.auth.decorators import login_required

from SepidarApp.Steps.save_order import save_multiple_product_orders
from SepidarApp.models import WarehouseRelation
from SepidarApp.utils import get_creator_sepidar, persian_to_gregorian

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

from .databaseConnector import DatabaseConnection, db

logger = logging.getLogger(__name__)
@login_required
def formula_list(request):
    try:
        db.connect()

        # ============================================
        # تشخیص حالت نمایش
        # ============================================
        relation_id = request.GET.get('relation_id')
        show_all = request.GET.get('show_all') == '1'   # ✅ چک‌باکس

        allowed_formula_ids = None
        selected_relation = None
        selected_relation_id = None

        # ✅ اگه "نمایش همه" فعاله، فیلتر نکن
        if not show_all and relation_id:
            try:
                selected_relation = WarehouseRelation.objects.get(id=relation_id)
                selected_relation_id = selected_relation.id
                allowed_formula_ids = set(
                    selected_relation.formula_relations
                        .filter(is_deleted=False)
                        .values_list('formula_id', flat=True)
                )
            except WarehouseRelation.DoesNotExist:
                pass

        # ============================================
        # همه فرمول‌ها از سپیدار
        # ============================================
        results = db.get_formulas_with_items()

        formulas = {}
        for row in results:
            formula_id = row.ProductFormulaID

            # ✅ فیلتر بر اساس رابطه (اگه show_all نیست)
            if allowed_formula_ids is not None and formula_id not in allowed_formula_ids:
                continue

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

        formula_list = list(formulas.values())

        # آمار
        total_formulas = len(formula_list)
        active_formulas = sum(1 for f in formula_list if f['is_active'])
        total_items = sum(len(f['items']) for f in formula_list)

        relations = WarehouseRelation.objects.select_related(
            'source_warehouse', 'destination_warehouse'
        ).all()

        # Session data
        exist = False
        try:
            needed_materials = request.session['needed_materials']
            selected_date = request.session['materials_date']
            count = request.session['materials_count']
            exist = True
        except:
            if not exist:
                needed_materials = []
                selected_date = []
                count = []

        error_message = request.GET.get('error', '')

        materials_by_code = {}
        for material in needed_materials:
            code = material.get('code', '')
            if code:
                materials_by_code[code] = material

        context = {
            'formulas': formula_list,
            'total_formulas': total_formulas,
            'active_formulas': active_formulas,
            'total_items': total_items,
            'inactive_formulas': total_formulas - active_formulas,
            'relations': relations,
            'needed_materials': needed_materials,
            'materials_by_code': materials_by_code,
            'needed_material_codes': list(materials_by_code.keys()),
            'has_needed_materials': len(needed_materials) > 0,
            'selected_date': selected_date,
            'count': count,
            'error_message': error_message,
            'selected_relation_id': selected_relation_id,
            'selected_relation': selected_relation,
            'show_all': show_all,  # ✅ اضافه کن
        }

        return render(request, 'formula_list.html', context)

    except Exception as e:
        logger.error(f"Error in formula_list: {e}")
        return render(request, 'error.html', {'error': str(e)})
    finally:
        db.close()

# ============================================================
# API: فرمول‌های مجاز یک رابطه
# ============================================================
@login_required
def api_relation_formulas(request, relation_id):
    """
    API: دریافت لیست ID فرمول‌های مجاز یک رابطه
    """
    try:
        relation = WarehouseRelation.objects.get(id=relation_id)
        allowed_ids = list(
            relation.formula_relations
                .filter(is_deleted=False)
                .values_list('formula_id', flat=True)
        )
        return JsonResponse({
            'success': True,
            'formula_ids': allowed_ids,
            'count': len(allowed_ids),
        })
    except WarehouseRelation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'رابطه یافت نشد'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

              
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
@login_required
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
        selected_date = data.get('selectedDate',None)
        
        if not formulas:
            return JsonResponse({
                'success': False,
                'error': 'هیچ مقداری برای ثبت وجود ندارد'
            }, status=400)

        georgian_date = None
        if selected_date is not None and selected_date !='':
            georgian_date = persian_to_gregorian(selected_date)
      

        
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
        cost_stock = relation.cost_stock
        moin_code = relation.moin_code
        deliverer_ref = relation.deliverer_ref
        order_registration_notes = relation.order_registration_notes

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

            # ============================================
            # 1️⃣ دریافت مواد اولیه اصلی فرمول از دیتابیس
            # ============================================
            recipe_items = get_formula_recipe(db, formula_id)

            if recipe_items is None:
                recipe_items = []

            # ============================================
            # 2️⃣ ✅ اضافه کردن مواد موقت به recipe_items
            # (موادی که کاربر توی فرانت اضافه کرده و توی فرمول اصلی نیستن)
            # ============================================
            existing_item_refs = {str(r.get('ItemRef')) for r in recipe_items}

            for w_item in withdrawal_items:
                w_item_ref = str(w_item.get('item_ref', '')).strip()

                # اگه این ماده توی فرمول اصلی نیست، اضافه‌ش کن
                if w_item_ref and w_item_ref not in existing_item_refs:
                    w_item_name = w_item.get('item_name', '')
                    withdrawal_amount = float(w_item.get('withdrawal_amount', 0) or 0)

                    if withdrawal_amount > 0:
                        # ✅ دریافت unit_ref از دیتابیس
                        unit_ref = None
                        unit_name = ''
                        try:
                            conn_temp = db.get_connection()
                            cursor_temp = conn_temp.cursor()
                            cursor_temp.execute("""
                                SELECT i.UnitRef, u.Title AS UnitName
                                FROM [Sepidar01].[INV].[Item] i
                                LEFT JOIN [Sepidar01].[INV].[Unit] u ON i.UnitRef = u.UnitID
                                WHERE i.ItemID = ?
                            """, (w_item_ref,))
                            row_temp = cursor_temp.fetchone()
                            if row_temp:
                                unit_ref = row_temp[0] if row_temp[0] else 1
                                unit_name = row_temp[1] or ''
                        except Exception as e:
                            logger.warning(f"Could not fetch unit for temp item {w_item_ref}: {e}")
                            unit_ref = 1

                        # ✅ اضافه به recipe_items با فرمت یکسان
                        recipe_items.append({
                            'FormulaBomItemID': None,   # ماده موقت BomItem نداره
                            'ItemRef': int(w_item_ref) if w_item_ref.isdigit() else w_item_ref,
                            'Quantity': 0,               # مقدار در هر واحد فرمول نداره
                            'SecondaryQuantity': 0,
                            'Description': 'ماده موقت اضافه‌شده توسط کاربر',
                            'ItemTracingRef': None,
                            'ItemName': w_item_name,
                            'ItemCode': '',
                            'UnitRef': unit_ref,
                            'UnitName': unit_name,
                            'IsTemp': True,
                            'WithdrawalAmount': withdrawal_amount,
                        })

                        existing_item_refs.add(w_item_ref)
                        logger.info(f"✅ ماده موقت {w_item_ref} ({w_item_name}) به فرمول {formula_id} اضافه شد")

            # ============================================
            # 3️⃣ محاسبه مقدار مورد نیاز برای هر ماده
            # ============================================
            formula_materials = []
            for recipe in recipe_items:
                item_ref = recipe.get('ItemRef')
                item_name = recipe.get('ItemName')
                unit_ref = recipe.get('UnitRef')
                unit_name = recipe.get('UnitName')
                quantity_per_unit = recipe.get('Quantity', 0)
                is_temp = recipe.get('IsTemp', False)

                # ✅ محاسبه مقدار مورد نیاز
                if is_temp:
                    # مواد موقت: از withdrawal_amount استفاده کن
                    required_quantity = recipe.get('WithdrawalAmount', 0)
                else:
                    # مواد اصلی: مقدار مصرفی * مقدار در هر واحد
                    required_quantity = consumption_value * quantity_per_unit

                # مقدار برداشتی کاربر
                user_withdrawal = next(
                    (w.get('withdrawal_amount', 0) for w in withdrawal_items
                     if str(w.get('item_ref')) == str(item_ref)),
                    0
                )

                formula_materials.append({
                    'item_ref': item_ref,
                    'item_name': item_name,
                    'unit_ref': unit_ref,
                    'unit_name': unit_name,
                    'quantity_per_unit': quantity_per_unit,
                    'required_quantity': required_quantity,
                    'withdrawal_amount': user_withdrawal,
                    'is_temp': is_temp
                })

                # ✅ جمع‌آوری در دیکشنری اصلی
                key = f"{item_ref}_{unit_ref}"
                required_materials[key]['total_required'] += required_quantity
                required_materials[key]['item_name'] = item_name
                required_materials[key]['unit_name'] = unit_name
                required_materials[key]['item_ref'] = item_ref
                required_materials[key]['bom_item_id'] = recipe.get('FormulaBomItemID')
                required_materials[key]['is_temp'] = is_temp

            # ============================================
            # 4️⃣ ذخیره جزئیات فرمول
            # ============================================
            formula_details.append({
                'formula_id': formula_id,
                'product_id': product_id,
                'product_unit': product_unit,
                'consumption_value': consumption_value,
                'total_withdrawal': total_withdrawal,
                'withdrawal_items': withdrawal_items,
                'materials': formula_materials
            })

            # ============================================
            # 5️⃣ جمع‌آوری جزئیات برداشت
            # ============================================
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
        
        creator_id = get_creator_sepidar(request)



        # ذخیره مقادیر در دیتابیس
        saved_formulas = []
        all_exist = True
        if all_exist:
            pass

            # for item in formulas:
            save_results  = save_multiple_product_orders(db,formulas,stock_source_ref,stock_dest_ref,\
                                                         georgian_date,moin_code=moin_code,cost_stock=cost_stock,\
                                                         dl_ref=deliverer_ref,   notes =order_registration_notes ,creator=creator_id)

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



        # ============================================
        # ✅ ثبت تاریخچه فعالیت
        # ============================================
        from SepidarApp.utils import log_activity
        
        # ✅ جمع‌آوری شماره‌های رسید از نتایج
        receipt_numbers = []
        if saved_results:
            for r in saved_results:
                if r.get('success'):
                    num = r.get('number') or r.get('product_order_id')
                    if num:
                        receipt_numbers.append(str(num))
        
        receipt_number_str = ', '.join(receipt_numbers) if receipt_numbers else None
        
        # ✅ شمارش مواد موقت
        total_temp = sum(
            1 for f in formulas 
            for w in f.get('withdrawal_items', []) 
            if w.get('is_temp')
        )
        
        # ✅ شمارش کل مواد
        total_items = sum(
            len(f.get('withdrawal_items', [])) 
            for f in formulas
        )
        
        if all_exist and saved_count > 0:
            # ✅ لاگ موفق
            log_activity(
                request=request,
                action_type='formula_submit',
                relation=relation,
                receipt_number=receipt_number_str,
                description=f"{saved_count} فرمول با موفقیت ثبت شد",
                details={
                    'formulas': [
                        {
                            'formula_id': f.get('formula_id'),
                            'formula_code': f.get('formula_code'),
                            'formula_title': f.get('formula_title'),
                            'consumption_value': f.get('consumption_value'),
                            'total_withdrawal': f.get('total_withdrawal'),
                            'items_count': len(f.get('withdrawal_items', [])),
                            'temp_items_count': sum(1 for w in f.get('withdrawal_items', []) if w.get('is_temp')),
                        }
                        for f in formulas
                    ],
                    'saved_count': saved_count,
                    'selected_date': selected_date,
                },
                total_formulas=len(formulas),
                total_items=total_items,
                total_temp_items=total_temp,
            )




        
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










def auto_order(request):
    return render(request,'auto_order.html')



import requests as http_requests  # Alias to avoid conflict
@login_required
@require_http_methods(["GET"])
def get_materials(request):
    """
    Fetch materials from external API based on date
    """
    try:
        # Get date from request
        start_date = request.GET.get('start_date')
        if not start_date:
            return JsonResponse({
                'success': False,
                'error': 'تاریخ شروع الزامی است'
            })

        end_date = request.GET.get('end_date')
        if not end_date:
            return JsonResponse({
                'success': False,
                'error': 'تاریخ پایان الزامی است'
            })

        
        # Convert Persian date to Gregorian
        try:
            start_gregorian_date = persian_to_gregorian(start_date)
            logger.info(f"Converted Persian date '{start_date}' to Gregorian '{start_gregorian_date}'")
            end_gregorian_date = persian_to_gregorian(end_date)
            logger.info(f"Converted Persian date '{end_date}' to Gregorian '{end_gregorian_date}'")
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
        except Exception as e:
            logger.error(f"Date conversion error: {e}")
            return JsonResponse({
                'success': False,
                'error': 'تاریخ صحیح نیست'
            })
        
        # Call external API with Gregorian date
        api_url = f"http://127.0.0.1:8900/data_analysis/api/get-date-items/?start_date={start_gregorian_date}&end_date={end_gregorian_date}"
        logger.info(f"Calling external API: {api_url}")
        
        # Use the alias http_requests instead of requests
        response = http_requests.get(api_url, timeout=30)
        
        # Check if external API call was successful
        if response.status_code == 200:
            external_data = response.json()
            
            # Check if external API returned success
            if external_data.get('success'):
                # Extract data from external API
                # The external API returns data as dict: {'10': 11, '11': 22, ...}
                external_items = external_data.get('data', {})
                
                # Convert to array format expected by frontend
                materials = []
                for code, quantity in external_items[0].items():
                    materials.append({
                        'code': code,
                        'name': f'ماده {code}',  # You might want to map codes to names
                        'quantity': quantity,
                        'available_quantity': quantity,  # Assuming available = required for now
                    })
                
                return JsonResponse({
                    'success': True,
                    'data': external_items,  # Send as array
                    'date': start_date,
                    'gregorian_date': start_gregorian_date,
                    'total_items': len(materials)
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': external_data.get('error', 'خطا در دریافت اطلاعات از سرویس خارجی')
                })
        else:
            return JsonResponse({
                'success': False,
                'error': f'خطا در ارتباط با سرویس خارجی: {response.status_code}',
                'details': response.text
            })
            
    except http_requests.exceptions.Timeout:
        logger.error("External API timeout")
        return JsonResponse({
            'success': False,
            'error': 'زمان اتصال به سرور به پایان رسید'
        })
    except http_requests.exceptions.ConnectionError:
        logger.error("External API connection error")
        return JsonResponse({
            'success': False,
            'error': 'خطا در اتصال به سرور'
        })
    except Exception as e:
        logger.error(f"Error in get_materials: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
    



def get_product_id(db,product_code):
    try:
        query = """
            SELECT 
                fbi.ItemID
            FROM [Sepidar01].[INV].[Item] fbi
            WHERE fbi.Code = ?
        """
        results = db.execute_query(query, product_code)
        
        if results and len(results) > 0:
            return results[0][0]
    except Exception as e:
        logger.error(f"Error getting formul id for prdouct :  {product_code}: {e}")
        return None





def get_formula_id(db,product_id):
    try:
        query = """
            SELECT 
                fbi.ProductFormulaID,
                fbi.Code,
                fbi.Title
            FROM [Sepidar01].[WKO].[ProductFormula] fbi
            WHERE fbi.ItemRef = ?
        """
        results = db.execute_query(query, product_id)
        
        if results and len(results) > 0:
            return {
                'formula_id':results[0][0],
                'formula_code':results[0][1],
                'formula_title':results[0][2],
            }
        
    except Exception as e:
        logger.error(f"Error getting formul id for prdouct :  {product_id}: {e}")
        return None







from django.shortcuts import redirect
from django.urls import reverse
import urllib.parse
import json


from django.shortcuts import redirect
from django.urls import reverse
import json
import logging

logger = logging.getLogger(__name__)
@login_required
@csrf_exempt
@require_http_methods(["POST"])
def submit_materials(request):
    try:
        data = json.loads(request.body)
        materials = data.get('materials', [])
        date = data.get('start_date')
        end_date = data.get('end_date')
        
        if not materials:
            return redirect(f"{reverse('sepidarApp:formula_list')}?error={urllib.parse.quote('هیچ داده‌ای برای ثبت وجود ندارد')}")

        

        
        needed_items = []
        saved_count = 0
        
        for material in materials:
            try:
                code =  material.get('code', 0)
                try:
                    code = int(code)
                    if code =='' or code<=0:
                        continue
                except Exception as e:
                    print(f'Error in convert code to int Code : {code} , ',e)
                    continue

                if material.get('adjusted_quantity', 0) > 0 or material.get('has_code_changed', False):
                    item_data = {
                        'code': material.get('code', ''),
                        'original_code': material.get('original_code', ''),
                        'quantity': material.get('adjusted_quantity', 0),
                        'original_quantity': material.get('original_quantity', 0),
                        'name': material.get('name', ''),
                        'available_quantity': material.get('available_quantity', 0),
                        'has_code_changed': material.get('has_code_changed', False),
                        'has_quantity_changed': material.get('has_quantity_changed', False)
                    }
                    needed_items.append(item_data)
                    saved_count += 1
            except Exception as e:
                logger.error(f"Error processing material {material.get('code')}: {e}")
        
        if saved_count > 0:
            # ذخیره در session
            request.session['needed_materials'] = needed_items
            request.session['materials_date'] = date
            request.session['materials_count'] = saved_count
            
            # هدایت به صفحه فرمول
            return redirect('sepidarApp:formula_list')
        else:
            error_msg = 'هیچ ماده‌ای با مقدار مثبت یا کد تغییر یافته وجود ندارد'
            return redirect(f"{reverse('sepidarApp:formula_list')}?error={urllib.parse.quote(error_msg)}")
            
    except json.JSONDecodeError:
        return redirect(f"{reverse('sepidarApp:formula_list')}?error={urllib.parse.quote('داده‌های ارسالی معتبر نیستند')}")
    except Exception as e:
        logger.error(f"Error in submit_materials: {e}")
        return redirect(f"{reverse('sepidarApp:formula_list')}?error={urllib.parse.quote(str(e))}")






def change_sl_acc_ref(request):
    """
    Get the last 10 InventoryReceipt records for a given StockRef,
    and for each one where SLAccountRef == old_sl_account_ref,
    update it to new_sl_account_ref and save.

    Parameters:
    - db_connection: Database connection object
    - stock_ref: Warehouse reference to filter receipts
    - old_sl_account_ref: The SLAccountRef to find (default 786)
    - new_sl_account_ref: The SLAccountRef to set (default 825)

    Returns:
    - dict with success flag, updated records, and errors
    """
    conn = None
    db_connection = db
    old_sl_account_ref: int = 786,
    new_sl_account_ref: int = 825

    try:
        conn = db_connection.get_connection()
        cursor = conn.cursor()

        # 1. Get last 10 InventoryReceipt records for the given StockRef
        cursor.execute("""
            SELECT TOP 10 InventoryReceiptID, Number, SLAccountRef
            FROM [Sepidar01].[INV].[InventoryReceipt]
            ORDER BY InventoryReceiptID DESC
        """, )

        rows = cursor.fetchall()

        if not rows:
            return {
                'success': True,
                'message': 'No inventory receipts found',
                'updated': [],
                'skipped': []
            }

        updated_records = []
        skipped_records = []

        # 2. Loop through each receipt
        for row in rows:
            receipt_id = row[0]
            number = row[1]
            sl_account_ref = row[2]

            # 3. Only update if SLAccountRef == 786
            if sl_account_ref == old_sl_account_ref:
                skipped_records.append({
                    'InventoryReceiptID': receipt_id,
                    'Number': number,
                    'SLAccountRef': sl_account_ref,
                    'reason': f'SLAccountRef is not {old_sl_account_ref}'
                })
                continue

            # 4. Update SLAccountRef to 825 and save
            cursor.execute("""
                UPDATE [Sepidar01].[INV].[InventoryReceipt]
                SET SLAccountRef = ?,
                    LastModificationDate = ?
                WHERE InventoryReceiptID = ?
            """, (new_sl_account_ref, datetime.now(), receipt_id))

            updated_records.append({
                'InventoryReceiptID': receipt_id,
                'Number': number,
                'old_SLAccountRef': sl_account_ref,
                'new_SLAccountRef': new_sl_account_ref
            })

            logger.info(
                f"Updated InventoryReceipt ID {receipt_id}, Number {number}: "
                f"SLAccountRef {old_sl_account_ref} -> {new_sl_account_ref}"
            )

        # 5. Commit all updates
        conn.commit()

        return {
            'success': True,
            'updated': updated_records,
            'skipped': skipped_records,
            'total_checked': len(rows),
            'total_updated': len(updated_records),
            'total_skipped': len(skipped_records)
        }

    except Exception as e:
        logger.error(f"Error updating receipts SLAccountRef: {e}")
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        return {
            'success': False,
            'error': str(e)
        }









def change_sl_acc_ref_for_last_ten_delivery_items(request):
    """
    Get the last 10 InventoryDeliveryItem records,
    and for each one where SLAccountRef == 786,
    update it to 825 and save.

    Returns:
    - dict with success flag, updated records, and errors
    """
    conn = None
    db_connection = db
    old_sl_account_ref = 786
    new_sl_account_ref = 825

    try:
        conn = db_connection.get_connection()
        cursor = conn.cursor()

        # 1. Get last 10 InventoryDeliveryItem records
        cursor.execute("""
            SELECT TOP 10 InventoryDeliveryItemID, InventoryDeliveryRef, RowNumber, SLAccountRef
            FROM [Sepidar01].[INV].[InventoryDeliveryItem]
            ORDER BY InventoryDeliveryItemID DESC
        """)

        rows = cursor.fetchall()

        if not rows:
            return {
                'success': True,
                'message': 'No inventory delivery items found',
                'updated': [],
                'skipped': []
            }

        updated_records = []
        skipped_records = []

        # 2. Loop through each item
        for row in rows:
            item_id = row[0]
            delivery_ref = row[1]
            row_number = row[2]
            sl_account_ref = row[3]

            # 3. Skip if SLAccountRef is not 786
            if sl_account_ref == new_sl_account_ref:
                skipped_records.append({
                    'InventoryDeliveryItemID': item_id,
                    'InventoryDeliveryRef': delivery_ref,
                    'RowNumber': row_number,
                    'SLAccountRef': sl_account_ref,
                    'reason': f'SLAccountRef is {new_sl_account_ref}'
                })
                continue

            # 4. Update SLAccountRef to 825 and save
            cursor.execute("""
                UPDATE [Sepidar01].[INV].[InventoryDeliveryItem]
                SET SLAccountRef = ?
                WHERE InventoryDeliveryItemID = ?
            """, (new_sl_account_ref, item_id))

            updated_records.append({
                'InventoryDeliveryItemID': item_id,
                'InventoryDeliveryRef': delivery_ref,
                'RowNumber': row_number,
                'old_SLAccountRef': sl_account_ref,
                'new_SLAccountRef': new_sl_account_ref
            })

            logger.info(
                f"Updated InventoryDeliveryItem ID {item_id}, "
                f"DeliveryRef {delivery_ref}, Row {row_number}: "
                f"SLAccountRef {old_sl_account_ref} -> {new_sl_account_ref}"
            )

        # 5. Commit all updates
        conn.commit()

        return {
            'success': True,
            'updated': updated_records,
            'skipped': skipped_records,
            'total_checked': len(rows),
            'total_updated': len(updated_records),
            'total_skipped': len(skipped_records)
        }

    except Exception as e:
        logger.error(f"Error updating last 10 delivery items SLAccountRef: {e}")
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        return {
            'success': False,
            'error': str(e)
        }
    


# SepidarApp/views.py
@login_required
@require_http_methods(["GET"])
def api_get_all_items(request):
    """
    API: دریافت همه مواد از سپیدار با واحد درست
    فقط خواندنی — بدون ذخیره‌سازی
    """
    try:
        from SepidarApp.databaseConnector import db
        db.connect()
        conn = db.get_connection()
        cursor = conn.cursor()

        search = request.GET.get('q', '').strip()

        if search:
            query = """
                SELECT 
                    i.ItemID,
                    i.Code,
                    i.Title,
                    i.UnitRef,
                    u.Title AS UnitTitle,
                    i.SecondaryUnitRef,
                    su.Title AS SecondaryUnitTitle,
                    i.MinimumAmount
                FROM [Sepidar01].[INV].[Item] i
                LEFT JOIN [Sepidar01].[INV].[Unit] u ON i.UnitRef = u.UnitID
                LEFT JOIN [Sepidar01].[INV].[Unit] su ON i.SecondaryUnitRef = su.UnitID
                WHERE i.IsActive = 1 
                  AND (i.Code LIKE ? OR i.Title LIKE ?)
                ORDER BY i.Code
            """
            pattern = f"%{search}%"
            cursor.execute(query, (pattern, pattern))
        else:
            # ✅ همه مواد بدون محدودیت
            query = """
                SELECT 
                    i.ItemID,
                    i.Code,
                    i.Title,
                    i.UnitRef,
                    u.Title AS UnitTitle,
                    i.SecondaryUnitRef,
                    su.Title AS SecondaryUnitTitle,
                    i.MinimumAmount
                FROM [Sepidar01].[INV].[Item] i
                LEFT JOIN [Sepidar01].[INV].[Unit] u ON i.UnitRef = u.UnitID
                LEFT JOIN [Sepidar01].[INV].[Unit] su ON i.SecondaryUnitRef = su.UnitID
                WHERE i.IsActive = 1
                ORDER BY i.Code
            """
            cursor.execute(query)

        rows = cursor.fetchall()

        items = []
        for row in rows:
            items.append({
                'id': int(row[0]),
                'code': row[1] or '',
                'title': row[2] or '',
                'unit_ref': int(row[3]) if row[3] else None,
                'unit_title': row[4] or '',
                'secondary_unit_ref': int(row[5]) if row[5] else None,
                'secondary_unit_title': row[6] or '',
                'minimum_amount': float(row[7]) if row[7] else 0,
            })

        return JsonResponse({
            'success': True,
            'items': items,
            'count': len(items)
        })

    except Exception as e:
        logger.error(f"Error in api_get_all_items: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)








# SepidarApp/views.py
from SepidarApp.activity_helper import (
    get_accounting_vouchers, get_users_map, get_all_activities,
    get_product_orders, get_inventory_deliveries, get_inventory_receipts,
)
import jdatetime
from collections import defaultdict


@login_required(login_url='authentication:sign-in')
def sepidar_activity_report(request):
    """
    گزارش فعالیت کاربران — مستقیم از سپیدار
    """
    try:
        # ============================================
        # 1️⃣ فیلترها
        # ============================================
        creator_filter = request.GET.get('creator', '').strip()
        date_from_shamsi = request.GET.get('date_from', '').strip()
        date_to_shamsi = request.GET.get('date_to', '').strip()
        activity_type = request.GET.get('activity_type', '').strip()

        # تبدیل تاریخ شمسی به میلادی
        date_from_gregorian = None
        date_to_gregorian = None

        if date_from_shamsi:
            try:
                date_from_gregorian = persian_to_gregorian(date_from_shamsi)
            except Exception:
                pass

        if date_to_shamsi:
            try:
                date_to_gregorian = persian_to_gregorian(date_to_shamsi)
            except Exception:
                pass

        # پیش‌فرض: ۷ روز اخیر
        if not date_from_gregorian and not date_to_gregorian:
            today = jdatetime.date.today()
            week_ago = today - jdatetime.timedelta(days=7)
            date_from_shamsi = week_ago.strftime('%Y/%m/%d')
            date_to_shamsi = today.strftime('%Y/%m/%d')
            try:
                date_from_gregorian = persian_to_gregorian(date_from_shamsi)
                date_to_gregorian = persian_to_gregorian(date_to_shamsi)
            except Exception:
                pass

        # ============================================
        # 2️⃣ خواندن از سپیدار
        # ============================================
        db.connect()

        users_map = get_users_map()

        # فیلتر کاربر
        creator_id = None
        if creator_filter:
            try:
                creator_id = int(creator_filter)
            except ValueError:
                pass

        # خواندن همه فعالیت‌ها
        if activity_type == 'product_order':
            activities = get_product_orders(date_from_gregorian, date_to_gregorian, creator_id)
        elif activity_type == 'inventory_delivery':
            activities = get_inventory_deliveries(date_from_gregorian, date_to_gregorian, creator_id)
        elif activity_type == 'inventory_receipt':
            activities = get_inventory_receipts(date_from_gregorian, date_to_gregorian, creator_id)
        elif activity_type == 'accounting_voucher':
            activities = get_accounting_vouchers(date_from_gregorian, date_to_gregorian, creator_id)
        else:
            activities = get_all_activities(date_from_gregorian, date_to_gregorian, creator_id)
        # ============================================
        # 3️⃣ گروه‌بندی بر اساس کاربر + روز
        # ============================================
        grouped = defaultdict(lambda: {
            'user_id': None,
            'user_name': '',
            'date_gregorian': None,
            'date_shamsi': '',
            'product_orders': [],
            'deliveries': [],
            'receipts': [],
            'vouchers': [],   # ✅ این
        })

        for act in activities:
            # کاربر
            uid = act.get('creator')
            user_info = users_map.get(uid, {})
            user_name = user_info.get('full_name', f'کاربر {uid}') if uid else 'نامشخص'

            # تاریخ
            act_date = act.get('date')
            if act_date:
                # میلادی
                if hasattr(act_date, 'date'):
                    date_only = act_date.date()
                else:
                    date_only = act_date

                # شمسی
                try:
                    shamsi = jdatetime.date.fromgregorian(date=date_only)
                    shamsi_str = f"{shamsi.year}/{shamsi.month:02d}/{shamsi.day:02d}"
                except Exception:
                    shamsi_str = str(date_only)
            else:
                date_only = None
                shamsi_str = '-'

            key = (uid, str(date_only))

            grouped[key]['user_id'] = uid
            grouped[key]['user_name'] = user_name
            grouped[key]['date_gregorian'] = date_only
            grouped[key]['date_shamsi'] = shamsi_str

            if act['activity_type'] == 'product_order':
                grouped[key]['product_orders'].append(act)
            elif act['activity_type'] == 'inventory_delivery':
                grouped[key]['deliveries'].append(act)
            elif act['activity_type'] == 'inventory_receipt':
                grouped[key]['receipts'].append(act)
            elif act['activity_type'] == 'accounting_voucher':
                grouped[key]['vouchers'].append(act)
        # ============================================
        # 4️⃣ تبدیل به لیست مرتب‌شده
        # ============================================
        daily_reports = []
        for key, data in grouped.items():
            # زمان شروع/پایان
            all_dates = []
            for po in data['product_orders']:
                if po['date']:
                    all_dates.append(po['date'])
            for d in data['deliveries']:
                if d['date']:
                    all_dates.append(d['date'])
            for r in data['receipts']:
                if r['date']:
                    all_dates.append(r['date'])

            first_time = min(all_dates).strftime('%H:%M') if all_dates else '-'
            last_time = max(all_dates).strftime('%H:%M') if all_dates else '-'

            total_activities = len(data['product_orders']) + len(data['deliveries']) + len(data['receipts'])

            daily_reports.append({
                'user_id': data['user_id'],
                'user_name': data['user_name'],
                'date_shamsi': data['date_shamsi'],
                'date_gregorian': data['date_gregorian'],
                'first_time': first_time,
                'last_time': last_time,
                'product_orders': data['product_orders'],
                'deliveries': data['deliveries'],
                'receipts': data['receipts'],
                'total_orders': len(data['product_orders']),
                'total_deliveries': len(data['deliveries']),
                'total_receipts': len(data['receipts']),
                'vouchers': data['vouchers'],
                'total_vouchers': len(data['vouchers']),

                'total_activities': total_activities,
            })

        # مرتب‌سازی: جدیدترین روز اول
        daily_reports.sort(
            key=lambda x: (x['date_gregorian'] or datetime.min.date(), x['user_name']),
            reverse=True
        )

        # ============================================
        # 5️⃣ آمار خلاصه
        # ============================================
        stats = {
            'total_reports': len(daily_reports),
            'total_orders': sum(r['total_orders'] for r in daily_reports),
            'total_deliveries': sum(r['total_deliveries'] for r in daily_reports),
            'total_receipts': sum(r['total_receipts'] for r in daily_reports),
            'total_users': len(set(r['user_id'] for r in daily_reports if r['user_id'])),
            'total_vouchers': sum(r['total_vouchers'] for r in daily_reports),
        }

        db.close()

        # ============================================
        # 6️⃣ لیست کاربران برای فیلتر
        # ============================================
        users_list = [
            {'id': uid, 'name': info['full_name']}
            for uid, info in sorted(users_map.items(), key=lambda x: x[1]['full_name'])
        ]





        # ============================================
        # ✅ داده‌های نمودار — به ازای هر کاربر
        # ============================================

        chart_users = defaultdict(lambda: {
            'user_id': None,
            'user_name': '',
            'orders': 0,
            'deliveries': 0,
            'receipts': 0,
            'vouchers': 0,
            'total': 0,
        })

        chart_daily = defaultdict(lambda: {
            'orders': 0,
            'deliveries': 0,
            'receipts': 0,
            'vouchers': 0,
        })

        # از daily_reports استفاده کن
        for report in daily_reports:
            uid = report['user_id']
            uname = report['user_name']

            # کاربر
            chart_users[uid]['user_id'] = uid
            chart_users[uid]['user_name'] = uname
            chart_users[uid]['orders'] += report['total_orders']
            chart_users[uid]['deliveries'] += report['total_deliveries']
            chart_users[uid]['receipts'] += report['total_receipts']
            chart_users[uid]['vouchers'] += report.get('total_vouchers', 0)
            chart_users[uid]['total'] += report['total_activities']

            # روزانه
            day = report['date_shamsi']
            chart_daily[day]['orders'] += report['total_orders']
            chart_daily[day]['deliveries'] += report['total_deliveries']
            chart_daily[day]['receipts'] += report['total_receipts']
            chart_daily[day]['vouchers'] += report.get('total_vouchers', 0)

        # تبدیل به لیست
        chart_users_list = sorted(chart_users.values(), key=lambda x: x['total'], reverse=True)
        chart_daily_list = []
        for date_str in sorted(chart_daily.keys()):
            chart_daily_list.append({
                'date': date_str,
                'orders': chart_daily[date_str]['orders'],
                'deliveries': chart_daily[date_str]['deliveries'],
                'receipts': chart_daily[date_str]['receipts'],
                'vouchers': chart_daily[date_str]['vouchers'],
            })

        # تبدیل به JSON برای جاوااسکریپت
        chart_data_json = json.dumps({
            'users': chart_users_list,
            'daily': chart_daily_list,
            'totals': {
                'orders': stats['total_orders'],
                'deliveries': stats['total_deliveries'],
                'receipts': stats['total_receipts'],
                'vouchers': stats.get('total_vouchers', 0),
            }
        }, ensure_ascii=False)








        context = {
            'daily_reports': daily_reports,
            'stats': stats,
            'users_list': users_list,
            'creator_filter': creator_filter,
            'date_from_shamsi': date_from_shamsi,
            'date_to_shamsi': date_to_shamsi,
            'activity_type': activity_type,
            'active_page': 'sepidar_activity_report',
            'chart_data_json': chart_data_json,   # ✅ اضافه کن
        }

        return render(request, 'sepidar_activity_report.html', context)

    except Exception as e:
        logger.error(f"Error in sepidar_activity_report: {e}", exc_info=True)
        try:
            db.close()
        except Exception:
            pass
        return render(request, 'error.html', {'error': str(e)})







@login_required
def test_daily_report(request):
    """
    تست دستی: فقط متن گزارش رو نشون بده
    """
    from SepidarApp.reports import build_daily_report_text, send_daily_report_sms
    
    # تاریخ دلخواه
    date_str = request.GET.get('date', '')
    for_date = None
    
    if date_str:
        try:
            for_date = persian_to_gregorian(date_str)
        except Exception:
            pass
    
    # حالت‌ها:
    # 1. فقط متن: ?date=1405/07/11
    # 2. با پیامک: ?date=1405/07/11&send_sms=1
    
    if request.GET.get('send_sms') == '1':
        # ساخت + ارسال
        result = send_daily_report_sms(for_date)
        return JsonResponse(result)
    else:
        # فقط ساخت متن
        result = build_daily_report_text(for_date)
        return JsonResponse(result)