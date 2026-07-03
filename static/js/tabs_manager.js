function openTab(evt, tabName, widgetId) {
    var tabWidget = document.getElementById(widgetId);
    
    // ==================== تب‌های محتوا ====================
    // استفاده از > برای انتخاب فقط فرزندان مستقیم
    var tabContents = tabWidget.querySelectorAll(':scope > .tab-content');
    
    tabContents.forEach(function(content) {
        content.classList.remove('active');
    });
    
    // ==================== دکمه‌های تب ====================
    // فقط فرزندان مستقیم tab-buttons
    var tabBtnContainer = tabWidget.querySelector(':scope > .tab-buttons');
    
    if (tabBtnContainer) {
        var tabBtns = tabBtnContainer.querySelectorAll(':scope > .tab-btn');
        
        tabBtns.forEach(function(btn) {
            btn.classList.remove('active');
        });
    }
    
    // ==================== فعال کردن تب انتخابی ====================
    var btnElement = evt.currentTarget;
    btnElement.classList.add('active');
    
    var selectedContent = document.getElementById(tabName);
    if (selectedContent) {
        selectedContent.classList.add('active');
    }
}