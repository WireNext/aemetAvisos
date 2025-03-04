import json
import os
import shutil
import requests
import tarfile
from datetime import datetime

# Definir la variable para forzar actualización
FORZAR_ACTUALIZACION = True  # Puedes cambiarlo a False si no quieres forzar

# Leer configuración desde `config.json`
CONFIG_FILE = "config.json"
with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    config = json.load(f)

URL_TAR = config["url_tar"]  # URL del archivo tar.gz

# Definir rutas
TAR_FILE_PATH = "datos/avisos.tar"
EXTRACT_PATH = "datos/geojson_temp"
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

DEFAULT_COLOR = "#808080"  # Gris medio

def descargar_tar():
    """Descarga el archivo tar.gz de la URL especificada en `config.json`."""
    try:
        response = requests.get(URL_TAR)
        response.raise_for_status()
        os.makedirs(os.path.dirname(TAR_FILE_PATH), exist_ok=True)
        with open(TAR_FILE_PATH, "wb") as f:
            f.write(response.content)
        print("✅ Archivo descargado correctamente.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al descargar: {e}")

def extraer_tar():
    """Extrae los archivos GeoJSON del tar.gz."""
    if not os.path.exists(EXTRACT_PATH):
        os.makedirs(EXTRACT_PATH)
    with tarfile.open(TAR_FILE_PATH, "r:gz") as tar:
        tar.extractall(EXTRACT_PATH)
    print("✅ Archivos extraídos.")

def procesar_geojson():
    """Combina y colorea los archivos GeoJSON con el formato correcto para uMap, seleccionando los avisos más severos y activos."""
    geojson_combinado = {"type": "FeatureCollection", "features": []}
    niveles_maximos = {}
    ahora = datetime.utcnow()

    for root, _, files in os.walk(EXTRACT_PATH):
        for file in files:
            if file.endswith(".geojson"):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for feature in data.get("features", []):
                        zona = feature["properties"].get("Nombre_zona", "Zona desconocida")
                        fecha_inicio = feature["properties"].get("Onset_PRP1", "")
                        fecha_expiracion = feature["properties"].get("Expire_PRP1", "")
                        
                        try:
                            inicio = datetime.fromisoformat(fecha_inicio) if fecha_inicio else None
                            expiracion = datetime.fromisoformat(fecha_expiracion) if fecha_expiracion else None
                        except ValueError:
                            continue
                        
from datetime import datetime, timezone

# Obtener la fecha y hora actual en UTC
ahora = datetime.utcnow().replace(tzinfo=timezone.utc)

niveles_maximos = {}

for root, _, files in os.walk(EXTRACT_PATH):
    for file in files:
        if file.endswith(".geojson"):
            with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                data = json.load(f)
                for feature in data.get("features", []):
                    zona = feature["properties"].get("Nombre_zona", "Zona desconocida")
                    fecha_inicio = feature["properties"].get("Onset_PRP1", "")
                    fecha_expiracion = feature["properties"].get("Expire_PRP1", "")

                    try:
                        inicio = datetime.fromisoformat(fecha_inicio).replace(tzinfo=timezone.utc) if fecha_inicio else None
                        expiracion = datetime.fromisoformat(fecha_expiracion).replace(tzinfo=timezone.utc) if fecha_expiracion else None
                    except ValueError:
                        print(f"⚠️ Error con las fechas en {zona}: {fecha_inicio} - {fecha_expiracion}")
                        continue  # Omitir si hay error en la fecha

                    # Depuración: Ver fechas
                    print(f"📅 {zona}: Inicio={inicio}, Expiración={expiracion}, Ahora={ahora}")

                    if inicio and expiracion:
                        if not (inicio <= ahora <= expiracion):
                            print(f"⏳ Omitiendo alerta de {zona}, no está activa ahora.")
                            continue  # Solo avisos activos en este momento

                    # Evaluar nivel de severidad
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

                    # Solo guardar si es el nivel más alto para la zona
                    if zona not in niveles_maximos or nivel > niveles_maximos[zona]:
                        niveles_maximos[zona] = nivel



                        
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

    for root, _, files in os.walk(EXTRACT_PATH):
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
                        fecha_inicio = feature["properties"].get("Onset_PRP1", "Sin fecha de inicio.")

                        feature["properties"]["description"] = (
                            f"<b>Resumen:</b> {resumido}<br>"
                            f"<b>Descripción:</b> {descripcion}<br>"
                            f"<b>Fecha de inicio:</b> {feature['properties'].get('Onset_PRP1', 'N/A')}<br>"
                            f"<b>Fecha de expiración:</b> {feature['properties'].get('Expire_PRP1', 'N/A')}<br>"
                            f"<b>Zona:</b> {zona}<br>"
                            f"<b>⚠️ Advertencia:</b> {mensaje_advertencia}"
                        )

                        feature["properties"].pop("style", None)
                        geojson_combinado["features"].append(feature)

    with open(SALIDA_GEOJSON, "w", encoding="utf-8") as f:
        json.dump(geojson_combinado, f, ensure_ascii=False, indent=4)
    print(f"✅ GeoJSON procesado y guardado en {SALIDA_GEOJSON}.")

if __name__ == "__main__":
    descargar_tar()
    extraer_tar()
    procesar_geojson()
