from django.shortcuts import render
from django.http import HttpResponse


def home(request):
    return render(request, 'core/home.html')

def about(request):
    return render(request, 'core/about.html', {'title': 'About'})

def contact_us(request):
    return render(request, 'core/contact_us.html', {'title': 'Contact Us'})

def legal_notice(request):
    return render(request, 'core/legal_notice.html', {'title': 'Legal Notice'})

def privacy_policy(request):
    return render(request, 'core/privacy_policy.html', {'title': 'Privacy Policy'})
