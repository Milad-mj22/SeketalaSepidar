from django.shortcuts import render

# Create your views here.

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


# from .models import Tool

@login_required(login_url='authentication:sign-in')
def dashboard_page(request,):
 
    return redirect('')





