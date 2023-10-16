import requests

class NationalPark:
    # Enter API key
    nps_apikey = "" 
    base_URL = "https://developer.nps.gov/api/v1/parks"

    def __init__(self, parkCode):
        self.parkCode = parkCode
        self.description = ""
        self.fullName = ""
        self.image_urls = []
        self.get_park_attributes()

    def get_park_attributes(self):
        # Add the parkCode key/value pair
        query_string = {"api_key": NationalPark.nps_apikey, "parkCode": self.parkCode}
        response = requests.get(NationalPark.base_URL, params=query_string)

        if response.status_code == 200:
            pyData = response.json()
            parkData = pyData["data"][0]

            # Images
            images_list = parkData.get("images", [])
            self.image_urls = NationalPark.get_image_urls(images_list)

            # Update class attributes
            self.description = parkData.get("description", "")
            self.fullName = parkData.get("fullName", "")

    @staticmethod
    def get_image_urls(image_list):
        imageURLs = [image.get("url") for image in image_list]
        return imageURLs

    def __str__(self):
        return f"Park Code: {self.parkCode}\nFull Name: {self.fullName}\nDescription: {self.description}\n"

print("National Park class defined...")

favPark = NationalPark("arch")
print(favPark)

testPark = favPark
for url in testPark.image_urls:
    print(url)