# core/middleware.py
from django.shortcuts import redirect
from django.conf import settings
from django.urls import resolve

EXCLUDED_PATHS = [
    '/login/',
    '/logout/',
    '/signup/',
    '/admin/',
    '/static/',     # αγνόηση static files
]

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Αγνόησε URLs που δεν χρειάζονται auth
        if any(path.startswith(p) for p in EXCLUDED_PATHS):
            return self.get_response(request)

        # Αν ο χρήστης δεν είναι authenticated → redirect στο login
        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)

        # Διαφορετικά συνέχισε κανονικά
        response = self.get_response(request)
        return response
