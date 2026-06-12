from django.shortcuts import redirect

class RestrictStaffMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if request.user.is_superuser or request.user.is_staff:
                path = request.path_info
                
                # Danh sách các tiền tố URL được phép truy cập
                allowed_prefixes = [
                    '/admin/', '/useradmin/', 
                    '/vi/admin/', '/vi/useradmin/', 
                    '/en/admin/', '/en/useradmin/',
                    '/user/sign-out/', '/vi/user/sign-out/', '/en/user/sign-out/',
                    '/media/', '/static/',
                ]
                
                # Nếu URL không bắt đầu bằng bất kỳ prefix nào trong danh sách
                if not any(path.startswith(prefix) for prefix in allowed_prefixes):
                    if request.user.is_superuser:
                        return redirect('/admin/')
                    else:
                        return redirect('useradmin:dashboard')
                        
        response = self.get_response(request)
        return response
