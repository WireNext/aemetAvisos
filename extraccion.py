import requests
import tarfile
from io import BytesIO
import os
import json
import geojson

def download_and_extract(url, extract_path):
    """Descarga el archivo TAR desde el URL y lo extrae en el directorio especificado."""
    response = requests.get(url, stream=True)
    
    if response.status_code == 200:
        # Guardar el contenido en un archivo para depuración
        with open("downloaded_file", "wb") as f:
            f.write(response.content)
        print("Archivo descargado y guardado como 'downloaded_file'.")
        
        # Verificar si la respuesta contiene redirecciones
        if response.history:
            print(f"Redirección detectada: {response.history}")
        
        # Intentar extraer el archivo
        try:
            with tarfile.open(fileobj=BytesIO(response.content), mode='r') as tar:
                print(f"Contenido del archivo TAR: {tar.getnames()}")
                tar.extractall(path=extract_path)
            print(f"Archivo TAR extraído correctamente en {extract_path}.")
        except Exception as e:
            print(f"Error al intentar extraer el archivo TAR: {e}")
    else:
        print(f"Error al descargar el archivo. Código de estado: {response.status_code}")

def process_extracted_files(extract_path):
    """Procesa los archivos extraídos y genera un archivo geojson."""
    # Aquí asumimos que dentro de la carpeta extraída hay un archivo JSON
    # Cambiar el nombre del archivo según lo que se extraiga
    extracted_files = os.listdir(extract_path)
    print(f"Archivos extraídos: {extracted_files}")

    for filename in extracted_files:
        if filename.endswith('.json'):
            json_path = os.path.join(extract_path, filename)
            print(f"Procesando archivo JSON: {json_path}")
            
            # Leer el archivo JSON
            with open(aemet_alerts.geojson, 'r') as f:
                try:
                    data = json.load(f)
                    print(f"Datos cargados correctamente del archivo JSON.")
                except json.JSONDecodeError as e:
                    print(f"Error al decodificar el JSON: {e}")
                    continue

            # Crear un archivo GeoJSON
            geojson_data = geojson.FeatureCollection([])

            # Procesar los datos para convertirlos en formato geojson
            # Esto depende de la estructura del archivo JSON
            # Aquí asumimos que los datos tienen una lista de características (features)
            if 'features' in data:
                for feature in data['features']:  # Cambia según la estructura de tu archivo
                    geometry = feature.get('geometry', {})
                    properties = feature.get('properties', {})
                    geojson_feature = geojson.Feature(geometry=geometry, properties=properties)
                    geojson_data.features.append(geojson_feature)

                # Guardar el archivo geojson
                geojson_file = os.path.join(extract_path, 'aemet_alerts.geojson')
                with open(geojson_file, 'w') as f:
                    geojson.dump(geojson_data, f)
                print(f"Archivo geojson generado en: {geojson_file}")
            else:
                print("No se encontraron 'features' en los datos JSON.")

def main():
    url = "https://opendata.aemet.es/opendata/sh/badff987Z_CAP_C_LEMM_20250212225001_AFAE"
    extract_path = "./extraido"  # Carpeta donde se extraerán los archivos

    # Verificar si la carpeta de destino existe, si no, crearla
    if not os.path.exists(extract_path):
        os.makedirs(extract_path)
    
    # Descargar y extraer archivos
    download_and_extract(url, extract_path)

    # Procesar los archivos extraídos para generar el geojson
    process_extracted_files(extract_path)

if __name__ == "__main__":
    main()
