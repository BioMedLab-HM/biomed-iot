from django import template
from django.urls import reverse, NoReverseMatch

"""
This Django template code defines custom template tags to help manage navigation menus 
by highlighting the active link. These tags are used in templates to add an "active" class 
to a navigation item if the current request's path matches certain criteria.
"""

# Create a Django template library instance to register custom template tags
register = template.Library()


# Define custom template tag 'is_active'
@register.simple_tag(takes_context=True)
def is_active(context, *url_names):
	request = context['request']
	if not request:
		return ''
	# Iterate through provided URL names to check if any match the current path
	for url_name in url_names:
		try:
			# Use Django's 'reverse' function to get the URL path from its name
			if request.path == reverse(url_name):
				return 'active'
		except NoReverseMatch:
			continue
	return ''


# Define custom template tag 'starts_with'
@register.simple_tag(takes_context=True)
def starts_with(context, prefix):
	# Extract the request object from the template context
	request = context['request']
	if not request:
		return ''
	return 'active' if request.path.startswith('/' + prefix) else ''
