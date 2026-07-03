from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required
def main_page(request,):
 

    context = {
        "active_page":"home"
    }
    return render(request, 
                  'main_page.html',
                  context
                  )


