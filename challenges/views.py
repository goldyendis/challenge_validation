from typing import List
from requests import Response
from rest_framework.views import APIView
from challenges.challenge_validation import ChallengeValidation
from challenges.serializer import BHDSerializer, BHSzDSerializer, BHSzakaszSerializer
from router.exceptions import UnauthorizedException
from router.views import verify_api_key
from rest_framework.renderers import JSONRenderer,BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework import status


class Challenges(APIView):
    # renderer_classes = [JSONRenderer]
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]

    # def handle_exception(self, exc):
    #     language = self.request.data.get("language", "hu")
    #     if isinstance(exc, UnauthorizedException):
    #         return Response({'status': 'service_error', 'message': exc.message}, status=401)
    #     return super().handle_exception(exc)
    

    def get(self, request, *args, **kwargs):
        example_request = {
            "stamps":[
                {
                    "stampPointId":"OKTPH_132",
                    "fulfillmentType":"digistamp",
                    "fulfillmentDate":1686139828
                },
                {
                    "stampPointId":"OKTPH_132_B_1",
                    "fulfillmentType":"digistamp",
                    "fulfillmentDate":1686154228
                },
                {
                    "stampPointId":"OKTPH_133",
                    "fulfillmentType":"digistamp",
                    "fulfillmentDate":1686168628
                },
                 {
                    "stampPointId":"OKTPH_133",
                    "fulfillmentType":"register",
                    "fulfillmentDate":1686168628
                }
            ],
            "language":"hu",
            "bookletWhichBlue":"OKT"
            }
        return Response({
            "message": "Use this structure to make a POST request",
            "example_request": example_request
        })

    def post(self, request, *args, **kwargs):
        # verify_api_key(request.headers.get('X-API-KEY'), request.data.get("language","hu"))

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
    