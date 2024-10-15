from datetime import datetime
from django.db import models
from django.db.models import Q
from rest_framework import exceptions
from challenges.enums import StampType

class BHSzakaszObject:
    def __init__(self, bhsz_id, times) -> None:
        self.bhsz_id = bhsz_id
        self.stamp_times:tuple=times


    
        

class BH(models.Model):
    objectid = models.AutoField(primary_key=True)
    sorszam = models.SmallIntegerField(null=True, blank=True)
    mtsz_id = models.CharField(max_length=30, null=True, blank=True)
    bh_id = models.CharField(max_length=30, null=True, blank=True)
    bh_nev = models.CharField(max_length=120, null=True, blank=True)
    helyszin = models.CharField(max_length=100, null=True, blank=True)
    helyszin_leiras = models.CharField(max_length=255, null=True, blank=True)
    cim = models.CharField(max_length=50, null=True, blank=True)
    elerhetoseg = models.CharField(max_length=40, null=True, blank=True)
    nyitvatartas = models.CharField(max_length=255, null=True, blank=True)
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lon = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lenyomat = models.CharField(max_length=100, null=True, blank=True)
    url_lenyomat = models.CharField(max_length=150, null=True, blank=True)
    url_kep_1 = models.CharField(max_length=150, null=True, blank=True)
    url_kep_2 = models.CharField(max_length=150, null=True, blank=True)
    url_kep_3 = models.CharField(max_length=150, null=True, blank=True)
    url_kep_4 = models.CharField(max_length=150, null=True, blank=True)
    url_kep_5 = models.CharField(max_length=150, null=True, blank=True)
    helyszin_eng = models.CharField(max_length=100, null=True, blank=True)
    helyszin_leiras_eng = models.CharField(max_length=255, null=True, blank=True)
    elerhetoseg_eng = models.CharField(max_length=40, null=True, blank=True)
    nyitvatartas_eng = models.CharField(max_length=255, null=True, blank=True)

    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    created_date = models.DateTimeField(null=True, blank=True)
    last_edited_date = models.DateTimeField(null=True, blank=True)

    created_user = models.CharField(max_length=255, null=True, blank=True)
    last_edited_user = models.CharField(max_length=255, null=True, blank=True)
    shape = models.TextField(null=True, blank=True)  

    class Meta:
        db_table = 'bhpont'
        managed = False  

    @staticmethod
    def create_BH_from_request(json_stamp:dict,timestamp: datetime):
        '''
        With the POST request data, get the BH from the DB.
        Database versioning start from 2000-01-01, so converting lower date up to that'''
        if timestamp < datetime(2000, 1, 1):
            timestamp = datetime(2000, 1, 1)
        try:
            bh:BH = BH.objects.get(
                Q(mtsz_id=json_stamp.get('stampPointId')),
                Q(start_date__lte=timestamp),
                Q(end_date__gte=timestamp) | Q(end_date__isnull=True)
            )
            return bh
        except BH.DoesNotExist:
            raise exceptions.ValidationError(f"No BHPoint found for mtsz_id {json_stamp.get('stampPointId')} at {timestamp}")
    def __str__(self):
        return f"{self.objectid}: {self.bh_nev} s_date:{self.start_date}, e_date: {self.end_date}, {self.mtsz_id}, {self.bh_id}"

