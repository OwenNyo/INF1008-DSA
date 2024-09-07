import pandas as pd
import folium
import osmnx as ox
import networkx as nx
from geopy.distance import geodesic, great_circle
from datetime import datetime
import googlemaps
from functools import lru_cache
from math import radians, cos, sin, sqrt, atan2

# Initialize the Google Maps client with your API key
gmaps = googlemaps.Client(key='AIzaSyA3xKb_HmBCX_8VpqShtvysHdpkUe24QwA')


def load_coordinates_from_csv(file_path, unique_hotels):
    # Read the Excel file
    df = pd.read_excel(file_path)

    # Create a dictionary from unique_hotels
    hotel_dict = {hotel['HotelName'].strip().lower(): hotel['HotelAddress'] for hotel in unique_hotels}

    # Filter and return the coordinates
    filtered_hotels = {
        row['HotelName']: {'coords': (float(row['Latitude']), float(row['Longitude'])), 'address': row['HotelAddress']}
        for index, row in df.iterrows() if row['HotelName'].strip().lower() in hotel_dict
    }

    # Add Changi Airport T3 at the front
    coordinates = {
        'Changi Airport T3': {'coords': (1.357107, 103.987224), 'address': 'Changi Airport Terminal 3, Singapore'},
        **filtered_hotels}

    return coordinates


# Create the map with initial markers, starting from Changi T3
def create_map(coordinates, start_location):
    starting_coordinates = coordinates[start_location]['coords']
    m = folium.Map(location=starting_coordinates, zoom_start=14)
    for name, data in coordinates.items():
        folium.Marker(location=data['coords'], popup=f"{name}<br>{data['address']}").add_to(m)
    return m


# Download the road network
def download_road_network(starting_coordinates, dist=17000):
    return ox.graph_from_point(starting_coordinates, dist=dist, network_type='drive', simplify=False)


# Get the nearest node
@lru_cache(maxsize=None)
def get_nearest_node(Graph, point):
    return ox.distance.nearest_nodes(Graph, point[1], point[0])


@lru_cache(maxsize=None)
def cached_shortest_path(Graph, source, target, method='dijkstra'):
    if method == 'astar':
        # A* algorithm implementation 
        return nx.astar_path(Graph, source=source, target=target, weight='length',
                             heuristic=lambda u, v: haversine_distance(
                                 (Graph.nodes[u]['y'], Graph.nodes[u]['x']),
                                 (Graph.nodes[v]['y'], Graph.nodes[v]['x'])))
    else:
        path = nx.shortest_path(Graph, source=source, target=target, weight='length')
        path_length = nx.shortest_path_length(Graph, source=source, target=target, weight='length')
        path_coords = [(Graph.nodes[node]['y'], Graph.nodes[node]['x']) for node in path]
        return path, path_length, path_coords


# Find nearest nodes for each location
def find_nearest_nodes(Graph, coordinates):
    return {name: get_nearest_node(Graph, data['coords']) for name, data in coordinates.items()}


# Calculate the haversine distance between two points for A* algorithm.
def haversine_distance(coord1, coord2):
    return great_circle(coord1, coord2).meters


# Find the shortest path route
def shortest_path_route(Graph, nodes, start_location, method='dijkstra'):
    route = [start_location]
    current_location = start_location
    while len(route) < len(nodes):
        min_dist = float('inf')
        next_location = None
        for location in nodes.keys():
            if location not in route:
                try:
                    if method == 'astar':
                        path = cached_shortest_path(Graph, nodes[current_location], nodes[location], method='astar')
                        dist = nx.path_weight(Graph, path, weight='length')
                    else:
                        dist = nx.shortest_path_length(Graph, nodes[current_location], nodes[location], weight='length')
                    if dist < min_dist:
                        min_dist = dist
                        next_location = location
                except nx.NetworkXNoPath:
                    continue
        if next_location is None:
            raise ValueError(f"No path found from {current_location} to any remaining locations.")
        route.append(next_location)
        current_location = next_location
    return route


