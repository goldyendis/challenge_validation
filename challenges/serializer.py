import re
from pyproj import Transformer
from rest_framework import serializers
from .models import BH, BHSzakasz, Turamozgalom
from django.db import connections

class BHPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = BH
        fields = ['bh_nev','mtsz_id','bh_id','objectid','start_date','end_date','lat','lon']

class BHPointDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = BH
        fields = '__all__'


class BHSzakaszSerializer(serializers.ModelSerializer):
    shape = serializers.SerializerMethodField()
    class Meta:
        model = BHSzakasz
        fields = ["objectid","bhszakasz_id",
			"kezdopont", "vegpont",
			"start_date","end_date",
			"kezdopont_bh_id",
			"vegpont_bh_id","shape"]

    def get_shape(self, obj):
        query = """
            SELECT sde.ST_AsText(shape) 
            FROM kektura.bhszakasz 
            WHERE objectid = %s
        """
        with connections['bh'].cursor() as cursor:
            cursor.execute(query, [obj.objectid])
            result = cursor.fetchone()
        
        if result and result[0]:
            wkt = result[0]
            geojson = self.linestring_z_to_geojson(wkt)
            return geojson
        return None
    
    def linestring_z_to_geojson(self, wkt):
        transformer = Transformer.from_crs("EPSG:102100", "EPSG:4326", always_xy=True)  

        coord_text = re.search(r"LINESTRING Z \((.*)\)", wkt).group(1)
        coords = [
            list(transformer.transform(x, y)) + [z] 
            for x, y, z in (map(float, point.split()) for point in coord_text.split(", "))
        ]
        
        geojson = {
            "type": "LineString",
            "coordinates": coords
        }
        return geojson
class TuramozgalomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Turamozgalom
        fields = '__all__'




# class ChallengesSerializer(serializers.Serializer):
#     stamps = StampSerializer(many=True)
#     language = serializers.CharField(default="hu")
#     bookletWhichBlue = serializers.CharField()


class BHDSerializer(serializers.Serializer):
    bh = serializers.SerializerMethodField()
    stamp_type = serializers.CharField()
    stamping_date = serializers.SerializerMethodField()

    def get_stamping_date(self, obj):

        if obj.stamp_type == "digistamp":
            return obj.stamping_date.strftime("%Y-%m-%d %H:%M:%S")

        elif obj.stamp_type == "register":
            return obj.stamping_date.strftime("%Y-%m-%d") 

    
    def get_bh(self,obj):
        serializer = BHPointSerializer(obj.bh)
        return serializer.data
    

class BHSzDSerializer(serializers.Serializer):
    bh_szakasz = serializers.SerializerMethodField()
    stamp_type = serializers.SerializerMethodField()
    stamping_date = serializers.SerializerMethodField()

    def get_stamping_date(self, obj):
        if obj.stamp_type == "digistamp":
            return obj.stamping_date.strftime("%Y-%m-%d %H:%M:%S")

        elif obj.stamp_type == "register":
            return obj.stamping_date.strftime("%Y-%m-%d") 


    def get_stamp_type(self,obj):
        return obj.stamp_type.value

    def get_bh_szakasz(self,obj):
        serializer = BHSzakaszSerializer(obj.bh_szakasz)
        return serializer.data
    

