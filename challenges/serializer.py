from datetime import datetime
from rest_framework import serializers
from .models import BH, BHSzakasz, Turamozgalom

class BHPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = BH
        fields = ['bh_nev','mtsz_id','bh_id','objectid','start_date','end_date']

class BHPointDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = BH
        fields = '__all__'


class BHSzakaszSerializer(serializers.ModelSerializer):
    class Meta:
        model = BHSzakasz
        fields = ["objectid","sorszam","nagyszakasz_id","bhszakasz_id",
			"kezdopont", "vegpont","szakasznev","tav","szintemelkedes",
			"szintcsokkenes","szintido_oda","szintido_vissza","gykt_tajegyseg",
			"okk_mozgalom","start_date","end_date",
			"kezdopont_bh_id",
			"vegpont_bh_id"]


class TuramozgalomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Turamozgalom
        fields = '__all__'



class StampSerializer(serializers.Serializer):
    stampPointId = serializers.CharField()
    fulfillmentType = serializers.CharField()
    fulfillmentDate = serializers.IntegerField()

class ChallengesSerializer(serializers.Serializer):
    stamps = StampSerializer(many=True)
    language = serializers.CharField(default="hu")
    bookletWhichBlue = serializers.CharField()


class BHDSerializer(serializers.Serializer):
    bh = serializers.SerializerMethodField()
    stamp_type = serializers.CharField()
    stamping_date = serializers.SerializerMethodField()

    def get_stamping_date(self, obj):
        if hasattr(obj, 'stampType') and obj.stampType == "digistamp":
            if isinstance(obj.stamping_date, datetime):
                return obj.stamping_date.strftime("%Y-%m-%d %H:%M:%S")
            return obj.stamping_date

        elif hasattr(obj, 'stampType') and obj.stampType == "register":
            if isinstance(obj.stamping_date, datetime):
                return obj.stamping_date.date() 
            return obj.stamping_date

        return obj.stamping_date
    
    def get_bh(self,obj):
        serializer = BHPointSerializer(obj.bh)
        return serializer.data