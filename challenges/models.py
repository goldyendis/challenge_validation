from datetime import datetime
from typing import List
from django.db import models
from django.db.models import Q
from rest_framework import exceptions
from challenges.enums import BookletTypes, DirectionType, StampType


class BHDList(list):
    def get_min_stamping_date(self):
        """Return the minimum stamping_date from the list of BHD objects"""
        if not self:
            return None  # If the list is empty, return None
        return min(bhd.stamping_date for bhd in self)

    def get_max_stamping_date(self):
        """Return the maximum stamping_date from the list of BHD objects"""
        if not self:
            return None  # If the list is empty, return None
        return max(bhd.stamping_date for bhd in self)  




class BH(models.Model):
    objectid = models.AutoField(primary_key=True)
    sorszam = models.SmallIntegerField(null=True, blank=True)
    ver_id = models.IntegerField(null=True, blank=False)
    mtsz_id = models.CharField(max_length=30, null=True, blank=True)
    bh_id = models.CharField(max_length=30, null=True, blank=True)
    bh_nev = models.CharField(max_length=120, null=True, blank=True)
    helyszin = models.CharField(max_length=100, null=True, blank=True)
    # helyszin_leiras = models.CharField(max_length=255, null=True, blank=True)
    # cim = models.CharField(max_length=50, null=True, blank=True)
    # elerhetoseg = models.CharField(max_length=40, null=True, blank=True)
    # nyitvatartas = models.CharField(max_length=255, null=True, blank=True)
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lon = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    # lenyomat = models.CharField(max_length=100, null=True, blank=True)
    # url_lenyomat = models.CharField(max_length=150, null=True, blank=True)
    # url_kep_1 = models.CharField(max_length=150, null=True, blank=True)
    # url_kep_2 = models.CharField(max_length=150, null=True, blank=True)
    # url_kep_3 = models.CharField(max_length=150, null=True, blank=True)
    # url_kep_4 = models.CharField(max_length=150, null=True, blank=True)
    # url_kep_5 = models.CharField(max_length=150, null=True, blank=True)
    # helyszin_eng = models.CharField(max_length=100, null=True, blank=True)
    # helyszin_leiras_eng = models.CharField(max_length=255, null=True, blank=True)
    # elerhetoseg_eng = models.CharField(max_length=40, null=True, blank=True)
    # nyitvatartas_eng = models.CharField(max_length=255, null=True, blank=True)

    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    # created_date = models.DateTimeField(null=True, blank=True)
    # last_edited_date = models.DateTimeField(null=True, blank=True)

    # created_user = models.CharField(max_length=255, null=True, blank=True)
    # last_edited_user = models.CharField(max_length=255, null=True, blank=True)
    # shape = models.TextField(null=True, blank=True)  

    class Meta:
        db_table = 'bhpont'
        managed = False  

    @staticmethod
    def get_mozgalom_start_end_BH(bhd_list:BHDList, mozgalom:BookletTypes)-> str:
        min_date:datetime = bhd_list.get_min_stamping_date()
        max_date:datetime = bhd_list.get_max_stamping_date()
        kezdopont = None
        vegpont = None
        turamozgalom_db = Turamozgalom()
        turamozgalom_versions = turamozgalom_db.get_mozgalmak_versions_in_interval(min_date, max_date, mozgalom)
        distinct_kezdopont = set()
        distinct_vegpont = set()

        for row in turamozgalom_versions:
            distinct_kezdopont.add(row.kezdopont)
            distinct_vegpont.add(row.vegpont)

        distinct_kezdopont = list(distinct_kezdopont)
        distinct_vegpont = list(distinct_vegpont)
        
        if len(distinct_kezdopont)==1:
            kezdopont:str = distinct_kezdopont[0]
        if len(distinct_vegpont)==1:
            vegpont:str = distinct_vegpont[0]

        return kezdopont, vegpont
    @staticmethod
    def get_actual_BH_from_bh_id(bh_id:str):
        return BH.objects.filter(
            Q(bh_id=bh_id) & Q(end_date__isnull=True)
        ).first()

    @staticmethod
    def create_BH_from_request(json_stamp:dict,bh_cache:dict,timestamp: datetime):
        '''
        With the POST request data, get the BH from the DB.
        Database versioning starts from 2000-01-01, so converting lower date up to that'''
        if timestamp < datetime(2000, 1, 1):
            timestamp = datetime(2000, 1, 1)

        bh_match = next(
        (
            bh for bh in bh_cache
            if bh['mtsz_id'] == json_stamp.get('stampPointId')
            and bh['start_date'] <= timestamp
            and (bh['end_date'] is None or bh['end_date'] >= timestamp)
        ),
        None
    )

        if bh_match:
            return BH(**bh_match)  # Rehydrate the BH object from the cache data

        else:
            try:
                bh:BH = BH.objects.get(
                    Q(mtsz_id=json_stamp.get('stampPointId')),
                    Q(start_date__lte=timestamp),
                    Q(end_date__gte=timestamp) | Q(end_date__isnull=True)
                )
                return bh
            except BH.DoesNotExist:
                print(exceptions.ValidationError(f"No BHPoint found for mtsz_id {json_stamp.get('stampPointId')} at {timestamp}"))
    
    def __str__(self):
        return f"{self.objectid}: {self.ver_id} {self.bh_nev} s_date:{self.start_date}, e_date: {self.end_date}, {self.mtsz_id}, {self.bh_id}"


