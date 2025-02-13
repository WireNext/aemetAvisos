import requests
import tarfile
import os
import xml.etree.ElementTree as ET
import json
from io import BytesIO

def get_latest_tar_url(api_key):
    aemet_api_url = "https://opendata.aemet.es/opendata/api/avisos_cap/ultima/"
    response = requests.get(aemet_api_url, params={"api_key": api_key})
    if response.status_code == 200:
        data = response.json()
        return data.get("datos", None)
    else:
        print("Error al obtener la URL del TAR")
        return None

def download_and_extract(url, extract_path):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with tarfile.open(fileobj=BytesIO(response.content), mode='r') as tar:
            tar.extractall(path=extract_path)
        print(f"Archivos extraídos en {extract_path}")
    else:
        print("Error al descargar el archivo TAR")

def xml_to_geojson(xml_folder, output_file):
    features = []
    for filename in os.listdir(xml_folder):
        if filename.endswith(".xml"):
            file_path = os.path.join(xml_folder, filename)
            print(f"Procesando archivo: {file_path}")  # Depuración: Ver qué archivo se está procesando
            tree = ET.parse(file_path)
            root = tree.getroot()
            namespace = {'cap': 'urn:oasis:names:tc:emergency:cap:1.2'}
            
            for info in root.findall("cap:info", namespace):
                event = info.find("cap:event", namespace).text if info.find("cap:event", namespace) is not None else ""
                level = ""
                for param in info.findall("cap:parameter", namespace):
                    if param.find("cap:valueName", namespace).text == "AEMET-Meteoalerta nivel":
                        level = param.find("cap:value", namespace).text
                
                for area in info.findall("cap:area", namespace):
                    area_desc = area.find("cap:areaDesc", namespace).text if area.find("cap:areaDesc", namespace) is not None else ""
                    polygon_text = area.find("cap:polygon", namespace).text if area.find("cap:polygon", namespace) is not None else ""
                    
                    # Depuración: Verificar si se encuentra la información necesaria
                    print(f"Event: {event}, Level: {level}, Area: {area_desc}, Polygon: {polygon_text}")

                    if polygon_text:
                        coordinates = [list(map(float, coord.split(","))) for coord in polygon_text.split(" ")]
                        feature = {
                            "type": "Feature",
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": [coordinates]
                            },
                            "properties": {
                                "event": event,
                                "area": area_desc,
                                "level": level
                            }
                        }
                        features.append(feature)
    
    geojson = {"type": "FeatureCollection", "features": features}
    print(f"Total de features procesados: {len(features)}")  # Depuración: Ver cuántos features se procesaron
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=4)
        print(f"GeoJSON generado correctamente en {output_file}")

def main():
    api_key = "tu_api_key_aemet"
    extract_path = "aemet_data"
    output_file = "aemet_alerts.geojson"
    
    tar_url = get_latest_tar_url(api_key)
    if not tar_url:
        print("No se pudo obtener la URL del TAR")
        return
    
    if not os.path.exists(extract_path):
        os.makedirs(extract_path)
    
    download_and_extract(tar_url, extract_path)
    xml_to_geojson(extract_path, output_file)

if __name__ == "__main__":
    main()
