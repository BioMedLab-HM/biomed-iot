from django.shortcuts import render


def home(request):
	context = {}

	page_title = 'Home'
	context = {'title': page_title, 'thin_navbar': False}
	return render(request, 'core/home.html', context)


def about(request):
	context = {}

	page_title = 'About'
	context = {'title': page_title, 'thin_navbar': False}
	return render(request, 'core/about.html', context)


def contact_us(request):
	context = {}

	page_title = 'Contact Us'
	context = {'title': page_title, 'thin_navbar': False}
	return render(request, 'core/contact_us.html', context)


def legal_notice(request):
	context = {}

	page_title = 'Legal Notice'
	context = {'title': page_title, 'thin_navbar': False}
	return render(request, 'core/legal_notice.html', context)


def privacy_policy(request):
	context = {}

	page_title = 'Privacy Policy'
	context = {'title': page_title, 'thin_navbar': False}
	return render(request, 'core/privacy_policy.html', context)


def manual(request):
	context = {}

	page_title = 'FAQ and Manual'
	context = {'title': page_title, 'thin_navbar': False}
	return render(request, 'core/manual.html', context)