class BHSzakasz(models.Model):
    objectid = models.AutoField(primary_key=True)
    sorszam = models.SmallIntegerField(null=True, blank=True)
    nagyszakasz_id = models.CharField(max_length=30, null=True, blank=True)
    bhszakasz_id = models.CharField(max_length=30, null=True, blank=True)
    kezdopont = models.CharField(max_length=60, null=True, blank=True)
    vegpont = models.CharField(max_length=60, null=True, blank=True)
    szakasznev = models.CharField(max_length=120, null=True, blank=True)
    tav = models.DecimalField(max_digits=12, decimal_places=8, null=True, blank=True)
    szintemelkedes = models.SmallIntegerField(null=True, blank=True)
    szintcsokkenes = models.SmallIntegerField(null=True, blank=True)
    szintido_oda = models.CharField(max_length=15, null=True, blank=True)
    szintido_vissza = models.CharField(max_length=15, null=True, blank=True)
    gykt_tajegyseg = models.CharField(max_length=60, null=True, blank=True)
    okk_mozgalom = models.CharField(max_length=10, null=True, blank=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    created_date = models.DateTimeField(null=True, blank=True)
    last_edited_date = models.DateTimeField(null=True, blank=True)
    created_user = models.CharField(max_length=255, null=True, blank=True)
    last_edited_user = models.CharField(max_length=255, null=True, blank=True)
    kezdopont_bh_id = models.CharField(max_length=10, null=True, blank=True)
    vegpont_bh_id = models.CharField(max_length=10, null=True, blank=True)
    shape = models.TextField(null=True, blank=True)  


    class Meta:
        db_table = 'bhszakasz'
        managed = False  

    def __str__(self):
        return f"{self.objectid}: {self.bhszakasz_id}, {self.szakasznev},{self.kezdopont_bh_id},{self.vegpont_bh_id} at s_date:{self.start_date}, e_date: {self.end_date}"
    

class Turamozgalom(models.Model):
    objectid = models.AutoField(primary_key=True)
    okk_mozgalom = models.CharField(max_length=10, null=True, blank=True)
    nev = models.CharField(max_length=100, null=True, blank=True)
    tav = models.DecimalField(max_digits=12, decimal_places=8, null=True, blank=True)
    szintemelkedes = models.SmallIntegerField(null=True, blank=True)
    szintcsokkenes = models.SmallIntegerField(null=True, blank=True)
    szintido_oda = models.CharField(max_length=15, null=True, blank=True)
    szintido_vissza = models.CharField(max_length=15, null=True, blank=True)
    gpx_line_url = models.CharField(max_length=150, null=True, blank=True)
    gpx_line_bh_url = models.CharField(max_length=150, null=True, blank=True)
    gpx_bh_url = models.CharField(max_length=150, null=True, blank=True)
    gpx_bhlist_url = models.CharField(max_length=150, null=True, blank=True)
    gpx_bhlist_en_url = models.CharField(max_length=150, null=True, blank=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    created_user = models.CharField(max_length=255, null=True, blank=True)
    created_date = models.DateTimeField(null=True, blank=True)
    last_edited_user = models.CharField(max_length=255, null=True, blank=True)
    last_edited_date = models.DateTimeField(null=True, blank=True)
    shape = models.TextField(null=True, blank=True)  
    kezdopont = models.CharField(max_length=60, null=True, blank=True)
    vegpont = models.CharField(max_length=60, null=True, blank=True)


    class Meta:
        db_table = 'turamozgalom'
        managed = False  

    def __str__(self):
        return self.nev
    

class BHD:
    '''Extending BH with properties and methods to validate Stamps'''
    def __init__(self,bh:BH, timestamp:datetime,stamp_type:StampType) -> None:
        self.bh:BH = bh
        self.stamping_date:datetime = timestamp
        self.stamp_type:StampType = stamp_type
        self.neighbour_prev =None
        self.neighbour_next  =None

    @staticmethod
    def create_bhd_from_bh(bh:BH,timestamp: datetime, stamp_type: StampType):
        '''DB BH model, with other request data converting into BHD'''
        time = timestamp if stamp_type == "digistamp" else timestamp.replace(hour=0,minute=0,second=0,microsecond=0)
        bhd = BHD(
            bh=bh,
            timestamp=time,
            stamp_type=stamp_type
        )
        return bhd

    def __repr__(self) -> str:
        return (f"BHD with ID:{self.bh.bh_id}, MTSZ_ID: {self.bh.mtsz_id}, NEV: {self.bh.bh_nev}, Time: {self.stamping_date}, Type: {self.stamp_type},  NEXT:{self.neighbour_next}, PREV: {self.neighbour_prev}")

# class DigitBH(BHD):
#     def __init__(self, bh_id: str, timestamp: datetime, type:str = "Digit") -> None:
#         super().__init__(bh_id, timestamp)
#         self.type = type

#     def __repr__(self) -> str:
#         timestamp_str = self.stamping_date.strftime('%Y-%m-%d %H:%M:%S') if isinstance(self.stamping_date, datetime) else self.stamping_date.strftime('%Y-%m-%d')
#         return (f"BH with ID:{self.bh_id}, Time: {timestamp_str}, "
#                 # f"Left:{self.left_track_link}, Left_Date: {self.left_track_link_date}, "
#                 f"Right: {self.right_track_link}, Type: {self.type}")

# class KeziBH(BHD):
#     def __init__(self, bh_id: str, timestamp: datetime, type:str = "Kezi") -> None:
#         super().__init__(bh_id, timestamp)
#         self.type = type

#     def __repr__(self) -> str:
#         timestamp_str = self.stamping_date.strftime('%Y-%m-%d %H:%M:%S') if isinstance(self.stamping_date, datetime) else self.stamping_date.strftime('%Y-%m-%d')
#         return (f"BH with ID:{self.bh_id}, Time: {timestamp_str}, "
#                 # f"Left:{self.left_track_link}, Left_Date: {self.left_track_link_date}, "
#                 f"Right: {self.right_track_link}, Type: {self.type}")
