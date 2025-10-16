class PaymentSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if 'last_receipt_no' in request.session:
            del request.session['last_receipt_no']
        return response