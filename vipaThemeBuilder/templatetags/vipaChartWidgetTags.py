from django import template
from django.utils.safestring import mark_safe
import json
from ..vipaThemeDataClass.vipaChartDataClass import barChartSeries, barChartDataClass
from ..vipaThemeDataClass.vipaChartDataClass import lineChartDataClass, lineChartSeries
register = template.Library()

@register.inclusion_tag('templates_tags/widgets/bar_chart.html')
def render_bar_chart_widget( bar_chart:barChartDataClass|None):

    default_bar_chart = barChartDataClass(
        title="درآمدها",
        chart_id ="vipa_charts_widget_1_chart",
        categories=["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور"],
        series= [
            barChartSeries(
                name="سود خالص",
                data=[44, 55, 57, 56, 61, 58],
            ),
            barChartSeries(
                name= "درآمد کل",
                data=[76, 85, 101, 98, 87, 105]
            )
            ]
    )

    bar_chart = bar_chart if bar_chart else default_bar_chart
    if bar_chart.chart_data_id is None:
        bar_chart.chart_data_id = bar_chart.chart_id + "_data"

    bar_chart_dict = bar_chart.__dict__.copy()
    bar_chart_dict["series"] = []
    for chart_series in bar_chart.series:
        bar_chart_dict["series"].append(chart_series.__dict__)

    context = {
        'bar_chart': bar_chart_dict,
    }
    return context



@register.inclusion_tag('templates_tags/widgets/line_chart.html')
def render_line_chart_widget(line_chart: lineChartDataClass | None = None):
    default_line_chart = lineChartDataClass(
        title="تماس‌ها",
        chart_id="line_chart_calls",
        categories=["9 AM", "12 PM", "15 PM", "18 PM", "19 PM", "21 PM"],
        series=[
            lineChartSeries(
                name="تماس‌های ورودی",
                data=[60, 50, 75, 50, 60, 60],
                color="#1b84ff"
            ),
            lineChartSeries(
                name="تماس‌های خروجی",
                data=[45, 52, 38, 45, 35, 85],
                color="#17c653"
            )
        ],
        height=300,
        gradient_colors=["#1b84ff", "#17c653"]
    )
    
    line_chart = line_chart if line_chart else default_line_chart
    
    if line_chart.chart_data_id is None:
        line_chart.chart_data_id = line_chart.chart_id + "_data"
    
    # تبدیل به دیکشنری
    chart_dict = line_chart.__dict__.copy()
    chart_dict["series"] = [
        {"name": s.name, "data": s.data, "color": s.color} 
        for s in line_chart.series
    ]
    
    context = {
        'line_chart': chart_dict,
    }
    return context


# templatetags/vipaChartWidgetTags.py

import json
import uuid

@register.inclusion_tag('templates_tags/widgets/pie_chart.html')
def pro_pie_chart(chart_data, chart_id=None):
    """
    تگ قالب برای نمایش پای چارت
    
    Usage:
        {% pro_pie_chart chart_data "my_chart" %}
    """
    # تولید ID یکتا
    if chart_id is None:
        chart_id = f'pie_chart_{uuid.uuid4().hex[:8]}'
    
    chart_data_id = f"{chart_id}_data"
    legend_id = f"{chart_id}_legend"  # اضافه شد
    
    # تبدیل داده‌ها به فرمت ApexCharts
    labels = [item['label'] for item in chart_data.get('data', [])]
    series = [item['value'] for item in chart_data.get('data', [])]
    
    # رنگ‌های پیش‌فرض
    default_colors = [
        '#009ef7', '#50cd89', '#f1416c', '#ffc700', 
        '#9012f4', '#00c9db', '#ffad2a', '#ff6b6b',
        '#4ecdc4', '#45b7d1', '#96ceb4', '#ffeaa7'
    ]
    
    payload = {
        'chart_id': chart_id,
        'legend_id': legend_id,  # اضافه شد
        'title': chart_data.get('title', ''),
        'description': chart_data.get('description', ''),
        'height': chart_data.get('height', '350px'),
        'series': series,
        'labels': labels,
        'colors': chart_data.get('colors', default_colors),
        'chart_data_id': chart_data_id
    }
    
    return {
        'pie_chart': payload,
        'chart_payload': payload
    }




# templatetags/vipaChartWidgetTags.py



# templatetags/vipaChartWidgetTags.py

import json
import uuid


@register.inclusion_tag('templates_tags/widgets/stat_card.html')
def pro_stat_card(card_data, card_id=None):
    """
    تگ قالب برای نمایش کارت آماری با نمودار
    """
    if card_id is None:
        card_id = f'stat_card_{uuid.uuid4().hex[:8]}'
    
    chart_id = f"{card_id}_chart"
    chart_data_id = f"{card_id}_chart_data"
    
    # دریافت داده‌های نمودار - پشتیبانی از chart_data و data
    chart_items = card_data.get('chart_data', card_data.get('data', []))
    
    # محاسبه مجموع
    total = sum(item.get('value', 0) for item in chart_items)
    
    # تبدیل داده‌ها به فرمت نمودار
    series = [item.get('value', 0) for item in chart_items]
    labels = [item.get('label', '') for item in chart_items]
    
    # رنگ‌های پیش‌فرض
    default_colors = ['#50cd89', '#009ef7', '#f1416c', '#ffc700', '#9012f4', '#00c9db']
    
    # استفاده از رنگ‌های ارائه شده یا پیش‌فرض
    if 'colors' in card_data:
        colors = card_data['colors']
    else:
        colors = []
        for item in chart_items:
            if 'color' in item:
                # تبدیل نام رنگ به hex
                color_map = {
                    'bg-success': '#50cd89',
                    'bg-primary': '#009ef7',
                    'bg-danger': '#f1416c',
                    'bg-warning': '#ffc700',
                    'bg-info': '#00c9db',
                    'bg-gray-300': '#e4e6ef',
                    'bg-gray-200': '#e9ecef',
                }
                colors.append(color_map.get(item['color'], item['color']))
            else:
                colors.append(default_colors[len(colors) % len(default_colors)])
    
    payload = {
        'chart_id': chart_id,
        'series': series,
        'labels': labels,
        'colors': colors,
        'size': card_data.get('size', 70),
        'line': card_data.get('line', 11),
        'chart_data_id': chart_data_id
    }
    
    return {
        'stat_card': {
            'card_id': card_id,
            'chart_id': chart_id,
            'chart_data_id': chart_data_id,
            'title': card_data.get('title', ''),
            'value': card_data.get('value', 0),
            'prefix': card_data.get('prefix', ''),
            'suffix': card_data.get('suffix', ''),
            'change': card_data.get('change', 0),
            'change_type': card_data.get('change_type', 'success'),
            'chart_data': chart_items,
            'total': total,
            'size': card_data.get('size', 70),
            'line': card_data.get('line', 11)
        },
        'chart_payload': payload
    }