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
