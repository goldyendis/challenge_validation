from datetime import datetime
from typing import List, Set
from django.db import models
from django.db.models import Q
from rest_framework import exceptions
from challenges.enums import BookletTypes, StampType


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
    def create_BH_from_request(json_stamp:dict,timestamp: datetime):
        '''
        With the POST request data, get the BH from the DB.
        Database versioning starts from 2000-01-01, so converting lower date up to that'''
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
            print(exceptions.ValidationError(f"No BHPoint found for mtsz_id {json_stamp.get('stampPointId')} at {timestamp}"))
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



    def __str__(self):
        return f"{self.objectid}: {self.bhszakasz_id}, {self.szakasznev},{self.kezdopont_bh_id},{self.vegpont_bh_id} at s_date:{self.start_date}, e_date: {self.end_date}"
    

class BHSzD:
    def __init__(self, bh_szakasz:BHSzakasz, validation_time:datetime=None, stamp_type: StampType=None, mozgalom: BookletTypes=None ) -> None:
        self.bh_szakasz:BHSzakasz = bh_szakasz
        self.stamping_date :datetime = validation_time
        self.stamp_type:StampType = stamp_type
        self.mozgalom:BookletTypes =mozgalom
        # self.bh_szakasz_id:str = bh_szakasz.bhszakasz_id
        # self.kezdopont:BHD = bh_szakasz.kezdopont_bh_id
        # self.vegpont:BHD = bh_szakasz.vegpont_bh_id
    

    def __repr__(self) -> str:
        return f"BHSzD with ID:{self.bh_szakasz.bhszakasz_id}, KezdoBH: {self.bh_szakasz.kezdopont_bh_id}, VEGBH: {self.bh_szakasz.vegpont_bh_id}, Time: {self.stamping_date}, StampType: {self.stamp_type}, Mozgalom: {self.mozgalom}"


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
            &
            (Q(start_date__lte=min_date) | Q(start_date__isnull=True))
            &
            (Q(end_date__isnull=True) | Q(end_date__gte=max_date))
        )

    def __str__(self):
        return self.nev



class BHD:
    '''Extending BH with properties and methods to validate Stamps'''
    def __init__(self,bh:BH, timestamp:datetime,stamp_type:StampType) -> None:
        self.bh:BH = bh
        self.stamping_date:datetime = timestamp
        self.stamp_type:StampType = stamp_type
        # self.neighbour_prev:BHD|None =None
        # self.neighbour_next:BHD|None  =None

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
        return (f"BHD with ID:{self.bh.bh_id}, MTSZ_ID: {self.bh.mtsz_id}, NEV: {self.bh.bh_nev}, Time: {self.stamping_date}, Type: {self.stamp_type}")
