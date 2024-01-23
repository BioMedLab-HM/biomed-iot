from django import template
from django.urls import reverse, NoReverseMatch

register = template.Library()

@register.simple_tag(takes_context=True)
def is_active(context, *url_names):
    request = context['request']
    if not request:
        return ''
    for url_name in url_names:
        try:
            if request.path == reverse(url_name):
                return 'active'
        except NoReverseMatch:
            continue
    return ''

# @register.simple_tag(takes_context=True)
# def is_active(context, url_name):
#     request = context['request']
#     if not request:
#         return ''
#     try:
#         if request.path == reverse(url_name):
#             return 'active'
#     except NoReverseMatch:
#         pass
#     return ''


@register.simple_tag(takes_context=True)
def starts_with(context, prefix):
    request = context['request']
    if not request:
        return ''
    return 'active' if request.path.startswith('/' + prefix) else ''


# @register.simple_tag(takes_context=True)
# def starts_with(context, prefix):
#     request = context['request']
#     if not request:
#         return ''
#     # Using resolve() to get the current view name and check if it starts with the prefix
#     current_view_name = resolve(request.path_info).url_name
#     return 'active' if current_view_name and current_view_name.startswith(prefix) else ''