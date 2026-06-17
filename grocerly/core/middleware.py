class ForceDefaultLanguageMiddleware:
    """
    Ignore Accept-Language HTTP headers.
    This forces Django to use the default LANGUAGE_CODE ('vi')
    if the user hasn't explicitly set a language via cookie/session.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if 'HTTP_ACCEPT_LANGUAGE' in request.META:
            del request.META['HTTP_ACCEPT_LANGUAGE']
        return self.get_response(request)
