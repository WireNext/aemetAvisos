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
CARPETA_TEMP = "geojson_temp"
SALIDA_GEOJSON = "avisos_espana.geojson"

# Definir colores según el nivel de aviso
COLORS = {
    "Amarillo": "#FFFF00",  # Amarillo
    "Naranja": "#FFA500",  # Naranja
    "Rojo": "#FF0000"      # Rojo
}

# Color por defecto si el nivel no está definido o es desconocido
DEFAULT_COLOR = "#808080"  # Gris medio

def descargar_tar():
    """Descarga el archivo tar.gz de la URL especificada en `config.json`."""
    try:
        response = requests.get(URL_TAR)
        response.raise_for_status()
        # Obtenemos el nombre del archivo de la URL.
        file_name = URL_TAR.split("/")[-1]
        with open(file_name, "wb") as f:
            f.write(response.content)
        print("✅ Archivo descargado correctamente.")
        print(f"Archivo descargado: {file_name}")  # Añadir esta línea
        return file_name
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al descargar: {e}")
        return None

def extraer_tar(file_name):
    """Extrae los archivos GeoJSON del tar.gz."""
    if not os.path.exists(CARPETA_TEMP):
        os.makedirs(CARPETA_TEMP)
    with tarfile.open(file_name, "r:gz") as tar:
        tar.extractall(CARPETA_TEMP)
    print("✅ Archivos extraídos.")
    print(f"Archivos extraídos a: {CARPETA_TEMP}")  # Añadir esta línea

def procesar_geojson():
    """Combina y colorea los archivos GeoJSON con el formato correcto para uMap."""
    geojson_combinado = {"type": "FeatureCollection", "features": []}

    print(f"Procesando archivos en: {CARPETA_TEMP}")  # Añadir esta línea

    for root, _, files in os.walk(CARPETA_TEMP):
        for file in files:
            if file.endswith(".geojson"):
                print(f"Procesando archivo: {file}")  # Añadir esta línea
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for feature in data.get("features", []):
                        # Usamos Sev_PRP1, Sev_COCO, Sev_PRP2 y Sev_NENV para el nivel de alerta
                        nivel_aviso_prp1 = feature["properties"].get("Sev_PRP1", "")
                        nivel_aviso_coco = feature["properties"].get("Sev_COCO", "")
                        nivel_aviso_prp2 = feature["properties"].get("Sev_PRP2", "")
                        nivel_aviso_nenv = feature["properties"].get("Sev_NENV", "")

                        # Depuración: Imprimir los valores de los campos de nivel de alerta
                        print(f"Niveles de alerta: PRP1={nivel_aviso_prp1}, COCO={nivel_aviso_coco}, PRP2={nivel_aviso_prp2}, NENV={nivel_aviso_nenv}")

                        # Lógica para asignar colores basada en los cuatro campos
                        if "amarillo" in (nivel_aviso_prp1.lower(), nivel_aviso_coco.lower(), nivel_aviso_prp2.lower(), nivel_aviso_nenv.lower()):
                            color = COLORS["Amarillo"]
                        elif "naranja" in (nivel_aviso_prp1.lower(), nivel_aviso_coco.lower(), nivel_aviso_prp2.lower(), nivel_aviso_nenv.lower()):
                            color = COLORS["Naranja"]
                        elif "rojo" in (nivel_aviso_prp1.lower(), nivel_aviso_coco.lower(), nivel_aviso_prp2.lower(), nivel_aviso_nenv.lower()):
                            color = COLORS["Rojo"]
                        else:
                            color = DEFAULT_COLOR

                        # Corregimos la clave "style" y usamos "_umap_options"
                        feature["properties"]["_umap_options"] = {
                            "color": "#000000",      # Color del contorno (negro)
                            "weight": 2,             # Grosor del borde
                            "opacity": 1,            # Opacidad para la visualización
                            "fillOpacity": 0.3,      # Opacidad del relleno
                            "dashArray": 1,      # Líneas discontinuas en el borde
                            "fillColor": color,      # Relleno de color
                            "stroke": True,          # Asegura que tenga borde
                            "fill": True             # Asegura que tenga relleno
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

    print(f"GeoJSON guardado en: {SALIDA_GEOJSON}")  # Añadir esta línea
    print(f"✅ GeoJSON procesado correctamente y guardado en {SALIDA_GEOJSON}.")

if __name__ == "__main__":
    file_name = descargar_tar()
    if file_name:
        extraer_tar(file_name)
        procesar_geojson()
    else:
        print("❌ No se pudo descargar el archivo. El script no continuará.")
