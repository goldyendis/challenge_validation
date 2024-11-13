from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Set
from challenges.enums import DirectionType, StampType
from challenges.models import BHD, BHSzD
from dateutil.relativedelta import relativedelta
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class Statistic:
    mozgalom_completed:bool = True
    all_length:float = 0
    completed_length:float = 0
    length_percentage:float = 0
    remaining_length:float = 0
    completed_elevation:int = 0
    all_elevation:int = 0
    elevation_percentage:float = 0
    completed_stamps:int = 0
    remaining_stamps:int = 0
    completed_main_sections:int = 0
    all_main_sections:int = 0
    average_speed:float = 0
    time_on_blue:Dict[str, int] = field(default_factory=dict)
    since_first_stamp_time_diff: Dict[str, int] = field(default_factory=dict)
    excepted_completion: Dict[str, int] = field(default_factory=dict)

    



class KekturaStatistics:
    def __init__(self, validated_bhszd:List[BHSzD], best_path:List[BHSzD], completed_nagyszakasz:int, all_nagyszakasz:int):
        self.valid_bhszds = validated_bhszd
        self.best_path = best_path
        self.completed_main_section = completed_nagyszakasz
        self.all_main_section = all_nagyszakasz
        self.statistic_data = Statistic()
        self.statistic_data.completed_main_sections = self.completed_main_section
        self.statistic_data.all_main_sections = self.all_main_section
        self.calculate_statistics()


    def calculate_statistics(self):
        collected_stamps:Set[str] = set()
        all_stamps:Set[str] = set()
        valid_bhszd_length = 0
        valid_bhszd_time = 0
        completed_elevation = 0
        all_elevation = 0
        start_date=min(bhszd.stamping_date for bhszd in self.valid_bhszds if bhszd.stamp_type != StampType.DB and bhszd.stamping_date is not None)
        end_date=max(bhszd.stamping_date for bhszd in self.valid_bhszds if bhszd.stamp_type != StampType.DB and bhszd.stamping_date is not None)
        for path in self.best_path:
            length =self._get_validated_length(path)
            self._add_stamp_to_collection(path,all_stamps)
            elevation = self._get_elevation(path)
            all_elevation+=elevation
            self.statistic_data.all_length +=length
            
            if path.stamp_type==StampType.DB:
                self.statistic_data.remaining_length +=length
                self.statistic_data.mozgalom_completed = False
            else:
                self.statistic_data.completed_length += length
                completed_elevation+=elevation
                self._add_stamp_to_collection(path,collected_stamps)

        for path in self.valid_bhszds:
            if path.stamp_type == StampType.Kezi:
                valid_bhszd_length += path.bh_szakasz.tav
                valid_bhszd_time += self._get_time_limit(path)

            if path.stamp_type == StampType.Digital:
                valid_bhszd_length += path.bh_szakasz.tav
                valid_bhszd_time += path.time



        self._get_stamp_statistic(collected_stamps,all_stamps)
        self._calculate_average_speed(valid_bhszd_length,valid_bhszd_time)
        self._calculate_length_statistic()
        self._calculate_elevation_statistic(all_elevation,completed_elevation)
        self._calculate_date_datas(start_date,valid_bhszd_time,end_date)

    def _calculate_date_datas(self,start_date:datetime, time_on_blue,end_date):
        time_diff = relativedelta(datetime.now(), start_date) if not self.statistic_data.mozgalom_completed else relativedelta(end_date,start_date)
        self.statistic_data.since_first_stamp_time_diff = {"years":time_diff.years, "months":time_diff.months, "days":time_diff.days}
        time_on_blue_in_days = ((time_on_blue/60)/60)//24
        self.statistic_data.time_on_blue = {"days":time_on_blue_in_days, "hours":((time_on_blue/60)/60)%24}
        if 0 < self.statistic_data.length_percentage < 100:
            scale_factor = 100 / self.statistic_data.length_percentage
            estimated_remaining_time = time_diff * scale_factor
            expected_completion = datetime.now() + estimated_remaining_time

            self.statistic_data.excepted_completion = {
                "years": expected_completion.year,
                "months": expected_completion.month,
                "days": expected_completion.day  
            }
        else:
            self.statistic_data.excepted_completion = {"years": 0, "months": 0, "days": 0} 

    def _get_time_limit(self, path: BHSzD) -> int:
        time_str = path.bh_szakasz.szintido_vissza if path.direction == DirectionType.Reverse else path.bh_szakasz.szintido_oda

        if time_str:
            hours, minutes = map(int, time_str.split(":"))
            total_seconds = hours * 3600 + minutes * 60
            return total_seconds
        
        return 0

    def _calculate_elevation_statistic(self, all_elevation,completed_elevation):
        self.statistic_data.all_elevation = all_elevation
        self.statistic_data.completed_elevation = completed_elevation
        self.statistic_data.elevation_percentage = completed_elevation/all_elevation*100

    def _calculate_length_statistic(self):
        self.statistic_data.remaining_length = self.statistic_data.all_length-self.statistic_data.completed_length
        self.statistic_data.length_percentage = self.statistic_data.completed_length/self.statistic_data.all_length*100

    def _get_elevation(self,path: BHSzD):
        if path.direction == DirectionType.Reverse:
            if path.bh_szakasz.szintcsokkenes:
                return path.bh_szakasz.szintcsokkenes
            else:
                return 0
        else:
            if path.bh_szakasz.szintemelkedes:
                return path.bh_szakasz.szintemelkedes
            else:
                return 0
            

    def _calculate_average_speed(self,length,time):
        if length and time:
            length_in_meter = float(length *1000)
            self.statistic_data.average_speed = (length_in_meter/time)*3.6

    def _add_stamp_to_collection(self,path:BHSzD,collection: Set[str]):
        collection.add(path.kezdopont.bh.bh_id)
        collection.add(path.vegpont.bh.bh_id)

    def _get_validated_length(self, bhszd:BHSzD):
        return bhszd.bh_szakasz.tav if bhszd.bh_szakasz.tav is not None else 0

    def _get_stamp_statistic(self,collected_stamps: Set[str], all_stamps: Set[str]):
        self.statistic_data.completed_stamps = len(collected_stamps)
        self.statistic_data.remaining_stamps = len(all_stamps)-len(collected_stamps)


#Teljesített szintemelkedés


#Teljesített főszakaszok száma (5/27)

#------ÖSSZES BHSZD-ből jön -------
#Kéktúrázással töltött idő
#Átlagsebesség
#Első bélyegzés óta eltelt idő, vagy, ha kész van, akkor meddig tartott a teljesítés
#Várható befejezés...