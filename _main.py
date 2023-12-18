from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import fiona
import geopandas as gpd
from geopy.distance import geodesic
from matplotlib import pyplot as plt
import numpy as np
from opencage.geocoder import OpenCageGeocode
import pandas as pd
import plotly.graph_objects as go
import requests
import sqlite3
from matplotlib_scalebar.scalebar import ScaleBar


# Console Output
desired_width = 1080
pd.set_option('display.width', desired_width)
np.set_printoptions(linewidth=desired_width)
pd.set_option('display.max_columns', None)

# OpenCage
opencage_api_key = ''
geocoder = OpenCageGeocode(opencage_api_key)

# NPS
nps_api_key = ''


# Queried NPS Individual NP
class NationalPark:
    def __init__(self, parkCode):
        self.parkCode = parkCode
        self.description = ""
        self.fullName = ""
        self.image_urls = []
        self.wikipedia_description = ""
        self.get_park_attributes()

    def get_park_attributes(self):
        query_string = {"api_key": nps_api_key, "parkCode": self.parkCode}
        response = requests.get("https://developer.nps.gov/api/v1/parks", params=query_string)

        if response.status_code == 200:
            park_data = response.json().get("data", [])[0]
            self.description = park_data.get("description", "")
            self.fullName = park_data.get("fullName", "")
            self.image_urls = [image.get("url") for image in park_data.get("images", [])]

    def __str__(self):
        return f"Park Code: {self.parkCode}\nFull Name: {self.fullName}\nDescription: {self.description}\n"


