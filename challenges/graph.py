import base64
import io
import re
from typing import List
import matplotlib
from networkx import descendants
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
from challenges.models import BHD, BHSzD, BHSzakasz

class NodeGraph:
    def __init__(self, kezdopont: str, vegpont: str, bhszd_sections: List[BHSzD],mozgalom:str):
        self.kezdopont = kezdopont
        self.vegpont = vegpont
        self.mozgalom = mozgalom
        self.bhszd_sections = bhszd_sections


    def create_graph(self):
        graph = self._build_graph()
        pos = self._get_node_positions(graph)
        edge_colors, edge_labels = self._get_edge_properties(graph)
        # print("Graph Nodes:", graph.nodes(data=True))
        # print("Graph Edges:", graph.edges(data=True))
        
        

        # Draw final graph
        return self._draw_graph(graph, pos, edge_colors, edge_labels)

    def sort_bhszd_key(self, bhszd):
        """Sorting key to handle numeric ordering and suffixes for both kezdopont_bh_id and vegpont_bh_id."""
        def extract_parts(bh_id):
            match = re.match(r"OKTPH_(\d+)(?:_([A-Za-z0-9_]+))?", bh_id)
            if match:
                number = int(match.group(1))
                suffix = match.group(2) or ""
                suffix_priority = 0 if suffix == "" else 1
                return (number, suffix_priority, suffix)
            else:
                return (float('inf'), 0, "")
        
        kezdopont_key = extract_parts(bhszd.bh_szakasz.kezdopont_bh_id)
        vegpont_key = extract_parts(bhszd.bh_szakasz.vegpont_bh_id)
        
        return (kezdopont_key, vegpont_key)

    def _build_graph(self) -> nx.MultiDiGraph:
        """Creates and populates the directed graph dynamically as we reach new nodes."""
        graph = nx.MultiDiGraph()
        
        sorted_bhszd_sections = sorted(self.bhszd_sections, key=self.sort_bhszd_key)
        bhszd_edges = {}
        for bhszd in sorted_bhszd_sections:
            start = bhszd.bh_szakasz.kezdopont_bh_id
            if start in bhszd_edges:
                bhszd_edges[start].append(bhszd)
            else:
                bhszd_edges[start] = [bhszd]
        visited_nodes = set() 
        farthest_node = self.kezdopont
        edges_for_graph = []

            
        while farthest_node != self.vegpont:
            if farthest_node not in visited_nodes:
                visited_nodes.add(farthest_node)
                
                if farthest_node in bhszd_edges:
                    for bhszd in bhszd_edges[farthest_node]:
                        start, end = bhszd.bh_szakasz.kezdopont_bh_id, bhszd.bh_szakasz.vegpont_bh_id
                        edges_for_graph.append(bhszd)
                    if bhszd_edges[farthest_node] != "OKTPH_79":
                        bhszd_edges.pop(farthest_node)
                        farthest_node = end
                    else:
                        number = int(end.split("_")[1])
                        bhszd_edges.pop(farthest_node)
                        farthest_node = f"OKTPH_{number+1}" 
                    
                else:
                    bhszakasz = BHSzakasz.get_actual_version_from_DB(farthest_node, self.mozgalom)
                    start, end = bhszakasz.kezdopont_bh_id, bhszakasz.vegpont_bh_id
                    edges_for_graph.append(BHSzD(bhszakasz))
                    if bhszakasz.vegpont != "Visegrád":
                        farthest_node = end
                    else:
                        number = int(end.split("_")[1])
                        new_id = f"OKTPH_{number+1}"
                        edges_for_graph.append(BHSzD(BHSzakasz.create_null_szakasz(end,new_id)))
                        farthest_node = new_id

        for stamp,_ in bhszd_edges.items():
            for bhszd in bhszd_edges[stamp]:
                start, end = bhszd.bh_szakasz.kezdopont_bh_id, bhszd.bh_szakasz.vegpont_bh_id
                edges_for_graph.append(bhszd)

        sorted_edges_for_graph=sorted(edges_for_graph, key=self.sort_bhszd_key)
        for bhszd in sorted_edges_for_graph:
            graph.add_edge(bhszd.bh_szakasz.kezdopont_bh_id,bhszd.bh_szakasz.vegpont_bh_id,BHSzD=bhszd)
        return graph



    def _get_node_positions(self, graph: nx.MultiDiGraph) -> dict:
        """Generates positions for each node, arranging them in an alternating snake-like row layout with staggered end nodes if necessary."""
        pos = {}
        y_position = 0.5
        x_step = 4.0 
        y_step =30.0 
        max_nodes_per_row = 10 
        direction = 1 

        row_start_x = 0   

        for i, node in enumerate(graph.nodes):
            row_index = i // max_nodes_per_row
            node_index_in_row = i % max_nodes_per_row

            if node_index_in_row == 0:
                direction = 1 if row_index % 2 == 0 else -1
                row_start_x = pos[list(graph.nodes)[i - 1]][0] if i > 0 else 0

                pos[node] = (row_start_x, y_position - row_index * y_step)
            else:
                pos[node] = (pos[list(graph.nodes)[i - 1]][0] + direction * x_step, pos[list(graph.nodes)[i - 1]][1])

        for start_node in graph.nodes:
            end_nodes = [v for u, v in graph.out_edges(start_node)]
            unique_end_nodes = set(end_nodes)

            if len(unique_end_nodes) > 1: 
                for index, end_node in enumerate(unique_end_nodes):
                    if end_node != start_node:
                        offset = 8* ((index % 2) * 2 - 1) * (index // 2 + 1)
                        pos[end_node] = (pos[start_node][0] + direction * x_step, pos[start_node][1] + offset)

        return pos


    def _get_edge_properties(self, graph: nx.MultiDiGraph):
        """Determines edge colors and labels based on stamp_type and stamping_date."""
        edge_colors = []
        edge_labels = {}
        for u, v, key, data in graph.edges(keys=True, data=True):
            if data["BHSzD"]:
                bhszd = data["BHSzD"]
                if bhszd.stamping_date is not None:
                    stamp_type = bhszd.stamp_type
                    edge_colors.append(self._get_edge_color(stamp_type.value))
                    edge_labels[(u, v, key)] = (bhszd.stamping_date, edge_colors[-1])
                else:
                    edge_colors.append(self._get_edge_color("black"))

        return edge_colors, edge_labels

    def _get_edge_color(self, stamp_type: str) -> str:
        """Returns edge color based on stamp type."""
        if stamp_type == 'digistamp':
            return "green"
        elif stamp_type == 'register':
            return "red"
        return "black"

    

    def _draw_graph(self, graph: nx.MultiDiGraph, pos: dict, edge_colors: list, edge_labels: dict) -> str:
        """Draws the graph and returns it as a base64-encoded image."""
        plt.figure(figsize=(22, 22), dpi=200)
        
        labels = {node: '_\n'.join(node.split('_', 1)) if '_' in node else node for node in graph.nodes}
        nx.draw_networkx_nodes(graph, pos, node_size=1100, node_color="lightblue")
        nx.draw_networkx_labels(graph, pos, font_size=7, labels=labels)

        for ((u, v, key), color) in zip(graph.edges(keys=True), edge_colors):
            connectionstyle = "arc3,rad=0" if key == 0 else f"arc3,rad={0 + key * -0.25}"
            
            nx.draw_networkx_edges(
                graph,
                pos,
                edgelist=[(u, v)],
                edge_color=[color],
                width=2,
                connectionstyle=connectionstyle
            )
        self._draw_edge_labels(pos, edge_labels)

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        plt.close()
        buf.seek(0)
        return base64.b64encode(buf.getvalue()).decode('utf-8')

    def _draw_edge_labels(self, pos: dict, edge_labels: dict):
        """Draws edge labels on the edge line if there are multiple end nodes, otherwise below the start node."""
        ax = plt.gca()
        y_values = [y for _, y in pos.values()]
        y_min, y_max = min(y_values), max(y_values)
        plt.ylim(y_min - 2.5, y_max + 2.5)

        start_node_end_count = {}
        for (u, v, key) in edge_labels.keys():
            if u in start_node_end_count:
                start_node_end_count[u].add(v)
            else:
                start_node_end_count[u] = {v}

        for (u, v, key), (label, color) in edge_labels.items():
            x_start, y_start = pos[u]
            x_end, y_end = pos[v]
            
            multiple_ends = len(start_node_end_count[u]) > 1
            
            if multiple_ends:
                x_label = (x_start + x_end) / 2
                y_label = (y_start + y_end) / 2
            else:
                x_label = x_start
                y_label = y_start - 3 - key * 2.5

            ax.annotate(
                label,
                (x_label, y_label),
                ha='center',
                va='top',
                fontsize=5,  
                fontweight="bold",
                color=color,
                bbox=dict(boxstyle="round,pad=0.2", edgecolor="none", facecolor="white", alpha=0.7)
            )

        plt.draw()
