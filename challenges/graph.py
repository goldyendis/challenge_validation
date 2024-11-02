import base64
import io
from typing import List

from matplotlib import pyplot as plt
from challenges.models import BHD, BHSzD
import networkx as nx


class StampNode:
    def __init__(self,  bhd:BHD):
        self.bhd = bhd


class BHSzDEdge:
    def __init__(self,bhszd:BHSzD ):
        self.bhszd = bhszd

class NodeGraph:
    def __init__(self, kezdopont:str,vegpont:str, bhszd_sections:List[BHSzD]):
        self.kezdopont = kezdopont
        self.vegpont = vegpont
        self.bhszd_sections = bhszd_sections

    def create_graph(self):
        Graph = nx.DiGraph()
        for bhszd in self.bhszd_sections:
            Graph.add_node(bhszd.bh_szakasz.kezdopont_bh_id)
            Graph.add_node(bhszd.bh_szakasz.vegpont_bh_id)
            Graph.add_edge(bhszd.bh_szakasz.kezdopont_bh_id, bhszd.bh_szakasz.vegpont_bh_id)

        print("NODES", Graph.nodes)
        print("EDGES", Graph.edges)

        shortest_path = nx.shortest_path(Graph)

        print("SHORTEST PATH", shortest_path)
        pos = nx.spring_layout(Graph)  # Positioning algorithm
        nx.draw(Graph, pos, with_labels=True, node_size=700, node_color="lightblue", font_size=10)
        nx.draw_networkx_edge_labels(Graph, pos)

        buf = io.BytesIO()
        plt.savefig(buf, format="png")  
        plt.close() 
        buf.seek(0)
        graph_image = base64.b64encode(buf.getvalue()).decode('utf-8')
        return graph_image