# Calculate the full route
def calculate_full_route(Graph, nodes, route_order, erp_coordinates, traffic_coordinates, shell_coordinates, trip_time):
    full_route = []
    distances = []
    ERP_Passed = []
    traffic_Passed = []
    Shell_Passed = []

    for i in range(len(route_order) - 1):
        start = nodes[route_order[i]]
        end = nodes[route_order[i + 1]]
        try:
            path, distance, path_coords = cached_shortest_path(Graph, start, end)
            full_route.extend(path)
            distances.append((route_order[i], route_order[i + 1], distance / 1000))
            # path_coords = [(Graph.nodes[node]['y'], Graph.nodes[node]['x']) for node in path]

            for erp_name, erp_data in erp_coordinates.items():
                erp_point = erp_data['coords']
                for route_point in path_coords:
                    if geodesic(route_point, erp_point).meters <= 100:
                        active, active_time_range = is_erp_active(erp_data['times'], trip_time)
                        if active:
                            times_list = erp_data['times'].split(", ")
                            charges_list = erp_data['charges'].split(", ")
                            if active_time_range in times_list:
                                active_index = times_list.index(active_time_range)
                                if active_index < len(charges_list):
                                    active_charge = charges_list[active_index]
                                    ERP_Passed.append({
                                        'name': erp_name,
                                        'time_range': active_time_range,
                                        'charge': active_charge
                                    })
                            break

            for traffic_index, traffic_point in enumerate(traffic_coordinates):
                for route_point in path_coords:
                    if geodesic(route_point, traffic_point).meters <= 30:
                        traffic_Passed.append({
                            'index': traffic_index,
                            'coords': traffic_point
                        })
                        break

            if shell_coordinates:
                shell_name, shell_data = next(iter(shell_coordinates.items()))
                shell_point = shell_data['coords']
                for route_point in path_coords:
                    if geodesic(route_point, shell_point).meters <= 100:  # Threshold distance can be adjusted
                        Shell_Passed.append({
                            'name': shell_name,
                            'coords': shell_point
                        })
                        break

        except nx.NetworkXNoPath:
            print(f"No path found between {route_order[i]} and {route_order[i + 1]}.")
    return full_route, distances, ERP_Passed, traffic_Passed, Shell_Passed


# Plot the route on the map
def plot_route_on_map(Map, Graph, full_route, erp_coordinates, ERP_Passed, traffic_Passed, shell_Passed, color="blue"):
    if full_route:
        route_coords = [(Graph.nodes[node]['y'], Graph.nodes[node]['x']) for node in full_route]
        folium.PolyLine(route_coords, color=color, weight=2.5, opacity=1).add_to(Map)

        for erp in ERP_Passed:
            erp_name = erp['name']
            details = erp_coordinates[erp_name]
            folium.Marker(location=details['coords'],
                          icon=folium.Icon(color='green', icon='info-sign'),
                          popup=f"Passing through {erp_name}"
                                f"<br>Charge: {erp['charge']}<br>Time: {erp['time_range']}").add_to(Map)

        for traffic in traffic_Passed:
            coords = traffic['coords']
            # Reverse geocode the coordinates
            result = gmaps.reverse_geocode(coords)
            if result:
                address = result[0]['formatted_address']
            else:
                address = "Address not found"

            folium.Marker(location=coords,
                          icon=folium.Icon(color='darkred', icon='exclamation-sign'),
                          popup=f"Traffic incident at {address}").add_to(Map)

        for shell in shell_Passed:
            shell_name = shell['name']
            shell_coords = shell['coords']
            folium.Marker(
                location=shell_coords,
                icon=folium.Icon(color='blue', icon='exclamation-sign'),  # Choose an appropriate icon
                popup=f"Shell Station: {shell_name}"
            ).add_to(Map)

        return Map


