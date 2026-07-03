from django import template
from django.db.models import Q
from django.contrib.auth.models import User

from authentication.models import Profile
from dashboard.models import Page
from SekeSepidar.settings import DEFAULT_PROFILE_PATH

register = template.Library()

@register.inclusion_tag('templates_tags/dashboard/user_top_menu.html')
def user_top_menu(user:User, image=None):  # Remove type hint Profile, use generic object
    """
    Generates a dictionary for the user's top menu, checking if the user is a Profile object.
    """
    name = 'Unknown User'
    role = 'Unknown'
    avatar = DEFAULT_PROFILE_PATH
    try:
        if isinstance(user.profile, Profile):
            if user.profile.first_name is None and user.profile.last_name is None:
                name = 'ناشناس'
            else:
                name =f'{user.profile.first_name}  {user.profile.last_name}'  # Access Profile attributes
            role = user.profile.role
            avatar = '/' + user.profile.avatar.name
            # avatar = user.profile.avatar.url
        elif isinstance(user, User):
            name = user.first_name + " " + user.last_name  # Access User attributes
            role = "User" # Or some default role
        else:
            pass
    except:
        pass
            
    return {'name': name, 'role': role, 'avatar':avatar}


@register.inclusion_tag('templates_tags/dashboard/theme_mode_menu.html')
def theme_mode_menu(active_theme=None):
    return {"theme":active_theme}


@register.inclusion_tag('templates_tags/dashboard/notif_top_menu.html')
def notif_top_menu(title:str, message:str):
    return {"title":title,
            "message":message}

@register.inclusion_tag('templates_tags/dashboard/side_menu_mobile.html')
def sidebar_mobile_menu():

    return {}


@register.inclusion_tag('templates_tags/dashboard/side_menu.html')
def sidebar_menu(curent_link:str, pages, pre_url:str, title=None, logo=None):
    
    if pages is None:
        pages = [
            {
                "name": "home",
                "label": "مقدار پیش فرض",
                "icon": """<i class="ki-duotone ki-element-11 fs-2">
                                <span class="path1"></span>
                                <span class="path2"></span>
                                <span class="path3"></span>
                                <span class="path4"></span>
                            </i>""",
                "type": "item",
                # "link": "#",
                "order" : 1,
            },
            {
                "name": "dataset",
                "label": "درختی نمونه",
                "icon": """<i class="ki-duotone ki-element-11 fs-2">
                                <span class="path1"></span>
                                <span class="path2"></span>
                                <span class="path3"></span>
                                <span class="path4"></span>
                            </i>""",
                "type": "tree",
                # "link": "#",
                "order" : 2,
                "subs": [
                    {
                        "name": "label",
                        "label": "زیر ۱",
                        "icon": """<i class="ki-duotone ki-element-11 fs-2">
                                        <span class="path1"></span>
                                        <span class="path2"></span>
                                        <span class="path3"></span>
                                        <span class="path4"></span>
                                    </i>""",
                        "type": "item",
                        # "link": "#",
                        "order" : 1,

                    }
                ]
            }
        ]
    if curent_link[-1] == "/":
        curent_link = curent_link[:-1]
    
    def generate_url(base_url, parent_name, item_name=None) ->str:
        if item_name:
            return f"{base_url}{parent_name}/{item_name}"
        return f"{base_url}{parent_name}"

    def process_pages(pages, pre_url, current_link):

        active_page = ""

        for page in pages:
            if not page.get('link'):
                page["link"] = generate_url(pre_url, page["name"])

            if curent_link.startswith(page["link"]):
                active_page = page["name"]

            for sub_page in page.get('subs', []):
                if not sub_page.get('link'):
                    sub_page['link'] = generate_url(pre_url, page["name"], sub_page["name"])
                
                if current_link.startswith( sub_page["link"]) :
                    active_page = sub_page["name"]

        return active_page
    
    active_page = process_pages(pages, pre_url, curent_link)


    return {"active_page":active_page,
            "pages":pages,
            "title":title,
            "pre_url":pre_url,
            "logo":logo
            }
