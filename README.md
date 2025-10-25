## National Park Info Analysis

### National Park Data Aggregation, Web Scraping, Custom Mapping, and Analysis Toolkit
**A comprehensive tool for managing, visualizing, and enriching data related to national parks**

### Overview
- Data retrieval
- Data visualtion
- Database management
- Web scraping
- Geospatial operations

### Getting Started

**Clone the repo**
```
git clone https://github.com/googs0/NationalParkDataSyncTool.git
```

**Dependencies**
```
pip install -r requirements.txt
```

<br>

### Files included
1. **_main.py**
2. **requirements.txt**
3. **popular_codes.txt**
4. **nps_boundary.gdb.zip**

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

**if you don't an Opencage or National Park Service API key, you can get them from here:**

Opencage
```
https://opencagedata.com/api#quickstart
```

NPS
```
https://www.nps.gov/subjects/developer/get-started.htm
```
