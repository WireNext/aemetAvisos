import json
import os
import requests
import tarfile

# Leer configuración desde `config.json`
CONFIG_FILE = "config.json"
with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = json.load(f)

URL_TAR = config["url_tar"]   # La URL del archivo tar.gz

# Archivos de trabajo
TAR_GZ = "avisos.tar.gz"
CARPETA_TEMP = "geojson_temp"
SALIDA_GEOJSON = "avisos_espana.geojson"

# Definir colores según el nivel de aviso
COLORS = {
    1: "#FFFF00",  # Amarillo
    2: "#FFA500",  # Naranja
    3: "#FF0000"   # Rojo
}

# Color por defecto si el nivel no está definido o es desconocido
DEFAULT_COLOR = "#008000"  # Verde ("green4")


def descargar_tar():
    """Descarga el archivo tar.gz de la URL especificada en `config.json`."""
    response = requests.get(URL_TAR)
    if response.status_code == 200:
        with open(TAR_GZ, "wb") as f:
            f.write(response.content)
        print("✅ Archivo descargado correctamente.")
    else:
        print(f"❌ Error al descargar: {response.status_code}")


def extraer_tar():
    """Extrae los archivos GeoJSON del tar.gz."""
    if not os.path.exists(CARPETA_TEMP):
        os.makedirs(CARPETA_TEMP)
    with tarfile.open(TAR_GZ, "r:gz") as tar:
        tar.extractall(CARPETA_TEMP)
    print("✅ Archivos extraídos.")

    # Eliminar el archivo tar.gz después de extraerlo
    os.remove(TAR_GZ)


def procesar_geojson():
    """Combina y colorea los archivos GeoJSON."""
    geojson_combinado = {"type": "FeatureCollection", "features": []}

    for root, _, files in os.walk(CARPETA_TEMP):
        for file in files:
            if file.endswith(".geojson"):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for feature in data.get("features", []):
                        nivel_aviso = feature["properties"].get("Av_mayor")  # Usamos 'Av_mayor' como nivel
                       nivel_aviso = feature["properties"].get("Av_mayor", 0)  # Si no hay 'Av_mayor', usa 0
color = COLORS.get(nivel_aviso, DEFAULT_COLOR)  # Verde si no hay nivel

if "_umap_options" not in feature["properties"]:
    feature["properties"]["_umap_options"] = {}  # Asegurar que existe

feature["properties"]["_umap_options"]["color"] = color
feature["properties"]["_umap_options"]["weight"] = 2
feature["properties"]["_umap_options"]["opacity"] = 0.8

                        geojson_combinado["features"].append(feature)

    # Guardar el resultado combinado
    with open(SALIDA_GEOJSON, "w", encoding="utf-8") as f:
        json.dump(geojson_combinado, f, ensure_ascii=False, indent=4)

    print("✅ GeoJSON procesado correctamente.")

    # Guardar el resultado combinado
    with open(SALIDA_GEOJSON, "w", encoding="utf-8") as f:
        json.dump(geojson_combinado, f, ensure_ascii=False, indent=4)

    print("✅ GeoJSON procesado correctamente.")


if __name__ == "__main__":
    descargar_tar()
    extraer_tar()
    procesar_geojson()
