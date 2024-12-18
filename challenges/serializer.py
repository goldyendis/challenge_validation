import re
from pyproj import Transformer
from rest_framework import serializers
from .models import BH, BHD, BHSzD, BHSzakasz, Turamozgalom
from django.db import connections
from decimal import Decimal, ROUND_HALF_UP


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

class BH_Dev_Serializer(serializers.Serializer):
    ver_id = serializers.SerializerMethodField()
    stamping_date = serializers.SerializerMethodField()

    def get_stamping_date(self,obj):
        return obj.stamping_date

    def get_ver_id(self,obj):
        return obj.bh.ver_id

class BHDSerializer(serializers.Serializer):
    bh = serializers.SerializerMethodField()
    stamp_type = serializers.CharField()
    stamping_date = serializers.SerializerMethodField()

    def get_stamping_date(self, obj):

        if obj.stamp_type in ["digistamp","register"]:
            return obj.stamping_date.strftime("%Y-%m-%d %H:%M:%S")

    def get_bh(self,obj):
        serializer = BHPointSerializer(obj.bh)
        return serializer.data


class BHSzakasz_Dev_Serializer(serializers.Serializer):
    ver_id = serializers.SerializerMethodField()
    stamping_date = serializers.SerializerMethodField()

    def get_stamping_date(self,obj):
        return obj.stamping_date

    def get_ver_id(self,obj):
        return obj.bh_szakasz.ver_id

class BHSzDSerializer(serializers.Serializer):
    bh_szakasz = serializers.SerializerMethodField()
    stamp_type = serializers.SerializerMethodField()
    stamping_date = serializers.SerializerMethodField()

    def get_stamping_date(self, obj):

        if obj.stamp_type.value in ["digistamp","register"]:
            return obj.stamping_date.strftime("%Y-%m-%d %H:%M:%S")


    def get_stamp_type(self,obj):
        return obj.stamp_type.value

    def get_bh_szakasz(self,obj):
        serializer = BHSzakaszSerializer(obj.bh_szakasz)
        return serializer.data
    

class GYKTSerializer(serializers.Serializer):
    name = serializers.CharField()
    completed = serializers.SerializerMethodField()
    length = serializers.DecimalField(max_digits=12, decimal_places=8)

    def get_completed(self, obj):
        if obj['name'] == 'mozgalom':
            return obj['length'] >= 300
        return obj['length'] >= 50

class StatisticSerializer(serializers.Serializer):
    mozgalom_completed = serializers.BooleanField()
    all_length = serializers.SerializerMethodField()
    completed_length = serializers.SerializerMethodField()
    length_percentage = serializers.SerializerMethodField()
    remaining_length = serializers.SerializerMethodField()
    completed_elevation = serializers.IntegerField()
    all_elevation = serializers.IntegerField()
    elevation_percentage = serializers.SerializerMethodField()
    completed_stamps = serializers.IntegerField()
    remaining_stamps = serializers.IntegerField()
    completed_main_sections = serializers.IntegerField()
    all_main_sections = serializers.IntegerField()
    average_speed = serializers.SerializerMethodField()
    time_on_blue = serializers.DictField()
    since_first_stamp_time_diff = serializers.DictField()
    excepted_completion = serializers.DictField()
    gykt_tajegyseg_data = serializers.SerializerMethodField()

    def _round_decimal(self, value):
        return float(Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

    def get_all_length(self, obj):
        return self._round_decimal(obj.all_length)

    def get_completed_length(self, obj):
        return self._round_decimal(obj.completed_length)

    def get_length_percentage(self, obj):
        return self._round_decimal(obj.length_percentage)

    def get_remaining_length(self, obj):
        return self._round_decimal(obj.remaining_length)

    def get_elevation_percentage(self, obj):
        return self._round_decimal(obj.elevation_percentage)

    def get_average_speed(self, obj):
        return self._round_decimal(obj.average_speed)
    
    def get_gykt_tajegyseg_data(self, obj):
        # Assuming `gykt_data` contains the raw data for serialization
        raw_data = obj.gykt_tajegyseg_data  # This should be a dictionary
        serializer = GYKTSerializer([
            {'name': key, 'length': value} for key, value in raw_data.items()
        ], many=True)
        return serializer.data