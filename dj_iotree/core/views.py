from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return render(request, 'core/home.html')

def about(request):
    return render(request, 'core/about.html')

def contact_us(request):
    return render(request, 'core/contact_us.html')

def impressum(request):
    return render(request, 'core/impressum.html')

def datenschutz(request):
    return render(request, 'core/datenschutz.html')
