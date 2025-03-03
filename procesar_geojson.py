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

# Mensajes de advertencia según nivel de alerta
WARNING_MESSAGES = {
    "Amarillo": "Tenga cuidado, manténgase informado de las últimas previsiones meteorológicas. Pueden producirse daños moderados a personas y propiedades, especialmente a personas vulnerables o en zonas expuestas.",
    "Naranja": "Esté atento y manténgase al día con las últimas previsiones meteorológicas. Pueden producirse daños moderados a personas y propiedades, especialmente a personas vulnerables o en zonas expuestas.",
    "Rojo": "Tome medidas de precaución, permanezca alerta y actúe según los consejos de las autoridades. Manténgase al día con las últimas previsiones meteorológicas. Viaje solo si su viaje es imprescindible. Pueden producirse daños extremos o catastróficos a personas y propiedades, especialmente a las personas vulnerables o en zonas expuestas."
}

# Color por defecto si el nivel no está definido o es desconocido
DEFAULT_COLOR = "#808080"  # Gris medio

def descargar_tar():
    """Descarga el archivo tar.gz de la URL especificada en `config.json`."""
    try:
        response = requests.get(URL_TAR)
        response.raise_for_status()
        file_name = URL_TAR.split("/")[-1]
        with open(file_name, "wb") as f:
            f.write(response.content)
        print("✅ Archivo descargado correctamente.")
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

def procesar_geojson():
    """Combina y colorea los archivos GeoJSON con el formato correcto para uMap."""
    geojson_combinado = {"type": "FeatureCollection", "features": []}
    niveles_maximos = {}
    
    for root, _, files in os.walk(CARPETA_TEMP):
        for file in files:
            if file.endswith(".geojson"):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for feature in data.get("features", []):
                        zona = feature["properties"].get("Nombre_zona", "Zona desconocida")
                        niveles = [
                            feature["properties"].get("Sev_PRP1", "").lower(),
                            feature["properties"].get("Sev_COCO", "").lower(),
                            feature["properties"].get("Sev_PRP2", "").lower(),
                            feature["properties"].get("Sev_NENV", "").lower()
                        ]
                        nivel = 0
                        if "rojo" in niveles:
                            nivel = 3
                        elif "naranja" in niveles:
                            nivel = 2
                        elif "amarillo" in niveles:
                            nivel = 1
                        
                        if zona not in niveles_maximos or nivel > niveles_maximos[zona]:
                            niveles_maximos[zona] = nivel

    for root, _, files in os.walk(CARPETA_TEMP):
        for file in files:
            if file.endswith(".geojson"):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for feature in data.get("features", []):
                        zona = feature["properties"].get("Nombre_zona", "Zona desconocida")
                        nivel_maximo = niveles_maximos.get(zona, 0)
                        color = DEFAULT_COLOR
                        mensaje_advertencia = ""
                        
                        if nivel_maximo == 3:
                            color = COLORS["Rojo"]
                            mensaje_advertencia = WARNING_MESSAGES["Rojo"]
                        elif nivel_maximo == 2:
                            color = COLORS["Naranja"]
                            mensaje_advertencia = WARNING_MESSAGES["Naranja"]
                        elif nivel_maximo == 1:
                            color = COLORS["Amarillo"]
                            mensaje_advertencia = WARNING_MESSAGES["Amarillo"]
                        
                        feature["properties"]["_umap_options"] = {
                            "color": "#000000",
                            "weight": 2,
                            "opacity": 1,
                            "fillOpacity": 0.3,
                            "dashArray": 1,
                            "fillColor": color,
                            "stroke": True,
                            "fill": True
                        }
                        
                        descripcion = feature["properties"].get("Des_PRP1", "Sin descripción disponible.")
                        resumido = feature["properties"].get("Resum_PRP1", "Sin resumen disponible.")
                        fecha_expiracion = feature["properties"].get("Expire_PRP1", "Sin fecha de expiración.")
                        
                        feature["properties"]["description"] = (
                            f"<b>Resumen:</b> {resumido}<br>"
                            f"<b>Descripción:</b> {descripcion}<br>"
                            f"<b>Fecha Expiración:</b> {fecha_expiracion}<br>"
                            f"<b>Zona:</b> {zona}<br><br>"
                            f"<b>⚠️ Advertencia:</b> {mensaje_advertencia}"
                        )
                        
                        feature["properties"].pop("style", None)
                        geojson_combinado["features"].append(feature)

    with open(SALIDA_GEOJSON, "w", encoding="utf-8") as f:
        json.dump(geojson_combinado, f, ensure_ascii=False, indent=4)
    print(f"✅ GeoJSON procesado y guardado en {SALIDA_GEOJSON}.")

if __name__ == "__main__":
    file_name = descargar_tar()
    if file_name:
        extraer_tar(file_name)
        procesar_geojson()
    else:
        print("❌ No se pudo descargar el archivo. El script no continuará.")
