from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple

from challenges.enums import BookletTypes, StampType
from challenges.models import BHD, BH, BHDList, BHSzD, BHSzakasz
from django.db.models import Q


class ChallengeValidation:
    '''Class to proccess BHD and BHSZD '''
    def __init__(self, request) -> None:
        self.validated_bhszd:List[BHSzD] = []
        self.mozgalom: BookletTypes = request.data.get('bookletWhichBlue',None)
        self.BHD_list:BHDList[BHD] = self.create_BHD_objects(request)
        self.kezdopont, self.vegpont = BH.get_mozgalom_start_end_BH(self.BHD_list, self.mozgalom)
        self.sort_BHDs()
        self.validate_bhszd_sections()

    def create_BHD_objects(self, request)->BHDList[BHD]:
        '''Converts the request to a list of BHD objects'''
        bhd_list:BHDList[BHD] = BHDList()
        for stamp in request.data.get('stamps', []):
            timestamp = self.process_timestamps(stamp)
            bh:BH = BH.create_BH_from_request(stamp,timestamp)
            if bh:
                bhd:BHD = BHD.create_bhd_from_bh(bh,timestamp,stamp.get('fulfillmentType'))
                bhd_list.append(bhd)
            
        return bhd_list

    def process_timestamps(self,stamp:dict) -> datetime:
        '''Convert UNIX timestamp to datetime format'''
        timestamp_unix: int = stamp.get('fulfillmentDate')
        timestamp = datetime.fromtimestamp(timestamp_unix)
        return timestamp

    def sort_BHDs(self):
        '''BHD list sorter. First with date, then StampType and lastly BH_ID'''
        def sort_key(bhd:BHD):
            type_order = 0 if bhd.stamp_type == "digistamp" else 1
            return (bhd.stamping_date.date(), type_order, bhd.bh.bh_id)

        self.BHD_list.sort(key=sort_key)


    def validate_bhszd_sections(self):
        n = len(self.BHD_list)
        for a in range(n - 1):
            found = failed = False
            b = a + 1
            
            while b < n and not (found or failed):
                # Check if within +1 day difference
                if self.BHD_list[a].stamping_date + timedelta(days=1) < self.BHD_list[b].stamping_date:
                    failed = True
                else:
                    # Try finding a valid BHSzakasz
                    section_date:datetime = min(self.BHD_list[a].stamping_date, self.BHD_list[b].stamping_date)
                    bh_szakasz = self.find_section(self.BHD_list[a], self.BHD_list[b],section_date)
                    if bh_szakasz:
                        if self.velocity_checked(bh_szakasz.tav, self.BHD_list[a].stamping_date, self.BHD_list[b].stamping_date):
                            found = True
                            bhszd = BHSzD(bh_szakasz,section_date,StampType.Digital,self.mozgalom)
                            self.validated_bhszd.append(bhszd)
                        else:
                            failed = True

                if failed and self.BHD_list[b].stamp_type == StampType.Kezi:
                    if (b + 1 < n and 
                        self.BHD_list[b + 1].stamp_type == StampType.Kezi and 
                        self.BHD_list[b].stamping_date.date() == self.BHD_list[b + 1].stamping_date.date()):
                        failed = False
                        section_date:datetime = min(self.BHD_list[a].stamping_date, self.BHD_list[b+1].stamping_date)
                        bh_szakasz = self.find_section(self.BHD_list[a], self.BHD_list[b+1],section_date)
                        if bh_szakasz:
                            bhszd = BHSzD(bh_szakasz,section_date,StampType.Kezi,self.mozgalom)
                            self.validated_bhszd.append(bhszd)
                b += 1

    def find_section(self, start_BHD:BHD, end_BHD:BHD,section_date:datetime)->BHSzD:
        """Attempt to find a BHSzakasz from DB between two BHD stamps"""
        try:
            bh_szakasz = BHSzakasz.get_from_DB(start_BHD,end_BHD,section_date, self.mozgalom)
            return bh_szakasz
        except BHSzakasz.DoesNotExist:
            return None 


    def velocity_checked(self, tav: float, start_time: datetime, end_time: datetime) -> bool:
        """Check if the calculated speed meets requirements"""
        speed = self.get_speed(start_time, end_time, tav)
        return speed <= 4.17  

    def get_speed(self, start_time,end_time, tav)-> float:
        time = self.get_time_difference(start_time,end_time)
        speed = (float(tav)*1000)/time
        return speed
    
    def get_time_difference(self,start_time,end_time)-> int:
        return abs((end_time - start_time).total_seconds())
    
