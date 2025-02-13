import requests
import tarfile
from io import BytesIO
import os

def download_and_extract(url, extract_path):
    """Descarga el archivo TAR desde el URL y lo extrae en el directorio especificado."""
    response = requests.get(url, stream=True)
    
    if response.status_code == 200:
        print("Archivo descargado exitosamente.")
        
        # Guardar el contenido en un archivo para depuración
        with open("downloaded_file", "wb") as f:
            f.write(response.content)
        print("Archivo guardado como 'downloaded_file'.")
        
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
    """Procesa los archivos extraídos y guarda directamente el archivo geojson."""
    extracted_files = os.listdir(extract_path)
    print(f"Archivos extraídos: {extracted_files}")

    for filename in extracted_files:
        print(f"Verificando archivo: {filename}")
        if filename.endswith('.geojson'):
            geojson_path = os.path.join(extract_path, filename)
            print(f"Procesando archivo GeoJSON: {geojson_path}")
            
            # Guardar el archivo GeoJSON directamente en el directorio deseado
            geojson_file = os.path.join(extract_path, 'aemet_alerts.geojson')
            os.rename(geojson_path, geojson_file)  # Cambiar el nombre del archivo si es necesario
            print(f"Archivo GeoJSON guardado como: {geojson_file}")
        else:
            print(f"El archivo {filename} no es un archivo .geojson")

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
