import json
import os
import requests
import tarfile

# Leer configuración desde `config.json`
CONFIG_FILE = "config.json"
with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = json.load(f)

URL_TAR = config["url_tar"]  # URL del archivo tar.gz

# Archivos de trabajo
TAR_GZ = "avisos.tar.gz"
CARPETA_TEMP = "geojson_temp"
SALIDA_GEOJSON = "avisos_espana.geojson"

# Definir colores según el nivel de aviso
COLORS = {
    "Amarillo": "#FFFF00",  # Amarillo
    "Naranja": "#FFA500",   # Naranja
    "Rojo": "#FF0000"       # Rojo
}

# Color por defecto si el nivel no está definido o es desconocido
DEFAULT_COLOR = "#008000"  # Verde

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

def procesar_geojson():
    """Combina y colorea los archivos GeoJSON con el formato correcto para uMap."""
    geojson_combinado = {"type": "FeatureCollection", "features": []}

    for root, _, files in os.walk(CARPETA_TEMP):
        for file in files:
            if file.endswith(".geojson"):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for feature in data.get("features", []):
                        # Usamos Sev_PRP1 para el nivel de alerta
                        nivel_aviso = feature["properties"].get("Sev_PRP1", "")
                        color = COLORS.get(nivel_aviso, DEFAULT_COLOR)

                        # Corregimos la clave "style" y usamos "_umap_options"
                        feature["properties"]["_umap_options"] = {
                            "color": color,              # Color del contorno
                            "weight": 2,                 # Grosor del borde
                            "opacity": 0.8,              # Opacidad para la visualización
                            "fillOpacity": 0.3,          # Opacidad del relleno
                            "dashArray": "5,5",          # Líneas discontinuas en el borde
                            "fillColor": color,          # Relleno de color
                            "stroke": True,              # Asegura que tenga borde
                            "fill": True                 # Asegura que tenga relleno
                        }

                        # Descripción del aviso completa
                        descripcion = feature["properties"].get("Des_PRP1", "Sin descripción disponible.")
                        resumido = feature["properties"].get("Resum_PRP1", "Sin resumen disponible.")
                        fecha_expiracion = feature["properties"].get("Expire_PRP1", "Sin fecha de expiración.")
                        nombre_zona = feature["properties"].get("Nombre_zona", "Zona no disponible.")
                        
                        # Añadimos los campos de descripción y otros detalles
                        feature["properties"]["description"] = {
                            "Resumen": resumido,
                            "Descripción": descripcion,
                            "Fecha Expiración": fecha_expiracion,
                            "Zona": nombre_zona
                        }

                        # Eliminamos "style" si existe
                        feature["properties"].pop("style", None)

                        geojson_combinado["features"].append(feature)

    # Verificar si el archivo ya existe y eliminarlo
    if os.path.exists(SALIDA_GEOJSON):
        print(f"❗ El archivo {SALIDA_GEOJSON} ya existe, se eliminará.")
        os.remove(SALIDA_GEOJSON)
    else:
        print(f"✅ El archivo {SALIDA_GEOJSON} no existía, se creará uno nuevo.")
    
    # Guardar el archivo combinado
    with open(SALIDA_GEOJSON, "w", encoding="utf-8") as f:
        json.dump(geojson_combinado, f, ensure_ascii=False, indent=4)
    
    print(f"✅ GeoJSON procesado correctamente y guardado en {SALIDA_GEOJSON}.")

if __name__ == "__main__":
    descargar_tar()
    extraer_tar()
    procesar_geojson()
