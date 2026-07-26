
0 =
{'formula_id': 10, 'formula_code': '100', 'formula_title': 'كاهو خرد شده آماده سازي', 'product_id': None, 'product_unit': '', 'consumption_value': 1, 'total_withdrawal': 1.5, 'withdrawal_items': [{...}]}
special variables
function variables
'formula_id' =
10
'formula_code' =
'100'
'formula_title' =
'كاهو خرد شده آماده سازي'
'product_id' =
None
'product_unit' =
''
'consumption_value' =
1
'total_withdrawal' =
1.5
'withdrawal_items' =
[{'item_ref': '1958', 'item_name': 'كاهو', 'quantity': 1.5, 'withdrawal_amount': 1.5}]
len() =
8









this is my page that render first page :

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


i want to add a auntity default for each formula that show in the page with this code :

@csrf_exempt
@require_http_methods(["POST"])
def submit_materials(request):
    """
    Submit adjusted materials data
    """
    try:
        data = json.loads(request.body)
        materials = data.get('materials', [])
        date = data.get('date')
        
        if not materials:
            return JsonResponse({
                'success': False,
                'error': 'هیچ داده‌ای برای ثبت وجود ندارد'
            })
        
        # Process each material
        saved_count = 0
        errors = []
        
        for material in materials:
            try:
                # Your logic to save material data
                # For example, save to database or call another API
                
                # Example: Save to database (you need to implement your model)
                # Material.objects.create(
                #     code=material.get('code'),
                #     name=material.get('name'),
                #     original_quantity=material.get('original_quantity', 0),
                #     adjusted_quantity=material.get('adjusted_quantity', 0),
                #     available_quantity=material.get('available_quantity', 0),
                #     date=date,
                #     created_at=datetime.now()
                # )
                # product_code = get_product_id(db,material['code'])
                # if product_code is None:
                #     print(f'Code not Exist for Item : {material['code']}  {material['name']}')
                #     continue
                # formula_id = get_formula_id(db,product_code)
                # if formula_id is None:
                #     print(f'Formula not Exist for Item : {material['code']}  {material['name']}')
                #     continue

                # recipe_items = get_formula_recipe(db, formula_id['formula_id'])
                # recipe_items = update_formula_recipe(recipe_items)

                
                # saved_count += 1
                
            except Exception as e:
                errors.append(f"خطا در ثبت {material.get('name')}: {str(e)}")
                logger.error(f"Error saving material {material.get('code')}: {e}")
        
        if saved_count > 0:
            return JsonResponse({
                'success': True,
                'message': f'{saved_count} ماده با موفقیت ثبت شد',
                'saved_count': saved_count,
                'errors': errors if errors else None
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'هیچ ماده‌ای ثبت نشد',
                'errors': errors
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'داده‌های ارسالی معتبر نیستند'
        })
    except Exception as e:
        logger.error(f"Error in submit_materials: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

من میخام لیست متریال ها که شامل code و تعداد است به اون تاربع ارسال بشه و دریافت کنه این نقدار راه هم و به فرانت بفرسته تا نمایش بده «/