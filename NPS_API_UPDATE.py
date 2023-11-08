import requests
import sqlite3
import geopandas as gpd
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup


class NationalPark:
  def __init__(self, parkCode):
    self.parkCode = parkCode
    self.description = ""
    self.fullName = ""
    self.image_urls = []
    self.get_park_attributes()

  def get_park_attributes(self):
    query_string = {"api_key": "YOUR_API_KEY", "parkCode": self.parkCode}
    response = requests.get("https://developer.nps.gov/api/v1/parks", params=query_string)
    
    if response.status_code == 200:
      park_data = response.json().get("data", [])[0]
      self.description = park_data.get("description", "")
      self.fullName = park_data.get("fullName", "")
      self.image_urls = [image.get("url") for image in park_data.get("images", [])]

  def __str__(self):
    return f"Park Code: {self.parkCode}\nFull Name: {self.fullName}\nDescription: {self.description}\n"

def create_parks_table():
  conn = sqlite3.connect("national_parks.db")
  with conn:
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parks (
            parkCode TEXT PRIMARY KEY,
            fullName TEXT,
            description TEXT,
            wikipedia_description TEXT
        )
    """)

def insert_park_data(park):
  conn = sqlite3.connect("national_parks.db")
  with conn:
    cursor = conn.cursor()
    cursor.execute("INSERT INTO parks VALUES (?, ?, ?, ?)",
                   (park.parkCode, park.fullName, park.description, park.wikipedia_description))  

def fetch_park_data_from_db(parkCode):
  conn = sqlite3.connect("national_parks.db")
  with conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM parks WHERE parkCode=?", (parkCode,))
    data = cursor.fetchone()
  if data:
    park = NationalPark(data[0])
    park.fullName = data[1]
    park.description = data[2]
    park.wikipedia_description = data[3]
    return park

def create_wikipedia_description_field():
  conn = sqlite3.connect("national_parks.db")
  with conn:
      cursor = conn.cursor()
      cursor.execute("ALTER TABLE parks ADD COLUMN wikipedia_description TEXT")
      conn.commit()

def filter_parks_by_location(location):
  conn = sqlite3.connect("national_parks.db")
  cursor = conn.cursor()
  cursor.execute("SELECT * FROM parks WHERE location=?", (location,))
  filtered_parks = [NationalPark(data[0]) for data in cursor.fetchall()]
  conn.close()
  return filtered_parks

def filter_parks_by_amenities(amenities):
  conn = sqlite3.connect("national_parks.db")
  cursor = conn.cursor()
  # You can construct a more complex SQL query based on the provided amenities
  query = "SELECT * FROM parks WHERE amenities LIKE ?"
  cursor.execute(query, ('%' + amenities + '%',))
  filtered_parks = [NationalPark(data[0]) for data in cursor.fetchall()]
  conn.close()
  return filtered_parks
    
def visualize_parks_on_map():
  conn = sqlite3.connect("national_parks.db")
  parks_df = gpd.read_sql("SELECT * FROM parks", conn)

  world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
  ax = world.plot()
  parks_df.plot(ax=ax, marker='o', color='red', markersize=5)
  plt.title("National Parks Worldwide")
  plt.show()

def scrape_wikipedia(park):
  url = f"https://en.wikipedia.org/wiki/{park.parkCode}"
  response = requests.get(url)
  if response.status_code == 200:
    soup = BeautifulSoup(response.text, "html.parser")
    # Extract relevant data from the page
    description = soup.find("p")
    if description:
      park.wikipedia_description = description.text
      # Insert this data into the database
      insert_park_data(park)
    else:
      print(f"No description found for {park.parkCode} on Wikipedia.")
  else:
    print(f"Failed to scrape Wikipedia page for {park.parkCode} (HTTP Status: {response.status_code}).")

# Call this function after inserting data from the National Park Service API
scrape_wikipedia(park1)
  
if __name__ == "__main__":
  create_parks_table()
  create_wikipedia_description_field()  # Create Wikipedia description field if it doesn't exist
  park1 = NationalPark("arch")
  insert_park_data(park1)
  retrieved_park = fetch_park_data_from_db("arch")

  if retrieved_park:
    print("Retrieved Park:")
    print(retrieved_park)

  # Call the Wikipedia scraping function within the main block
  scrape_wikipedia(park1)
  visualize_parks_on_map()