def avoid_erp(Graph, erp_coordinates, distance=100):
    distance_in_degrees = distance / 111320  # Rough conversion factor for degrees to meters
    nodes_to_remove = set()
    for erp_name, erp_data in erp_coordinates.items():
        erp_point = erp_data['coords']
        nearest_node = ox.distance.nearest_nodes(Graph, erp_point[1], erp_point[0])
        nodes_within_distance = nx.single_source_dijkstra_path_length(Graph, nearest_node, cutoff=distance_in_degrees,
                                                                      weight='length')
        nodes_to_remove.update(nodes_within_distance)

    Graph.remove_nodes_from(nodes_to_remove)
    return Graph


def avoid_traffic(Graph, traffic_coordinates, distance=100):
    distance_in_degrees = distance / 111320  # Rough conversion factor for degrees to meters
    nodes_to_remove = set()

    # Assuming traffic_coordinates is a list of tuples (latitude, longitude)
    for lat, lon in traffic_coordinates:
        # Find the nearest node to the given coordinates
        nearest_node = ox.distance.nearest_nodes(Graph, lon, lat)

        # Get all nodes within the specified 'distance' around 'nearest_node'
        nodes_within_distance = nx.single_source_dijkstra_path_length(Graph, nearest_node, cutoff=distance_in_degrees,
                                                                      weight='length')
        nodes_to_remove.update(nodes_within_distance.keys())

    # Remove all accumulated nodes in one operation
    for node in nodes_to_remove:
        # It's more efficient to remove edges first in bulk and then the nodes
        for successor in list(Graph.successors(node)):
            if Graph.has_edge(node, successor):
                Graph.remove_edge(node, successor)
        for predecessor in list(Graph.predecessors(node)):
            if Graph.has_edge(predecessor, node):
                Graph.remove_edge(predecessor, node)
        if Graph.has_node(node):
            Graph.remove_node(node)

    return Graph


def is_erp_active(times, trip_time):
    current_time = datetime.strptime(trip_time, '%H:%M:%S').time()
    for time_range in times.split(", "):
        start_time, end_time = (datetime.strptime(t, '%H:%M').time() for t in time_range.split('-'))
        if start_time <= current_time <= end_time:
            return True, time_range
    return False, None


def extract_traffic_data_coordinates(traffic_data):
    coordinates_list = []

    # Manually add specific coordinates for simulation purpose only
    coordinates_list.append((1.338279, 103.970359))
    coordinates_list.append((1.313991, 103.932150))

    for incident in traffic_data['incidents']:
        # Check if the geometry type is 'LineString' which contains coordinates
        if incident['geometry']['type'] == 'LineString':
            # Extract all coordinate pairs for this incident
            coordinates = incident['geometry']['coordinates']
            # Reverse each coordinate pair from (longitude, latitude) to (latitude, longitude)
            reversed_coordinates = [(lat, lon) for lon, lat in coordinates]
            # Append these reversed coordinates to the list
            coordinates_list.extend(reversed_coordinates)
    return coordinates_list


def calculate_distance(lat1, lon1, lat2, lon2):
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    # Radius of Earth in kilometers. Use 6371 for kilometers or 3956 for miles
    r = 6371
    return c * r


def find_nearest_shell(hotel_lat, hotel_lon, shell_data, Graph):
    nearest_shell = None
    min_distance = float('inf')
    nearest_coords = None
    nearest_node = None
    nearest_shell_data = {}
    for index, row in shell_data.iterrows():
        shell_lat = row['station_lat']
        shell_lon = row['station_long']
        distance = calculate_distance(hotel_lat, hotel_lon, shell_lat, shell_lon)
        if distance < min_distance:
            min_distance = distance
            nearest_shell = row['station_name']
            nearest_coords = (shell_lat, shell_lon)
            # Find the nearest node in the graph for the Shell station
            nearest_node = ox.distance.nearest_nodes(Graph, shell_lon, shell_lat)
            nearest_shell_data = {
                nearest_shell: {
                    'coords': (shell_lat, shell_lon),
                    'distance': distance
                }
            }
    return nearest_shell, nearest_coords, nearest_node, nearest_shell_data, min_distance
