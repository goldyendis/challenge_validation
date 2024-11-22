from datetime import datetime
from typing import List
from django.http import JsonResponse
from django.shortcuts import render
from requests import Response
from rest_framework.views import APIView
from challenges.challenge_validation import ChallengeValidation
from challenges.models import BH
from challenges.serializer import BH_Dev_Serializer, BHDSerializer, BHSzDSerializer, BHSzakasz_Dev_Serializer,  StatisticSerializer
from router.exceptions import UnauthorizedException
from router.views import verify_api_key
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework import status



class Challenges(APIView):
    renderer_classes = [JSONRenderer]

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
        challenge = ChallengeValidation(request, testing=False)
        bh_serializer = BH_Dev_Serializer(challenge.BHD_list,many=True)
        bhszakasz_serializer = BHSzakasz_Dev_Serializer(challenge.validated_bhszd, many=True)
        statistic_serializer = StatisticSerializer(challenge.statistics.statistic_data)
        return Response({
            'status': 'success',
            'bh': bh_serializer.data,
            'bhszakasz': bhszakasz_serializer.data,
            'statistics': statistic_serializer.data

        }, status=status.HTTP_200_OK)
    


class Testing(APIView):
    renderer_classes = [JSONRenderer]

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
        challenge = ChallengeValidation(request, testing=True)
        bhd_serializer = BHDSerializer(challenge.BHD_list,many=True)
        bhszd_serializer = BHSzDSerializer(challenge.validated_bhszd, many=True)
        statistic_serializer = StatisticSerializer(challenge.statistics.statistic_data)

        return Response({
            'status': 'success',
            'mozgalom':challenge.mozgalom,
            'mozgalom_kezdoBH': challenge.kezdopont,
            'mozgalom_vegpontBH': challenge.vegpont,
            'valid_bhszd': bhszd_serializer.data,
            'sorted_BHD': bhd_serializer.data,
            'image':challenge.nodeGraph.bhszd_graph_image if challenge.nodeGraph.bhszd_graph_image is not None else "",
            'image_mozgalom':challenge.nodeGraph.validated_graph_image if challenge.nodeGraph.validated_graph_image is not None else "",
            'statistics': statistic_serializer.data

        }, status=status.HTTP_200_OK)
    

    