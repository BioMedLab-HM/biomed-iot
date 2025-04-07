from django.contrib.admin import AdminSite
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import render

class MyAdminSite(AdminSite):
    def login(self, request, extra_context=None):
        # If the user is not authenticated, redirect them to your regular login page.
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        # If they are authenticated but not a staff member, deny access.
        if not request.user.is_staff:
            # Render a custom error template or redirect to a custom page
            return render(request, 'core/not_found.html')
        # Otherwise, proceed with the default admin login process.
        return super().login(request, extra_context=extra_context)

# Instantiate your custom admin site.
admin_site = MyAdminSite(name='iot-admin')
