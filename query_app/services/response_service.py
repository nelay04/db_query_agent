from rest_framework.response import Response

class ResponseService:
    @staticmethod
    def success(message='Success', code=200, data=None):
        return Response({
            'success': True,
            'message': message,
            'data': data or {}
        }, status=code)

    @staticmethod
    def error(message='Something went wrong', code=400, errors=None):
        return Response({
            'success': False,
            'message': message,
            'errors': errors or {}
        }, status=code)
