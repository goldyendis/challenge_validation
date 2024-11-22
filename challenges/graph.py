import base64
from datetime import datetime
import io
import re
from typing import List
import matplotlib
import heapq
from challenges.enums import DirectionType, StampType

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
from challenges.models import BHD, BHSzD, BHSzakasz, CustomNagyszakasz

class NodeGraph:
    def __init__(self, kezdopont: str, vegpont: str, bhszd_sections: List[BHSzD],mozgalom:str,testing):
        self.testing = testing
        self.kezdopont = kezdopont
        self.vegpont = vegpont
        self.mozgalom = mozgalom
        self.bhszd_sections = bhszd_sections
        self.current_time = datetime.now()
        self.bhszd_graph = None
        self.bhszd_graph_image = None
        self.validated_graph = None
        self.validated_graph_image = None
        self.best_path = None
        self._create_graph()
        self.completed_nagyszakasz = 0
        self.all_nagyszakasz = 0
        

    def _create_graph(self):
        self.bhszd_graph = self._build_graph(self.bhszd_sections)
        if self.testing:
            self.bhszd_graph_image=self._create_graph_image(self.bhszd_graph)

    
    def _create_graph_image(self,graph):
        pos = self._get_node_positions(graph)
        edge_colors, edge_labels = self._get_edge_properties(graph)
        return self._draw_graph(graph, pos, edge_colors, edge_labels)


    def _custom_edge_weight(self,bhszd:BHSzD):
        stamp_type_multiplier = {
            StampType.Digital.value:1,
            StampType.Kezi.value:100000000,
            StampType.DB.value:999999999999999999999999999
        }
        stamp_type = bhszd.stamp_type 
        stamp_time = bhszd.stamping_date
        if stamp_type == StampType.DB:
            return stamp_type_multiplier[StampType.DB.value]
        elif stamp_type == StampType.Kezi:
            day_diff = abs((self.current_time - stamp_time).total_seconds())/60
            if bhszd.bh_szakasz.end_date is None:
                return stamp_type_multiplier[StampType.Kezi.value]+day_diff
            else:
                return stamp_type_multiplier[StampType.Kezi.value]+day_diff
        else:
            day_diff = abs((self.current_time - stamp_time).total_seconds())/60
            if bhszd.bh_szakasz.end_date is None:
                return stamp_type_multiplier[StampType.Digital.value]+day_diff
            else:
                return stamp_type_multiplier[StampType.Digital.value]+day_diff

    def validate_mozgalom(self):
        self.best_path:List[BHSzD] = self.custom_dijkstra_path(self.bhszd_graph, self.kezdopont, self.vegpont, weight="weight")
        self.validated_graph= nx.MultiDiGraph()
        for bhszd in self.best_path:
            self.validated_graph.add_edge(bhszd.bh_szakasz.kezdopont_bh_id,bhszd.bh_szakasz.vegpont_bh_id,BHSzD=bhszd)
        if self.testing:
            self.validated_graph_image = self._create_graph_image(self.validated_graph)
        self._group_bhszd_by_nagyszakasz()


    def _group_bhszd_by_nagyszakasz(self):
        nagyszakasz_bhszds = {}
        nagyszakasz_db = {}
        for bhszd in self.best_path:
            if bhszd.stamp_type != StampType.DB:
                value = nagyszakasz_bhszds.get(bhszd.bh_szakasz.nagyszakasz_id, None)
                if not value:
                    nagyszakasz_bhszds[bhszd.bh_szakasz.nagyszakasz_id] = []
                    nagyszakasz_bhszds[bhszd.bh_szakasz.nagyszakasz_id].append(bhszd)
                else:
                    value.append(bhszd)
            else:
                if bhszd.bh_szakasz.nagyszakasz_id:
                    value = nagyszakasz_db.get(bhszd.bh_szakasz.nagyszakasz_id, None)
                    if not value:
                        nagyszakasz_db[bhszd.bh_szakasz.nagyszakasz_id] = []
                        nagyszakasz_db[bhszd.bh_szakasz.nagyszakasz_id].append(bhszd)
                    else:
                        value.append(bhszd)
        self.all_nagyszakasz = len(nagyszakasz_db.keys())
        for key,value in nagyszakasz_bhszds.items():
            custom_nagyszakasz = CustomNagyszakasz(value,key)
            nagyszakasz_graph = nx.MultiDiGraph()
            for edge in custom_nagyszakasz.bhszds:
                nagyszakasz_graph.add_edge(edge.bh_szakasz.kezdopont_bh_id,edge.bh_szakasz.vegpont_bh_id,BHSzD=edge, weight=1)
            try:
                path = self.custom_dijkstra_path(nagyszakasz_graph,custom_nagyszakasz.db_nagyszakasz.kezdopont_bh_id, custom_nagyszakasz.db_nagyszakasz.vegpont_bh_id,weight="weight")
                if path:
                    self.completed_nagyszakasz+=1
            except:
                pass

    def custom_dijkstra_path(self, graph, source, target, weight="weight"):
        queue = [(0, source, [], [])]  
        visited = set()

        while queue:
            (cost, u, path, edge_used) = heapq.heappop(queue)

            if u in visited:
                continue
            visited.add(u)

            path = path + [u]

            if u == target:
                return edge_used 

            for v, edge_data in graph[u].items():
                min_edge_weight = float('inf')
                best_bhszd = None
                for edge_key, edge in edge_data.items():
                    edge_weight = edge.get(weight, float('inf'))
                    if edge_weight < min_edge_weight:
                        min_edge_weight = edge_weight
                        best_bhszd = edge["BHSzD"]

                if v not in visited and best_bhszd:
                    new_edge_used = edge_used + [best_bhszd]
                    heapq.heappush(queue, (cost + min_edge_weight, v, path, new_edge_used))

        return None


    def extract_parts(self,bh_id: str) -> int:
        """Extract relevant parts based on mozgalom."""
        mozgalom_type = self.mozgalom
        if self.mozgalom == "RPDDK":
            mozgalom_type = "DDK"
        # Match all relevant prefixes and their associated numbers
        matches = re.findall(r"(AKPH|DDKPH|OKTPH)_(\d+)", bh_id)
        if matches:
            # Convert to a dictionary for easy lookup
            prefix_dict = {prefix: int(number) for prefix, number in matches}
            # Get the number associated with the current mozgalom
            return prefix_dict.get(f"{mozgalom_type}PH", float('inf'))
        return float('inf')  # If no matches, sort to the end

    def sort_bhszd_key(self,bhszd):
        """Sorting key to handle numeric ordering based on the relevant prefix for the current mozgalom."""
        kezdopont_key = self.extract_parts(bhszd.bh_szakasz.kezdopont_bh_id, self.mozgalom)
        vegpont_key = self.extract_parts(bhszd.bh_szakasz.vegpont_bh_id, self.mozgalom)
        return (kezdopont_key, vegpont_key)

    def _build_graph(self, bhszd_sections) -> nx.MultiDiGraph:
        """
        Creates and populates the directed graph dynamically by updating the cached graph
        and adding new, validated BHSzD sections.
        """
        # Retrieve cached graph for the current 'mozgalom'
        from challenges.task import get_graph_cache
        cached_graph: nx.MultiDiGraph = get_graph_cache(self.mozgalom)

        # Create a new graph to work with
        graph = nx.MultiDiGraph()
        if cached_graph:
            graph = cached_graph.copy()
        
        cached_nodes = set(graph.nodes)

        for bhszd in bhszd_sections:
            start = bhszd.bh_szakasz.kezdopont_bh_id
            end = bhszd.bh_szakasz.vegpont_bh_id
            edge_weight = int(self._custom_edge_weight(bhszd))

            # Remove existing edges between these nodes to replace them with validated BHSzD
            edges_to_remove = [
                (u, v, key) for u, v, key, data in graph.edges(keys=True, data=True)
                if u == start and v == end and data["BHSzD"].stamp_type == StampType.DB
            ]
            if edges_to_remove:
                graph.remove_edges_from(edges_to_remove)

            # Add missing nodes
            if start not in cached_nodes:
                graph.add_node(start)
                cached_nodes.add(start)
            if end not in cached_nodes:
                graph.add_node(end)
                cached_nodes.add(end)

            # Add the new validated edge
            graph.add_edge(start, end, BHSzD=bhszd, weight=edge_weight)

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
        plt.figure(figsize=(22, 22), dpi=100)
        
        labels = {node: '_\n'.join(node.split('_', 1)) if '_' in node else node for node in graph.nodes}
        nx.draw_networkx_nodes(graph, pos, node_size=300, node_color="lightblue")
        nx.draw_networkx_labels(graph, pos, font_size=7, labels=labels)

        for ((u, v, key), color) in zip(graph.edges(keys=True), edge_colors):
            bhszd = graph[u][v][key]["BHSzD"]
            direction = bhszd.direction

            if direction == DirectionType.Forward:
                connectionstyle = f"arc3,rad={0 + key * 0.25}"  
                arrowstyle = "-|> "
            elif direction == DirectionType.Reverse:
                connectionstyle = f"arc3,rad={-(0 + key * 0.25)}"  
                arrowstyle = " <|-"
            else:
                connectionstyle = f"arc3,rad={0 + key * 0.25}"  
                arrowstyle = "-|> "
                    
            nx.draw_networkx_edges(
                graph,
                pos,
                edgelist=[(u, v)],
                edge_color=[color],
                width=2,
                connectionstyle=connectionstyle,
                arrowstyle=arrowstyle,
        arrowsize=15
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
