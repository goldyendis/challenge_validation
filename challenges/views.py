from typing import List
from django.shortcuts import render
from requests import Response
from rest_framework.views import APIView
from challenges.challenge_validation import ChallengeValidation
from challenges.models import BH
from challenges.serializer import BHDSerializer, BHSzDSerializer, BHSzakaszSerializer
from router.exceptions import UnauthorizedException
from router.views import verify_api_key
from rest_framework.renderers import JSONRenderer,BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework import status


class Challenges(APIView):
    # renderer_classes = [JSONRenderer]
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]

    def handle_exception(self, exc):
        language = self.request.data.get("language", "hu")
        if isinstance(exc, UnauthorizedException):
            return Response({'status': 'service_error', 'message': exc.message}, status=401)
        return super().handle_exception(exc)
    

    def get(self, request, *args, **kwargs):
        stamps = BH.objects.all().order_by('-mtsz_id')
        
        return render(request, 'challenges/stamp_form.html', {'stamps': stamps})

    def post(self, request, *args, **kwargs):
        verify_api_key(request.headers.get('X-API-KEY'), request.data.get("language","hu"))

        challenge = ChallengeValidation(request)
        bhd_serializer = BHDSerializer(challenge.BHD_list,many=True)
        bhszd_serializer = BHSzDSerializer(challenge.validated_bhszd, many=True)

        return Response({
            'status': 'success',
            'mozgalom':challenge.mozgalom,
            'mozgalom_kezdoBH': challenge.kezdopont,
            'mozgalom_vegpontBH': challenge.vegpont,
            'valid_bhszd': bhszd_serializer.data,
            'sorted_BHD': bhd_serializer.data,
        }, status=status.HTTP_200_OK)
    