class NagySzakasz(models.Model):
    objectid = models.AutoField(primary_key=True)
    sorszam = models.SmallIntegerField(null=True, blank=True)
    nagyszakasz_id = models.CharField(max_length=30, null=True, blank=True)
    kezdopont = models.CharField(max_length=60, null=True, blank=True)
    kezdopont_bh_id = models.CharField(max_length=10, null=True, blank=True)
    vegpont = models.CharField(max_length=60, null=True, blank=True)
    vegpont_bh_id = models.CharField(max_length=10, null=True, blank=True)
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
    shape = models.TextField(null=True, blank=True)  
    class Meta:
        db_table = 'nagyszakasz'
        managed = False  

    def __repr__(self):
        return f"{self.nagyszakasz_id}, {self.kezdopont}, {self.vegpont}, {self.start_date}, {self.end_date}"


class BHSzakasz(models.Model):
    objectid = models.AutoField(primary_key=True)
    sorszam = models.SmallIntegerField(null=True, blank=True)
    ver_id = models.IntegerField(null=True, blank=False)
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
    # created_date = models.DateTimeField(null=True, blank=True)
    # last_edited_date = models.DateTimeField(null=True, blank=True)
    # created_user = models.CharField(max_length=255, null=True, blank=True)
    # last_edited_user = models.CharField(max_length=255, null=True, blank=True)
    kezdopont_bh_id = models.CharField(max_length=10, null=True, blank=True)
    vegpont_bh_id = models.CharField(max_length=10, null=True, blank=True)
    # shape = models.TextField(null=True, blank=True)  


    class Meta:
        db_table = 'bhszakasz'
        managed = False  

    @staticmethod
    def create_null_szakasz(kezdopont_bh_id,vegpont_bh_id):
        bhszakasz = BHSzakasz(kezdopont_bh_id=kezdopont_bh_id,vegpont_bh_id=vegpont_bh_id)
        return bhszakasz

    @staticmethod
    def get_from_DB(start_BHD,end_BHD,section_date,mozgalom):
        return BHSzakasz.objects.get((
                (Q(kezdopont_bh_id=start_BHD.bh.bh_id) & Q(vegpont_bh_id=end_BHD.bh.bh_id)) |
                (Q(kezdopont_bh_id=end_BHD.bh.bh_id) & Q(vegpont_bh_id=start_BHD.bh.bh_id))
            ) &
            Q(start_date__lte=section_date) &
            (Q(end_date__gte=section_date) | Q(end_date__isnull=True)) &
            Q(okk_mozgalom=mozgalom)
        )
    
    @staticmethod
    def get_actual_version_from_DB(start_bh:str,mozgalom:str):
        try:
            return BHSzakasz.objects.get((Q(kezdopont_bh_id=start_bh)&Q(end_date__isnull=True)&Q(okk_mozgalom=mozgalom)))
        except:
            return None


    def __str__(self):
        return f"{self.objectid}:{self.ver_id} {self.bhszakasz_id}, {self.szakasznev},{self.kezdopont_bh_id}/{self.kezdopont},{self.vegpont_bh_id}/{self.vegpont} at s_date:{self.start_date}, e_date: {self.end_date}"
    


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

    def get_mozgalmak_versions_in_interval(self,min_date:datetime,max_date:datetime,mozgalom:BookletTypes):
        """
        Fetch rows where the version was valid at any point between min_date and max_date.
        The start_date should be before or on max_date, and the end_date should be after or on min_date or null.
        """
        return Turamozgalom.objects.filter(
            Q(okk_mozgalom=mozgalom)
            # &
            # (Q(start_date__lte=min_date) | Q(start_date__isnull=True))
            # &
            # (Q(end_date__isnull=True) | Q(end_date__gte=max_date))
        )

    def __str__(self):
        return self.nev



