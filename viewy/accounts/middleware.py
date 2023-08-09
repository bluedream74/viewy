from urllib.parse import urlencode
from django.urls import reverse
from django.shortcuts import redirect

class AgeVerificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if '/poster/' in request.path and not request.COOKIES.get('is_over_18'):
            query_string = urlencode({'next': request.path})
            url = reverse('home') + '?' + query_string
            return redirect(url)

        response = self.get_response(request)
        return response