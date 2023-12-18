## National Park Info Analysis

### National Park Data Aggregation, Web Scraping, Custom Mapping, and Analysis Toolkit

**You must have an Opencage API key and a National Park Service API key**
if you don't have one, you can get them from here:

Opencage
```
https://opencagedata.com/api#quickstart
```

NPS
```
https://www.nps.gov/subjects/developer/get-started.htm
```

- Usage:
  - Run the create_parks_table function to create the database table for storing park data
  - Use the NationalPark class to retrieve and store data about national parks, including descriptions and images
  - Perform data analysis, filtering parks by location or amenities, and visualize them on a map using the provided functions
  - Utilize the scrape_wikipedia function to gather additional Wikipedia descriptions for parks
  - Enhance the functionality as needed for your specific use case.

**Clone the repo**
```
git clone https://github.com/googs0/NationalParkDataSyncTool.git
```

**Dependencies**
```
pip install -r requirements.txt
```

### External Libraries
- **BeautifulSoup**: HTML parsing and web scraping
- **concurrent.futures.ThreadPoolExecutor**: Async execution
- **fiona**: Reading and writing georgraphic data files (e.g. shapefiles)
- **geopandas**: Spatial operations and mapping with pandas
- **matplotlib.pyplot & matplotlib_scalebar**: Visualizations
- **numpy**: math operations with arrays and matrices
- **Opencage**: Geocoding API
- **pandas**: Data structuring and manipulation
- **plotly**: interactive web graphs
- **Requests**: HTTP requests
- **sqlite3**: SQLite database interface

<br>
<br>

**Example image:**
![NPS API Request Class Example Screen](/assets/nps_api_screen1.png)
![NPS API Request Class Example Screen](/assets/nps_api_screen2.png)
