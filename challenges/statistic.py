from dataclasses import dataclass
from datetime import datetime
from typing import List, Set
from challenges.enums import StampType
from challenges.models import BHD, BHSzD


@dataclass
class Statistic:
    all_length:float = 0
    completed_length:float = 0
    remaining_length:float = 0
    completed_elevation:float = 0
    completed_stamps:int = 0
    remaining_stamps:int = 0
    completed_main_sections:int = 0
    average_speed:float = 0
    time_on_blue:datetime = 0
    first_last_stamps_time_diff:datetime = 0
    excepted_completion:datetime = 0



class KekturaStatistics:
    def __init__(self, validated_bhszd:List[BHSzD], best_path:List[BHSzD], completed_nagyszakasz:int):
        self.valid_bhszds = validated_bhszd
        self.best_path = best_path
        self.completed_main_section = completed_nagyszakasz
        print("STATISTIC READY TO BE CALCULATED")
        self.statistic_data = Statistic()
        self.statistic_data.completed_main_sections = self.completed_main_section
        self.calculate_statistics()
        print(self.statistic_data)


    def calculate_statistics(self):
        collected_stamps:Set[BHD] = set()
        all_stamps:Set[BHD] = set()
        for path in self.best_path:
            length =self._get_validated_length(path)
            self._add_stamp_to_collection(path,all_stamps)
            if path.stamp_type==StampType.DB:
                self.statistic_data.all_length +=length
                self.statistic_data.remaining_length +=length
            else:
                self.statistic_data.all_length +=length
                self.statistic_data.completed_length += length
                self._add_stamp_to_collection(path,collected_stamps)
        self._get_stamp_statistic(collected_stamps,all_stamps)


    def _add_stamp_to_collection(self,path:BHSzD,collection: Set[BHD]):
        collection.add(path.kezdopont)
        collection.add(path.vegpont)

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