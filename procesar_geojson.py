import json
import os
import requests
import tarfile

# URL del archivo tar.gz de AEMET (ajústala si cambia)
URL_TAR = "URL_DEL_ARCHIVO_TAR_GZ_DE_AEMET"

# Archivos de trabajo
TAR_GZ = "avisos.tar.gz"
CARPETA_TEMP = "geojson_temp"
SALIDA_GEOJSON = "avisos_espana.geojson"

# Mapeo de colores por nivel de aviso
COLOR_MAP = {1: "yellow", 2: "orange", 3: "red"}

def descargar_tar():
    """Descarga el archivo tar.gz de AEMET."""
    response = requests.get(URL_TAR)
    if response.status_code == 200:
        with open(TAR_GZ, "wb") as f:
            f.write(response.content)
        print("Archivo descargado.")
    else:
        print(f"Error al descargar: {response.status_code}")

def extraer_tar():
    """Extrae los archivos GeoJSON."""
    if not os.path.exists(CARPETA_TEMP):
        os.makedirs(CARPETA_TEMP)
    with tarfile.open(TAR_GZ, "r:gz") as tar:
        tar.extractall(CARPETA_TEMP)
    print("Archivos extraídos.")

def procesar_geojson():
    """Combina y colorea los archivos GeoJSON."""
    geojson_combinado = {"type": "FeatureCollection", "features": []}

    for root, _, files in os.walk(CARPETA_TEMP):
        for file in files:
            if file.endswith(".geojson"):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for feature in data.get("features", []):
                        nivel = feature["properties"].get("nivel", 0)
                        if nivel in COLOR_MAP:
                            feature["properties"]["style"] = {"color": COLOR_MAP[nivel]}
                        geojson_combinado["features"].append(feature)

    with open(SALIDA_GEOJSON, "w", encoding="utf-8") as f:
        json.dump(geojson_combinado, f, ensure_ascii=False, indent=4)

    print("GeoJSON procesado.")

if __name__ == "__main__":
    descargar_tar()
    extraer_tar()
    procesar_geojson()
