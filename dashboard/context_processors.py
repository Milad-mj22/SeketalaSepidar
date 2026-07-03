

from dashboard.models import BaseSettings, Page


def menu_items_processor(request):
    
    pages =  None
    try:
        user = request.user
        if not user.is_authenticated:
            pass
        else:
            pages =    Page.get_page_list()    
    except:
        print('Error in menu_items_processor')

    active_page = ''
    try:
        active_page = request.path.split('/')[-1]
        if active_page == '':
            active_page = request.path.split('/')[-2]
            
    except:
        pass

    logo = BaseSettings.get_settings().sidebar_logo
    sidebar_title = BaseSettings.get_settings().sidebar_title

    if logo:
        try:
            _ = logo.url
        except Exception:
            logo = None

    return {'pages':pages,'active_page':active_page,'pre_url':'/','logo':logo,'sidebar_title':sidebar_title}
