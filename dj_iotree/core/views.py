from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return HttpResponse('<h1>IoTree42 - Home</h1>')

def about(request):
    return HttpResponse('<h1>IoTree42 - About</h1>')

def contact_us(request):
    return HttpResponse('<h1>IoTree42 - Contact Us</h1>')

def impressum(request):
    return HttpResponse('<h1>IoTree42 - Impressum</h1>')

def datenschutz(request):
    return HttpResponse('<h1>IoTree42 - Impressum</h1>')
