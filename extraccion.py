import requests
import tarfile
from io import BytesIO
import os
import shutil

def download_and_extract(url, extract_path):
    """Descarga el archivo TAR desde el URL y lo extrae en el directorio especificado."""
    response = requests.get(url, stream=True)
    
    if response.status_code == 200:
        print("Archivo descargado exitosamente.")
        
        # Verificar si el archivo descargado es diferente del existente (si existe)
        download_file_path = "downloaded_file"
        if os.path.exists(download_file_path):
            os.remove(download_file_path)
            print("Archivo anterior eliminado.")
        
        # Guardar el contenido en un archivo para depuración
        with open(download_file_path, "wb") as f:
            f.write(response.content)
        print(f"Archivo guardado como '{download_file_path}'.")

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
            
            # Verificar si el archivo geojson ya existe
            geojson_file = os.path.join(extract_path, 'aemet_alerts.geojson')
            if os.path.exists(geojson_file):
                # Si existe, eliminar el anterior
                os.remove(geojson_file)
                print(f"Archivo geojson anterior eliminado: {geojson_file}")
            
            # Guardar el archivo GeoJSON directamente en el directorio deseado
            shutil.move(geojson_path, geojson_file)  # Cambiar el nombre del archivo si es necesario
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
