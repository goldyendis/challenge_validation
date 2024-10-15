from datetime import datetime
from typing import Dict, List, Set, Tuple

from challenges.enums import BookletTypes
from challenges.models import BHD, BH,BHSzakasz, BHSzakaszObject
from django.db.models import Q


class ChallengeValidation:
    '''Class to proccess BHD and BHSZD '''
    def __init__(self, request) -> None:
        self.validated_bhszakasz:List[BHSzakaszObject] = []
        self.mozgalom: BookletTypes = request.data.get('bookletWhichBlue',None)
        self.BHD_list:List[BHD] = self.create_BHD_objects(request)
        self.sort_BHDs()
        # self.validate_bh_szakasz()

    def create_BHD_objects(self, request)->List[BHD]:
        '''Converts the request to a list of BHD objects'''
        bhd_list:List[BHD] = []
        for stamp in request.data.get('stamps'):
            timestamp = self.process_timestamps(stamp)
            bh:BH = BH.create_BH_from_request(stamp,timestamp)
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

    
    def validate_bh_szakasz(self):
        '''Loop through each BHD object'''
        for index, bhd in enumerate(self.BHD_list):
            if index == len(self.BHD_list) - 1:
                print(f"No next BHD for the last element: {bhd}")
                continue
            different_bh_index = index+1
            while different_bh_index < len(self.BHD_list) and bhd.bh_id == self.BHD_list[different_bh_index].bh_id:
                different_bh_index += 1

            test_next_BHD:BHD=self.BHD_list[different_bh_index]
            print("Test:",test_next_BHD)

        # for bh_id, bhpoint in self.bh_models.items():
        #     '''Loop through each Stamp's Stamping Time List. Starting with the nearest to today date'''
        #     for time in bhpoint.stamping_date:
        #         if time in used_starting_times:
        #             continue  # Skip already used starting times

        #         '''Get from the DB that BHSzakasz, where bhpoint is the starting point, and the line is valid at that stamping time'''
        #         try:
        #             bh_szakasz = BHSzakasz.objects.get(
        #                 Q(kezdopont_bh_id=bh_id),
        #                 Q(start_date__lte=time),
        #                 Q(end_date__gte=time) | Q(end_date__isnull=True),
        #                 Q(okk_mozgalom=self.mozgalom)
        #             )
        #             '''Check the BHSzakasz end stamp ID is in the stamp list'''
        #             bh_vegpont: BH | None = self.bh_models.get(bh_szakasz.vegpont_bh_id, None)
        #             if bh_vegpont:
        #                 '''Check the endpoint timestamps, if any of them is in +/- 24 hour and the speed is correct'''
        #                 for vegpont_time in bh_vegpont.stamping_date:
        #                     if self.get_time_difference(time, vegpont_time) <= 86400 and self.get_speed(time, vegpont_time, bh_szakasz.tav) <= 4.17:
        #                         '''ADD BHSzakasz ID to the BH.right_track_link and to the left of the bh_vegpont'''
        #                         print(f"Match found: {bh_id} at {time} and {bh_szakasz.vegpont_bh_id} at {vegpont_time}, with speed of {self.get_speed(time, vegpont_time, bh_szakasz.tav)} m/s")
        #                         bhpoint.add_right_track_link(bh_szakasz.bhszakasz_id, (time, vegpont_time))
        #                         bh_vegpont.add_left_track_link(bh_szakasz.bhszakasz_id, (time, vegpont_time))
        #                         used_starting_times.add(time)
        #                         break
        #         except BHSzakasz.DoesNotExist:
        #             continue

        #         '''Get from DB that BHSzakasz, where bhpoint is starting point at stamping_time - 1day.'''
        #         try:
        #             bh_szakasz = BHSzakasz.objects.get(
        #                 Q(kezdopont_bh_id=bh_id),
        #                 Q(start_date__lte=time - timedelta(days=1)),
        #                 Q(end_date__gte=time - timedelta(days=1)) | Q(end_date__isnull=True),
        #                 Q(okk_mozgalom=self.mozgalom)
        #             )

        #             bh_vegpont: BH | None = self.bh_models.get(bh_szakasz.vegpont_bh_id, None)
        #             if bh_vegpont:
        #                 for vegpont_time in bh_vegpont.stamping_date:
        #                     if self.get_time_difference(time, vegpont_time) <= 86400 and self.get_speed(time, vegpont_time, bh_szakasz.tav) <= 4.17:
        #                         '''ADD BHSzakasz ID to the BH.right_track_link and to the left of the bh_vegpont'''
        #                         print(f"Match found: {bh_id} at {time} and {bh_szakasz.vegpont_bh_id} at {vegpont_time}, with speed of {self.get_speed(time, vegpont_time, bh_szakasz.tav)} m/s")
        #                         bhpoint.add_right_track_link(bh_szakasz.bhszakasz_id, (time, vegpont_time))
        #                         bh_vegpont.add_left_track_link(bh_szakasz.bhszakasz_id, (time, vegpont_time))
        #                         used_starting_times.add(time)
        #                         break
        #         except BHSzakasz.DoesNotExist:
        #             continue


    def get_speed(self, start_time,end_time, tav)-> float:
        time = self.get_time_difference(start_time,end_time)
        speed = (float(tav)*1000)/time
        return speed
    
    def get_time_difference(self,start_time,end_time)-> int:
        return abs((end_time - start_time).total_seconds())
    
    def get_bh_szakaszs(self) -> Dict[str, Set[Tuple[datetime, datetime]]]:
        bh_szakasz_dict: Dict[str, Set[Tuple[datetime, datetime]]] = {}
        for bh in self.bh_models.values():
            if bh.left_track_link:
                for bhszakasz_id, time_pairs in bh.left_track_link.items():
                    if bhszakasz_id not in bh_szakasz_dict:
                        bh_szakasz_dict[bhszakasz_id] = set()
                    bh_szakasz_dict[bhszakasz_id].update(time_pairs)
            if bh.right_track_link:
                for bhszakasz_id, time_pairs in bh.right_track_link.items():
                    if bhszakasz_id not in bh_szakasz_dict:
                        bh_szakasz_dict[bhszakasz_id] = set()
                    bh_szakasz_dict[bhszakasz_id].update(time_pairs)
        return bh_szakasz_dict
    

        # def validate_bh_szakasz(self):
        # '''Loop through the stamps'''
        # for bh_id, bhpoint in self.bh_models.items():
        #     '''Loop through each Stamp's Stamping Time List. Starting with the nearest to today date'''
        #     # match_found = False
        #     for time in bhpoint.stamping_date:
        #         '''Get from the DB that BHSzakasz, where bhpoint is the starting point, and the line is valid at that stamping time'''
        #         try:
        #             bh_szakasz = BHSzakasz.objects.get(
        #                 Q(kezdopont_bh_id=bh_id),
        #                 Q(start_date__lte=time),
        #                 Q(end_date__gte=time) | Q(end_date__isnull=True),
        #                 Q(okk_mozgalom=self.mozgalom)
        #             )
        #             '''Check the BHSzakasz end stamp ID is in the stamp list'''
        #             bh_vegpont:BH|None = self.bh_models.get(bh_szakasz.vegpont_bh_id, None)
        #             if bh_vegpont:
        #                 '''Check the endpoint timestamps, if any of them is in +/- 24 hour and the speed is correct'''
        #                 for vegpont_time in bh_vegpont.stamping_date:
        #                     if self.get_time_difference(time,vegpont_time) <= 86400 and self.get_speed(time,vegpont_time,bh_szakasz.tav)<=4.17:
        #                         '''ADD BHSzakasz ID to the BH.right_track_link and to the left of the bh_vegpont'''
        #                         print(f"Match found: {bh_id} at {time} and {bh_szakasz.vegpont_bh_id} at {vegpont_time}, with speed of {self.get_speed(time, vegpont_time, bh_szakasz.tav)} m/s")
        #                         bhpoint.right_track_link = bh_szakasz.bhszakasz_id
        #                         bhpoint.right_track_link_date = time
        #                         bh_vegpont.left_track_link = bh_szakasz.bhszakasz_id
        #                         bh_vegpont.left_track_link_date = vegpont_time
        #                 #         match_found = True
        #                 #         break
        #                 # if match_found:
        #                 #     break
        #         except BHSzakasz.DoesNotExist:
        #             continue
        #         '''Get from DB that BHSzakasz, where bhpoint is starting point at stamping_time - 1day.
        #         az előző napon be van ütve az előző napon tőle jobbra eső bélyegző is, 
        #         ÉS az átlagsebesség közöttük nem nagyobb, mint $MAXSPEED'''        
        #         # if match_found:
        #         #     break
        #         try:
        #             bh_szakasz = BHSzakasz.objects.get(
        #                 Q(kezdopont_bh_id=bh_id),
        #                 Q(start_date__lte=time - timedelta(days=1)),
        #                 Q(end_date__gte=time - timedelta(days=1)) | Q(end_date__isnull=True),
        #                 Q(okk_mozgalom=self.mozgalom)
        #             )

        #             bh_vegpont:BH|None = self.bh_models.get(bh_szakasz.vegpont_bh_id, None)
        #             if bh_vegpont:
        #                 for vegpont_time in bh_vegpont.stamping_date:
        #                     if self.get_time_difference(time,vegpont_time) <= 86400 and self.get_speed(time,vegpont_time,bh_szakasz.tav)<=4.17:
        #                         '''ADD BHSzakasz ID to the BH.right_track_link and to the left of the bh_vegpont'''
        #                         print(f"Match found: {bh_id} at {time} and {bh_szakasz.vegpont_bh_id} at {vegpont_time}, with speed of {self.get_speed(time, vegpont_time, bh_szakasz.tav)} m/s")
        #                         bhpoint.right_track_link = bh_szakasz.bhszakasz_id
        #                         bhpoint.right_track_link_date = time
        #                         bh_vegpont.left_track_link = bh_szakasz.bhszakasz_id
        #                         bh_vegpont.left_track_link_date = vegpont_time
        #                 #         match_found = True
        #                 #         break
        #                 # if match_found:
        #                 #     break
        #         except BHSzakasz.DoesNotExist:
        #             continue