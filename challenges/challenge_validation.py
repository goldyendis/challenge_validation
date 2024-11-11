from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple

from challenges.graph import NodeGraph
from challenges.enums import BookletTypes, DirectionType, StampType
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
        self.nodeGraph = NodeGraph(self.kezdopont,self.vegpont,self.validated_bhszd,self.mozgalom)
        self.nodeGraph.validate_mozgalom()
        
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
        '''BHD list sorter. First with date, then StampType, then timestamp, and lastly BH_ID'''
        def sort_key(bhd:BHD):
            type_order = 0 if bhd.stamp_type == "digistamp" else 1
            return (bhd.stamping_date.date(), type_order, bhd.stamping_date,bhd.bh.bh_id)

        self.BHD_list.sort(key=sort_key)

    def validate_bhszd_sections(self):
        n = len(self.BHD_list)
        for a in range(n - 1):
            found = failed = False
            b = a + 1
            digi_already_checked = False
            
            while b < n and not (found or failed):
                #IF next bhd is not within one day skip to next
                if self.BHD_list[a].stamping_date.date() + timedelta(days=1) < self.BHD_list[b].stamping_date.date():
                    failed = True
                else:
                    #Flag to store if next is digistamp, because for each BHD only one digi can be checked
                    if self.BHD_list[b].stamp_type == "digistamp":
                        digi_already_checked = True
                    section_date:datetime = min(self.BHD_list[a].stamping_date, self.BHD_list[b].stamping_date)
                    bh_szakasz = self.find_section(self.BHD_list[a], self.BHD_list[b],section_date)
                    if bh_szakasz:
                        bhszd_stamp_type:StampType = self._get_stamp_type([self.BHD_list[a], self.BHD_list[b]])
                        if bhszd_stamp_type.value == "digistamp":
                            if self.velocity_checked(bh_szakasz.tav, self.BHD_list[a].stamping_date, self.BHD_list[b].stamping_date):
                                self._add_to_validated_bhszd(bh_szakasz, section_date,bhszd_stamp_type,self.BHD_list[a],self.BHD_list[b])
                            else:
                                failed = True
                        else:
                            if self.BHD_list[b].bh.bh_id != self.BHD_list[b-1].bh.bh_id:
                                self._add_to_validated_bhszd(bh_szakasz, section_date,bhszd_stamp_type,self.BHD_list[a],self.BHD_list[b])
                    else:
                        failed = True
                        if failed:
                            c = b+1
                            while c< n and self.BHD_list[a].stamping_date.date()+timedelta(days=1) >= self.BHD_list[c].stamping_date.date():
                                if self.BHD_list[c].stamp_type == "digistamp" and digi_already_checked:
                                    c+=1
                                    continue
                                elif self.BHD_list[c].stamp_type == "digistamp" and not digi_already_checked:
                                    digi_already_checked = True
                                    section_date:datetime = min(self.BHD_list[a].stamping_date, self.BHD_list[c].stamping_date)
                                    bh_szakasz = self.find_section(self.BHD_list[a], self.BHD_list[c],section_date)
                                    if bh_szakasz:
                                        bhszd_stamp_type:StampType = self._get_stamp_type([self.BHD_list[a], self.BHD_list[c]])
                                        if bhszd_stamp_type.value == "digistamp":
                                            if self.velocity_checked(bh_szakasz.tav, self.BHD_list[a].stamping_date, self.BHD_list[c].stamping_date):
                                                self._add_to_validated_bhszd(bh_szakasz, section_date,bhszd_stamp_type,self.BHD_list[a],self.BHD_list[c])
                                else:
                                    section_date:datetime = min(self.BHD_list[a].stamping_date, self.BHD_list[c].stamping_date)
                                    bh_szakasz = self.find_section(self.BHD_list[a], self.BHD_list[c],section_date)
                                    if bh_szakasz:
                                        bhszd_stamp_type:StampType = self._get_stamp_type([self.BHD_list[a], self.BHD_list[c]])
                                        self._add_to_validated_bhszd(bh_szakasz, section_date,bhszd_stamp_type,self.BHD_list[a],self.BHD_list[c])
                                c +=1


                b += 1

    def _add_to_validated_bhszd(self, bh_szakasz: BHSzakasz, section_date: datetime,bhszd_stamp_type:StampType, a_BHD:BHD, b_BHD:BHD)->None:
        start, end = self._match_bhd_with_section_ends(a_BHD, b_BHD, bh_szakasz)
        direction = self._get_direction(start,end,bhszd_stamp_type)
        bhszd = BHSzD(bh_szakasz,section_date,bhszd_stamp_type,self.mozgalom,
                    start,end,direction)
        self.validated_bhszd.append(bhszd)

    def _match_bhd_with_section_ends(self, a_bhd:BHD, b_bhd:BHD, section:BHSzakasz)-> Tuple[BHD]: 
        start:BHD = a_bhd if section.kezdopont_bh_id == a_bhd.bh.bh_id else b_bhd
        end:BHD = b_bhd if section.vegpont_bh_id == b_bhd.bh.bh_id else a_bhd
        return start,end

    def _get_stamp_type(self, BHDS: List[BHD])->StampType:
        return StampType.Kezi if any(stamp.stamp_type == StampType.Kezi.value for stamp in BHDS) else StampType.Digital


    def find_section(self, start_BHD:BHD, end_BHD:BHD,section_date:datetime)->BHSzakasz:
        """Attempt to find a BHSzakasz from DB between two BHD stamps"""
        try:
            bh_szakasz = BHSzakasz.get_from_DB(start_BHD,end_BHD,section_date, self.mozgalom)
            return bh_szakasz
        except BHSzakasz.DoesNotExist:
            return None 

    def _get_direction(self,start:BHD, end:BHD, stamp_type:StampType) -> DirectionType:
        """Helper to determine if the direction of travel is forward or reverse."""
        if stamp_type == StampType.Digital:
            return DirectionType.Forward if start.stamping_date< end.stamping_date else DirectionType.Reverse
        elif stamp_type == StampType.Kezi:
            if start.stamping_date.date() < end.stamping_date.date():
                return DirectionType.Forward
            elif start.stamping_date.date() > end.stamping_date.date():
                return DirectionType.Reverse
            else:
                return DirectionType.Unknown 

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
    