class BHD:
    '''Extending BH with properties and methods to validate Stamps'''
    def __init__(self,bh:BH, timestamp:datetime=None,stamp_type:StampType=None) -> None:
        self.bh:BH = bh
        self.stamping_date:datetime = timestamp
        self.stamp_type:StampType = stamp_type
        # self.neighbour_prev:BHD|None =None
        # self.neighbour_next:BHD|None  =None

    @staticmethod
    def create_bhd_from_bh(bh:BH,timestamp: datetime, stamp_type: StampType):
        '''DB BH model, with other request data converting into BHD'''
        # time = timestamp if stamp_type == "digistamp" else timestamp.replace(hour=0,minute=0,second=0,microsecond=0)
        time = timestamp 
        bhd = BHD(
            bh=bh,
            timestamp=time,
            stamp_type=stamp_type
        )
        return bhd

    @staticmethod
    def create_bhd_from_bh_id(bh_id:str, bh_cache:dict=None):
        if bh_cache:
            bh_match = next(
            (
                bh for bh in bh_cache
                if bh['bh_id'] == bh_id
                and bh['end_date'] is None)
            )

            if bh_match:
                return BHD(bh=BH(**bh_match),timestamp=None,stamp_type=StampType.DB)  

        else:

            bh:BH = BH.get_actual_BH_from_bh_id(bh_id)
            return BHD(bh,timestamp=None,stamp_type=StampType.DB)

    def __repr__(self) -> str:
        return (f"BHD with ID:{self.bh.bh_id}, {self.bh.ver_id} MTSZ_ID: {self.bh.mtsz_id}, NEV: {self.bh.bh_nev}, Time: {self.stamping_date}, Type: {self.stamp_type}")

class BHSzD:
    def __init__(self, bh_szakasz:BHSzakasz, validation_time:datetime=None, stamp_type: StampType=None, mozgalom: BookletTypes=None,kezdopont:BHD=None, vegpont:BHD=None, direction:DirectionType=DirectionType.Unknown,speed=None ) -> None:
        self.bh_szakasz:BHSzakasz = bh_szakasz
        self.stamping_date :datetime = validation_time
        self.stamp_type:StampType = stamp_type
        self.mozgalom:BookletTypes =mozgalom
        self.kezdopont:BHD = kezdopont
        self.vegpont:BHD = vegpont
        self.direction: DirectionType = direction
        self.time:int|None = self._get_time_difference()
        self.speed:float = speed*3.6 if speed else None

    def _get_time_difference(self)-> int:
        if self.stamp_type == StampType.Digital:
            return abs((self.vegpont.stamping_date - self.kezdopont.stamping_date).total_seconds())
        return None

    def __repr__(self) -> str:
        return f"BHSzD with ID:{self.bh_szakasz.bhszakasz_id},{self.bh_szakasz.ver_id} Szakasz: {self.bh_szakasz} KezdoBH: {self.kezdopont.bh.bh_id} at {self.kezdopont.stamping_date}, VEGBH: {self.vegpont.bh.bh_id} at {self.vegpont.stamping_date}, Time: {self.stamping_date}, {self.stamp_type}, {self.mozgalom}, {self.direction}, {self.speed}km/h, {self.time} minutes"

class CustomNagyszakasz(NagySzakasz):
    def __init__(self, bhszds:List[BHSzD],id:str,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = id
        self.bhszds = bhszds
        self.min_date, self.max_date = self._get_time_interval()
        self.db_nagyszakasz = self.get_Nagyszakasz_from_db()

    def _get_time_interval(self):
        return min(bhszd.stamping_date for bhszd in self.bhszds), max(bhszd.stamping_date for bhszd in self.bhszds)
    

    def get_Nagyszakasz_from_db(self):
        if isinstance(self.min_date, datetime):
            self.min_date = self.min_date.isoformat()
        if isinstance(self.max_date, datetime):
            self.max_date = self.max_date.isoformat()
        try:
            return NagySzakasz.objects.filter(
                nagyszakasz_id=self.id,
            start_date__lte=self.min_date,
            ).filter(Q(end_date__gte=self.max_date) | Q(end_date__isnull=True)).order_by('end_date').first()
        except NagySzakasz.DoesNotExist:
            return None
    def __repr__(self):
        return f"CUSTOM Nagyszakasz: {len(self.bhszds)} elemmel, min date:{self.min_date}, max date:{self.max_date}, Nagyszakasz: {self.db_nagyszakasz}"
