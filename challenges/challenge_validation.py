from datetime import datetime, timedelta
from typing import List, Tuple

from challenges.graph import NodeGraph
from challenges.enums import BookletTypes, DirectionType, StampType
from challenges.models import BHD, BH, BHDList, BHSzD, BHSzakasz

from challenges.statistic import KekturaStatistics
from challenges.task import get_bhpont_cache, get_bhszakasz_cache


class ChallengeValidation:
    '''Class to proccess BHD and BHSZD '''
    def __init__(self, request, testing) -> None:
        self.testing = testing
        self.validated_bhszd:List[BHSzD] = []
        self.mozgalom: BookletTypes = request.data.get('bookletWhichBlue',None)
        self.birth_year: int = int(request.data.get('birth_year',None))
        self.gykt_already: bool = True if request.data.get('gykt_done',None) == "true" else False
        self.BHD_list:BHDList[BHD] = self.create_BHD_objects(request)
        self.kezdopont, self.vegpont = BH.get_mozgalom_start_end_BH(self.BHD_list, self.mozgalom)
        self.sort_BHDs()
        self.validate_bhszd_sections()
        self.nodeGraph = NodeGraph(self.kezdopont,self.vegpont,self.validated_bhszd,self.mozgalom, testing=self.testing)
        self.nodeGraph.validate_mozgalom()
        self.statistics = KekturaStatistics(
            validated_bhd=self.BHD_list,
            validated_bhszd=self.validated_bhszd,
            best_path=self.nodeGraph.best_path, 
            completed_nagyszakasz=self.nodeGraph.completed_nagyszakasz, 
            all_nagyszakasz = self.nodeGraph.all_nagyszakasz,
            birth_year=self.birth_year,
            gykt_already = self.gykt_already,
            mozgalom = self.mozgalom)
        

    def create_BHD_objects(self, request)->BHDList[BHD]:
        '''Converts the request to a list of BHD objects'''
        bh_cache = get_bhpont_cache()  
        bhd_list: BHDList[BHD] = BHDList()

        for stamp in request.data.get('stamps', []):
            timestamp = self.process_timestamps(stamp)
            bh: BH = BH.create_BH_from_request(stamp, bh_cache, timestamp)
            if bh:
                bhd: BHD = BHD.create_bhd_from_bh(bh, timestamp, stamp.get('fulfillmentType'))
                bhd_list.append(bhd)

        return bhd_list


    def process_timestamps(self,stamp:dict) -> datetime:
        timestamp_iso: int = stamp.get('fulfillmentDate')
        timestamp = datetime.fromisoformat(timestamp_iso.replace("Z", "+00:00"))
        time = timestamp.replace(tzinfo=None)
        return time

    def sort_BHDs(self):
        '''BHD list sorter. First with date, then StampType, then timestamp, and lastly BH_ID'''
        def sort_key(bhd:BHD):
            type_order = 0 if bhd.stamp_type == "digistamp" else 1
            # return (bhd.stamping_date.date(), type_order, bhd.stamping_date,bhd.bh.bh_id)
            return (bhd.stamping_date.date(), bhd.bh.bh_id)

        self.BHD_list.sort(key=sort_key)

    def validate_bhszd_sections(self):
        for i,a in enumerate(self.BHD_list[:-1]):
            if a.stamping_date.date() + timedelta(days=1) < self.BHD_list[i+1].stamping_date.date():
                continue
            else:
                section_date:datetime = min(a.stamping_date, self.BHD_list[i+1].stamping_date)
                bh_szakasz = self.find_section(a, self.BHD_list[i+1],section_date)
                if bh_szakasz:
                    bhszd_stamp_type:StampType = self._get_stamp_type([a,self.BHD_list[i+1]])
                    if bhszd_stamp_type.value == "digistamp":
                        is_valid,speed = self.velocity_checked(bh_szakasz.tav, a.stamping_date, self.BHD_list[i+1].stamping_date)
                        if is_valid:
                            self._add_to_validated_bhszd(bh_szakasz, bhszd_stamp_type,a,self.BHD_list[i+1],speed)
                            continue
                        else:
                            continue
                    else:
                        self._add_to_validated_bhszd(bh_szakasz, bhszd_stamp_type,a,self.BHD_list[i+1])
                        continue
                

    def _add_to_validated_bhszd(self, bh_szakasz: BHSzakasz, bhszd_stamp_type:StampType, a_BHD:BHD, b_BHD:BHD, speed:float=None)->None:
        start, end = self._match_bhd_with_section_ends(a_BHD, b_BHD, bh_szakasz)
        direction = self._get_direction(start,end,bhszd_stamp_type)
        validation_date:datetime = max(a_BHD.stamping_date, b_BHD.stamping_date)
        bhszd = BHSzD(bh_szakasz,validation_date,bhszd_stamp_type,self.mozgalom,
                    start,end,direction,speed)
        self.validated_bhszd.append(bhszd)

    def _match_bhd_with_section_ends(self, a_bhd:BHD, b_bhd:BHD, section:BHSzakasz)-> Tuple[BHD]: 
        start:BHD = a_bhd if section.kezdopont_bh_id == a_bhd.bh.bh_id else b_bhd
        end:BHD = b_bhd if section.vegpont_bh_id == b_bhd.bh.bh_id else a_bhd
        return start,end

    def _get_stamp_type(self, BHDS: List[BHD])->StampType:
        return StampType.Kezi if any(stamp.stamp_type == StampType.Kezi.value for stamp in BHDS) else StampType.Digital


    def find_section(self, start_BHD:BHD, end_BHD:BHD,section_date:datetime)->BHSzakasz:
        """Attempt to find a BHSzakasz from DB between two BHD stamps"""
        bhszakasz_cache = get_bhszakasz_cache()
        section_match = next(
        (
            section for section in bhszakasz_cache
            if section['kezdopont_bh_id'] == start_BHD.bh.bh_id
            and section['vegpont_bh_id'] == end_BHD.bh.bh_id
            and section['start_date'] <= section_date
            and (section['end_date'] is None or section['end_date'] >= section_date)
        ),
        None
    )
        if section_match:
            return BHSzakasz(**section_match)
        else:
            try:
                bh_szakasz = BHSzakasz.get_from_DB(start_BHD,end_BHD,section_date, self.mozgalom)
                return bh_szakasz
            except BHSzakasz.DoesNotExist:
                return None 

    def _get_direction(self,start:BHD, end:BHD, stamp_type:StampType) -> DirectionType:
        """Helper to determine if the direction of travel is forward or reverse."""
        if stamp_type != StampType.DB:
            return DirectionType.Forward if start.stamping_date<end.stamping_date else DirectionType.Reverse
        else:
            return DirectionType.Unknown

    def velocity_checked(self, tav: float, start_time: datetime, end_time: datetime) -> bool:
        """Check if the calculated speed meets requirements"""
        speed = self.get_speed(start_time, end_time, tav)
        return speed <= 4.17, speed  

    def get_speed(self, start_time,end_time, tav)-> float:
        time = self.get_time_difference(start_time,end_time)
        speed = (float(tav)*1000)/time
        return speed
    
    def get_time_difference(self,start_time,end_time)-> int:
        return abs((end_time - start_time).total_seconds())
    