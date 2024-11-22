from datetime import datetime
import re
from typing import List
import networkx as nx

from challenges.enums import StampType
from challenges.models import BHD, BHSzD, BHSzakasz

def extract_parts(bh_id: str, mozgalom: str) -> int:
    """Extract relevant parts based on mozgalom."""
    if mozgalom == "RPDDK":
        mozgalom = "DDK"
    # Match all relevant prefixes and their associated numbers
    matches = re.findall(r"(AKPH|DDKPH|OKTPH)_(\d+)", bh_id)
    if matches:
        # Convert to a dictionary for easy lookup
        prefix_dict = {prefix: int(number) for prefix, number in matches}
        # Get the number associated with the current mozgalom
        return prefix_dict.get(f"{mozgalom}PH", float('inf'))
    return float('inf')  # If no matches, sort to the end

def sort_bhszd_key(bhszd, mozgalom: str):
    """Sorting key to handle numeric ordering based on the relevant prefix for the current mozgalom."""
    kezdopont_key = extract_parts(bhszd.bh_szakasz.kezdopont_bh_id, mozgalom)
    vegpont_key = extract_parts(bhszd.bh_szakasz.vegpont_bh_id, mozgalom)
    return (kezdopont_key, vegpont_key)

def build_cache_graph(bhszd_sections: List[BHSzD], mozgalom:str):
        graph = nx.MultiDiGraph()
        
        
        sorted_bhszd_sections: List[BHSzD] = sorted(
            bhszd_sections, key=lambda bhszd: sort_bhszd_key(bhszd, mozgalom)
        )
        edges_for_graph:List[BHSzD] = []

        for section in sorted_bhszd_sections:
            start, end = section.bh_szakasz.kezdopont_bh_id, section.bh_szakasz.vegpont_bh_id
            edges_for_graph.append(section)
            if section.bh_szakasz.vegpont == "Visegrád":
                number = int(end.split("_")[1])
                new_id = f"OKTPH_{number+1}"
                visegrad_nagymaros_komp = BHSzD(
                    BHSzakasz.create_null_szakasz(end,new_id),
                    mozgalom=mozgalom,
                    stamp_type=StampType.DB,
                    validation_time=datetime.now(),
                    kezdopont=BHD.create_bhd_from_bh_id(end),
                    vegpont=BHD.create_bhd_from_bh_id(new_id),
                    )
                edges_for_graph.append(visegrad_nagymaros_komp)

        for bhszd in edges_for_graph:
            graph.add_edge(bhszd.bh_szakasz.kezdopont_bh_id,bhszd.bh_szakasz.vegpont_bh_id,BHSzD=bhszd, weight=999999999999999999999999999)
        return graph