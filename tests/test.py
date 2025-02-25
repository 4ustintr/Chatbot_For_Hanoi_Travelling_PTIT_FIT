import requests
import json

overpass_url = "http://overpass-api.de/api/interpreter"
overpass_query = """
[bbox:21.0,105.7,21.1,105.9]
[out:json]
[timeout:90];
(
  way(
    21.0,
    105.7,
    21.1,
    105.9
  );
  node["amenity"](
    21.0,
    105.7,
    21.1,
    105.9
  );
);
out geom;
"""

response = requests.post(
    overpass_url, 
    data={'data': overpass_query}
)
data = response.json()



# Process individual elements
for element in data['elements']:
    if 'tags' in element:
        name = element['tags'].get('name', 'Không có tên')
        amenity = element['tags'].get('amenity', 'Không có loại')
        
        # Get coordinates based on element type
        if element['type'] == 'node':
            lat = element.get('lat', 'Không có vĩ độ')
            lon = element.get('lon', 'Không có kinh độ')
        elif element['type'] == 'way' and 'geometry' in element:
            lat = element['geometry'][0]['lat']
            lon = element['geometry'][0]['lon']
            
        with open('output.txt', 'a') as f:
            f.write(f'{name} ({amenity}): {lat}, {lon}\n')