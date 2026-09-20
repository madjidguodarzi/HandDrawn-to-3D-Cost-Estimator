# core/room_detector.py
import math
from typing import List, Tuple, Dict, Set, Any
from collections import defaultdict

class RoomDetector:
    """
    Detects enclosed spaces (rooms) from a set of wall segments using 
    topological face traversal.

    Algorithm Overview:
    1. Constructs a planar graph where nodes are wall endpoints and edges are walls.
    2. Sorts outgoing edges at each node by angle to enable consistent traversal.
    3. Performs a 'left-hand rule' traversal to identify minimal closed loops (faces).
    4. Filters faces based on minimum area to remove noise or tiny artifacts.
    """
    def __init__(self, min_room_area: float = 500.0):
        """
        Args:
            min_room_area: Minimum area in pixel^2 to consider a loop as a valid room.
        """
        self.min_room_area = min_room_area

    def detect_rooms(self, walls: List[Tuple[int, int, int, int, int]]) -> List[Dict[str, Any]]:
        """
        Main entry point for room detection.

        Args:
            walls: List of tuples (wall_id, x1, y1, x2, y2). 
                   Coordinates should be integers for consistent graph matching.

        Returns:
            A list of dictionaries, each containing:
            - 'coordinates': List of (x, y) tuples forming the room polygon.
            - 'wall_ids': List of wall IDs that form the boundary of this room.
            - 'area': The calculated area of the room.
        """
        if not walls:
            return []

        # ✅ 1. Build Graph and Edge Map
        # edge_to_wall_id maps a normalized edge (sorted points) to its unique DB ID
        edge_to_wall_id: Dict[Tuple[Tuple[int,int], Tuple[int,int]], int] = {}
        
        # graph maps a point to its sorted list of neighboring points
        graph: Dict[Tuple[int, int], List[Tuple[int, int]]] = defaultdict(list)
        
        for wall_id, x1, y1, x2, y2 in walls:
            p1, p2 = (x1, y1), (x2, y2)
            
            # Normalize key: ensure (smaller_point, larger_point) order for undirected matching
            key = (min(p1, p2), max(p1, p2))
            edge_to_wall_id[key] = wall_id
            
            graph[p1].append(p2)
            graph[p2].append(p1)

        # Sort neighbors at each node by angle relative to the node.
        # This ensures that when we traverse, we always pick the "next" edge in a 
        # consistent clockwise or counter-clockwise order.
        for node in graph:
            neighbors = graph[node]
            # Calculate angle for each neighbor
            angles = [(math.atan2(nb[1]-node[1], nb[0]-node[0]), nb) for nb in neighbors]
            angles.sort(key=lambda x: x[0])
            # Update graph with sorted neighbors
            graph[node] = [nb for _, nb in angles]

        # 2. Face Traversal (Left-Hand Rule)
        visited_edges: Set[Tuple[Tuple[int, int], Tuple[int, int]]] = set()
        result_rooms = []

        for start_node in list(graph.keys()):
            for next_node in graph[start_node]:
                # Define the directed edge we are about to traverse
                edge = (start_node, next_node)
                
                if edge not in visited_edges:
                    current_path = [start_node]
                    current_node, prev_node = start_node, None
                    
                    while True:
                        # Mark the directed edge as visited
                        visited_edges.add((current_node, next_node))
                        current_path.append(next_node)
                        
                        # Find the next edge: 
                        # At 'next_node', find the index of 'current_node' in its sorted neighbors.
                        # The next node in the loop is the one immediately BEFORE it in the sorted list 
                        # (this implements the left-hand turn).
                        curr_neighbors = graph[next_node]
                        idx_prev = curr_neighbors.index(current_node)
                        idx_next = (idx_prev - 1) % len(curr_neighbors)
                        
                        prev_node = current_node
                        current_node = next_node
                        next_node = curr_neighbors[idx_next]
                        
                        # Loop closure condition: 
                        # We returned to start_node AND the next step would be the second node in our path.
                        if current_node == start_node and next_node == current_path[1]:
                            break
                    
                    area = self._calculate_polygon_area(current_path)
                    
                    # Filter out small noise loops
                    if abs(area) >= self.min_room_area:
                        # 3. Extract wall IDs associated with this room's boundary
                        wall_ids = []
                        for i in range(len(current_path)):
                            p1 = current_path[i]
                            p2 = current_path[(i + 1) % len(current_path)]
                            
                            key = (min(p1, p2), max(p1, p2))
                            wid = edge_to_wall_id.get(key)
                            if wid is not None:
                                wall_ids.append(wid)
                        
                        result_rooms.append({
                            "coordinates": current_path,
                            "wall_ids": wall_ids,
                            "area": abs(area)
                        })

        return result_rooms

    @staticmethod
    def _calculate_polygon_area(points: List[Tuple[int, int]]) -> float:
        """
        Calculates the area of a polygon using the Shoelace formula.
        
        Args:
            points: List of (x, y) coordinates forming a closed loop.
            
        Returns:
            The absolute area of the polygon.
        """
        n = len(points)
        if n < 3: return 0.0
        area = sum(points[i][0]*points[(i+1)%n][1] - points[(i+1)%n][0]*points[i][1] for i in range(n))
        return abs(area) / 2.0
