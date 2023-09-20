from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return HttpResponse('<h1>IoTree42 Home</h1>')

def about(request):
    return HttpResponse('<h1>IoTree42 About</h1>')