# Personal National Park DB
class NationalParksDB:
    def __init__(self, db_name="national_parks.db"):
        self.db_name = db_name
        self.create_parks_table()

    def create_parks_table(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS parks (
                    parkCode TEXT PRIMARY KEY,
                    fullName TEXT,
                    description TEXT,
                    wikipedia_description TEXT
                )
            """)

    def insert_park_data(self, park):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM parks WHERE parkCode=?", (park.parkCode,))
            existing_data = cursor.fetchone()

            if existing_data:
                cursor.execute("""
                    UPDATE parks
                    SET fullName=?, description=?, wikipedia_description=?
                    WHERE parkCode=?
                """, (park.fullName, park.description, park.wikipedia_description, park.parkCode))
                print(f"Updated data for park with parkCode {park.parkCode}")
            else:
                cursor.execute("INSERT INTO parks VALUES (?, ?, ?, ?)",
                               (park.parkCode, park.fullName, park.description, park.wikipedia_description))
                print(f"Inserted data for new park with parkCode {park.parkCode}")

    def fetch_park_data_from_db(self, parkCode):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM parks WHERE parkCode=?", (parkCode,))
            data = cursor.fetchone()

        if data:
            park = NationalPark(data[0])
            park.fullName = data[1]
            park.description = data[2]
            park.wikipedia_description = data[3]
            return park

    def create_wikipedia_description_field(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(parks)")
            columns = cursor.fetchall()
            column_names = [column[1] for column in columns]

            if 'wikipedia_description' not in column_names:
                cursor.execute("ALTER TABLE parks ADD COLUMN wikipedia_description TEXT")
                print("Added 'wikipedia_description' column.")
            else:
                print("Column 'wikipedia_description' already exists.")


def fetch_all_parks_from_api():
    print("Fetching all parks from NPS API")
    # Fetch all parks from the NPS API
    api_url = "https://developer.nps.gov/api/v1/parks"
    params = {"api_key": nps_api_key, "limit": 600}

    response = requests.get(api_url, params=params)

    if response.status_code == 200:
        parks_data = response.json().get("data", [])
        return parks_data
    else:
        print(f"Failed to fetch parks from NPS API (HTTP Status: {response.status_code}).")
        return []


def visualize_all_parks_on_map():
    # Fetch all parks directly from the NPS API
    parks_data = fetch_all_parks_from_api()

    if parks_data:
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=5) as executor:  # Adjust max_workers as needed
            # Concurrently geocode park locations
            park_locations = list(executor.map(lambda location: geocode_location(location["fullName"]), parks_data))

        # Filter out locations with None values
        park_locations = [(lat, lng, park_data["fullName"]) for (lat, lng), park_data
                          in zip(park_locations, parks_data) if lat is not None and lng is not None]

        # Scatter plot
        fig = go.Figure()

        # Add scatter mapbox traces
        fig.add_trace(go.Scattermapbox(
            lon=[lng for lat, lng, park_name in park_locations],
            lat=[lat for lat, lng, park_name in park_locations],
            text=[park_name for lat, lng, park_name in park_locations],
            mode='markers',
            marker=dict(
                size=13,
                color='#ff0066',
                opacity=0.9,
            ),
            name='National Parks'
        ))

        # Add custom Mapbox raster layer
        fig.update_layout(
            mapbox=dict(
                style="white-bg",
                layers=[
                    {
                        "below": 'traces',
                        "sourcetype": "raster",
                        "sourceattribution": "United States Geological Survey",
                        "source": [
                            "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}"
                        ]
                    }
                ],
                # US Map
                zoom=3,
                center=dict(lat=39.8283, lon=-98.5795),
            )
        )

        fig.update_layout(
            paper_bgcolor='#262626',
            margin=dict(l=0, r=0, b=0, t=0),
            font=dict(color='#ffffff'),
            legend=dict(font=dict(color='#f2f5f5'))
        )

        fig.show()
    else:
        print("No parks data found.")


def geocode_location(location):
    try:
        result = geocoder.geocode(location)
        if result and 'geometry' in result[0]:
            return result[0]['geometry']['lat'], result[0]['geometry']['lng']
        else:
            return None, None
    except (IndexError, TypeError):
        return None, None


def plot_boundary_on_map(park_gdf):
    fig = go.Figure()

    if not park_gdf.empty:
        # Calculate the center and zoom level based on the extent of the park boundary
        center_lat = park_gdf.bounds["maxy"].mean()
        center_lon = park_gdf.bounds["maxx"].mean()
        lat_range = park_gdf.bounds["maxy"].max() - park_gdf.bounds["miny"].min()
        lon_range = park_gdf.bounds["maxx"].max() - park_gdf.bounds["minx"].min()

        # Adjust zoom
        if lat_range > lon_range:
            zoom = 8 - np.log2(lat_range)
        else:
            zoom = 8 - np.log2(lon_range)

        # Add the park boundary as a GeoJSON layer
        fig.add_trace(go.Choroplethmapbox(
            geojson=park_gdf.geometry.__geo_interface__,
            showscale=False,
            locations=park_gdf.index,
            colorscale='Turbo',
            z=[1] * len(park_gdf),
            text=park_gdf['UNIT_NAME'] + '<br>' + park_gdf['STATE'],
            hoverinfo="location+z+text",
            marker=dict(
                opacity=0.9,
                line_width=1.5,
                line_color='orangered'
            ),
        ))

        # Set the layout of the map with terrain style
        fig.update_layout(
            mapbox_style="white-bg",
            mapbox_layers=[
                {
                    "below": 'traces',
                    "sourcetype": "raster",
                    "sourceattribution": "United States Geological Survey",
                    "source": [
                        "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}"
                    ]
                }
            ],
            mapbox_center={"lat": center_lat, "lon": center_lon},
            mapbox_zoom=zoom,
            margin=dict(l=0, r=0, b=0, t=0),
        )

        fig.show()


def calculate_distance(point1, point2):
    lat1, lon1 = point1
    lat2, lon2 = point2

    # Ensure latitude values are within the valid range [-90, 90]
    lat1 = max(min(lat1, 90), -90)
    lat2 = max(min(lat2, 90), -90)

    return geodesic((lat1, lon1), (lat2, lon2)).kilometers


# Function to draw the park boundary with a scale bar
def draw_park_boundary(park_gdf):
    # Reproject the park geometry to a projected CRS (e.g., Web Mercator)
    park_gdf_projected = park_gdf.to_crs(epsg=3857)

    # Get the x and y coordinates of the park boundary
    x, y = park_gdf_projected.geometry.total_bounds[0], park_gdf_projected.geometry.total_bounds[1]

    # Calculate the scale bar distance using the approximate length of the bounding box diagonal
    lon_range = park_gdf_projected.bounds["maxx"].max() - park_gdf_projected.bounds["minx"].min()
    lat_range = park_gdf_projected.bounds["maxy"].max() - park_gdf_projected.bounds["miny"].min()
    diagonal_length = np.sqrt(lon_range ** 2 + lat_range ** 2)

    # Calculate the scale bar distance
    scalebar_distance = calculate_distance((y, x), (y + diagonal_length, x))

    # Create the scale bar
    scalebar = ScaleBar(dx=scalebar_distance, location='lower right', length_fraction=0.1,
                        scale_loc='bottom', units='km', border_pad=0.5,
                        color='black', box_alpha=0)

    # Create a figure and axis
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_facecolor('#f0f0f0')  # Light gray background
    park_gdf_projected.plot(ax=ax, alpha=0.8, edgecolor='#006633', linewidth=2, facecolor='#99ff66', zorder=2)

    # Set equal aspect ratio
    ax.set_aspect('equal', adjustable='box')

    park_gdf_projected.boundary.plot(ax=ax, color='#1A1A1A', linewidth=1.5, zorder=3)
  
    title_font = {'fontsize': 20, 'fontweight': 'bold', 'color': '#1A1A1A', 'fontfamily': 'sans'}
    ax.set_title(f"Boundary of {park_gdf['UNIT_NAME'].iloc[0]}", fontdict=title_font)

    # Add scalebar to plot
    ax.add_artist(scalebar)
    label_font = {'fontsize': 12, 'color': 'black'}
    ax.text(park_gdf_projected.bounds["minx"].min(), park_gdf_projected.bounds["miny"].min() - 0.05,
            f'Scale: {scalebar_distance:.2f} km', fontdict=label_font, ha='center', va='center',
            backgroundcolor='white')

    # Remove x and y axis labels and ticks
    ax.set_xticks([])
    ax.set_yticks([])

    plt.tight_layout()
    plt.show()


def park_boundary(parkCode, draw_boundary=False):
    # Path to the GDB file
    gdb_path = 'nps_boundary.gdb'

    # Use fiona list layers to get the list of layer names
    layer_names = fiona.listlayers(gdb_path)

    print("Layer names in the GDB file:")
    for layer_name in layer_names:
        print(layer_name)

    # Name of the layer containing park boundaries
    layer_name = 'nps_boundary'
    print(f"Chosen layer: {layer_name}")

    # Read the GDB layer into a GeoDataFrame
    gdf = gpd.read_file(gdb_path, layer=layer_name)

    print(f"Columns of the GeoDataFrame:\n{gdf.columns}\n")
    print(f"Sample of the GeoDataFrame:\n{gdf.sample()}\n")

    # If 'parkCode' is not present, replace it with the correct column name
    park_code_column_name = 'UNIT_CODE'
    park_boundary_desired = gdf[gdf[park_code_column_name] == parkCode.upper()]

    # Resulting GeoDataFrame
    print(f"Desired Park: {park_boundary_desired}\n")

    if draw_boundary:
        draw_park_boundary(park_boundary_desired)

    plot_boundary_on_map(park_boundary_desired)


def scrape_wikipedia(park, db_instance, num_paragraphs=5):
    url = f"https://en.wikipedia.org/wiki/{park.fullName}"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract text from the first num_paragraphs paragraphs
        paragraphs = soup.find_all("p")[:num_paragraphs]
        wikipedia_description = ' '.join([paragraph.text for paragraph in paragraphs])

        # Compare with existing description
        if wikipedia_description != park.description:
            print(f"\nWikipedia Scrape - {park.fullName}:\n{wikipedia_description}\n")

            # Update Wikipedia description in the database
            park.wikipedia_description = wikipedia_description
            db_instance.insert_park_data(park)
        else:
            print(f"No new information found for {park.fullName} on Wikipedia.")
    else:
        print(f"Failed to scrape Wikipedia page for {park.parkCode} (HTTP Status: {response.status_code}).")


def main():
    desired_park_code = "dena"

    national_parks_db = NationalParksDB()

    # Update schema
    national_parks_db.create_wikipedia_description_field()

    # NationalPark object for desired park code
    park_for_query = NationalPark(desired_park_code)

    # Insert / update park data in database
    national_parks_db.insert_park_data(park_for_query)

    # Scrape wiki for new info not found in park description from NPS
    scrape_wikipedia(park_for_query, national_parks_db)

    # Plot park boundaries
    park_boundary(desired_park_code)
    visualize_all_parks_on_map()


if __name__ == "__main__":
    main()
