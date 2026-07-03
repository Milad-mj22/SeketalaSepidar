// static/js/widgets/line_chart.js

/**
 * رندر نمودار خطی
 * @param {string} chartId - آیدی المنت نمودار
 * @param {Object} config - تنظیمات نمودار
 * @param {string} config.title - عنوان
 * @param {Array} config.categories - دسته‌بندی‌ها
 * @param {Array} config.series - سری‌های داده
 * @param {number} config.height - ارتفاع
 * @param {Array} config.colors - رنگ‌ها
 */
function renderLineChart(chartId, config) {
    const chartElement = document.querySelector(`#${chartId}`);
    if (!chartElement) {
        console.error(`Chart element #${chartId} not found`);
        return null;
    }
    
    // مقادیر پیش‌فرض
    const defaultConfig = {
        height: 300,
        strokeCurve: 'smooth',
        showLegend: true,
        gradientColors: ['#1b84ff', '#17c653']
    };
    
    config = { ...defaultConfig, ...config };
    
    var options = {
        series: config.series || [],
        chart: {
            height: config.height,
            type: 'area',
            fontFamily: 'inherit',
            toolbar: { show: false },
            zoom: { enabled: false },
            animations: {
                enabled: true,
                easing: 'easeinout',
                speed: 800
            }
        },
        dataLabels: { enabled: false },
        stroke: {
            curve: config.strokeCurve || 'smooth',
            width: 3
        },
        xaxis: {
            categories: config.categories || [],
            axisBorder: { show: false },
            axisTicks: { show: false },
            labels: {
                style: {
                    colors: '#99a1b7',
                    fontSize: '12px'
                }
            }
        },
        yaxis: {
            labels: {
                style: {
                    colors: '#99a1b7',
                    fontSize: '12px'
                }
            }
        },
        colors: config.gradientColors || ['#1b84ff'],
        fill: {
            type: 'gradient',
            gradient: {
                shadeIntensity: 1,
                opacityFrom: 0.4,
                opacityTo: 0.1,
                stops: [0, 90, 100]
            }
        },
        grid: {
            borderColor: '#dbdfe9',
            strokeDashArray: 4,
            yaxis: { lines: { show: true } }
        },
        legend: {
            show: config.showLegend !== false,
            position: 'top',
            horizontalAlign: 'right',
            floating: true,
            offsetY: 0,
            offsetX: 0,
            height: 400,
            markers: {
                size: 8
            },
            labels: {
                colors: '#99a1b7'
            },
            itemMargin: {
                horizontal: 0,
                vertical: 0  // ← فاصله عمودی
            }
        },
        tooltip: {
            theme: 'light',
            y: { formatter: function (val) { return val; } }
        }
    };
    
    var chart = new ApexCharts(chartElement, options);
    chart.render();
    
    return chart;
}

/**
 * آپدیت نمودار با داده‌های جدید
 * @param {Object} chart - instance نمودار
 * @param {Object} newData - داده‌های جدید
 */
function updateLineChart(chart, newData) {
    if (!chart) return;
    
    if (newData.series) {
        chart.updateSeries(newData.series);
    }
    
    if (newData.categories) {
        chart.updateOptions({
            xaxis: { categories: newData.categories }
        });
    }
}




/**
 * اتصال به SSE و آپدیت نمودار
 * @param {string} sseUrl - آدرس SSE
 * @param {Object} chartInstance - instance نمودار
 * @param {Function} onUpdate - callback برای پردازش داده‌ها (اختیاری)
 */
function initLineChartSSE(sseUrl, chartInstance, onUpdate = null) {
    const eventSource = registerSSE(
        new EventSource(sseUrl)
    );
    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        // اگر callback داده شده، ابتدا داده‌ها را پردازش کن
        if (onUpdate) {
            const processedData = onUpdate(data);
            if (processedData) {
                updateLineChart(chartInstance, processedData);
            }
        } else {
            // استفاده مستقیم
            updateLineChart(chartInstance, data);
        }
    };
    
    eventSource.onerror = function(e) {
        console.log('SSE connection closed');
        eventSource.close();
    };
    
    return eventSource;
}




/**
 * اتصال SSE برای چندین نمودار
 * @param {string} sseUrl - آدرس SSE
 * @param {Array} charts - آرایه‌ای از تنظیمات نمودارها
 * @param {string} categoriesKey - کلید دسته‌بندی در داده‌های SSE (پیش‌فرض: 'categories')
 */
function initMultiChartsSSE(sseUrl, charts) {
    const eventSource = registerSSE(
        new EventSource(sseUrl)
    );
    eventSource.onmessage = function(event) {
        if (!event.data) return;
        const data = JSON.parse(event.data);
        if ( typeof(data) === 'object' && Object.keys(data).length === 0) return;
        
        // آپدیت همه نمودارها
        charts.forEach(chartConfig => {
            updateLineChart(chartConfig.instance, {
                series: data[chartConfig.seriesKey]['series'],
                categories: data[chartConfig.seriesKey]['categories']
            });
        });
    };
    
    eventSource.onerror = function(e) {
        console.log('SSE connection closed');
        eventSource.close();
    };
    
    return eventSource;
}