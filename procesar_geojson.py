
import json
import os
import shutil
import requests
import tarfile

# Definir la variable para forzar actualización
FORZAR_ACTUALIZACION = True  # Puedes cambiarlo a False si no quieres forzar

# Leer configuración desde config.json
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

def descargar_tar():
    """Descarga el archivo tar.gz de la URL especificada en `config.json`."""
    try:
        response = requests.get(URL_TAR)
        response.raise_for_status()
        
        # Crear la carpeta 'datos/' si no existe
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
    """Combina y colorea los archivos GeoJSON con el formato correcto para uMap."""
    geojson_combinado = {"type": "FeatureCollection", "features": []}
    niveles_maximos = {}

    def formatear_fecha(fecha):
        """Convierte una fecha ISO en formato DD-MM-YY HH:MM o devuelve 'Desconocida' si es inválida."""
        try:
            dt = datetime.fromisoformat(fecha)
            return dt.strftime("%d-%m-%y %H:%M")
        except (ValueError, TypeError):
            return "Desconocida"
    
    def obtener_fecha_dt(fecha):
        """Convierte una fecha ISO a datetime o devuelve None si es inválida."""
        try:
            return datetime.fromisoformat(fecha)
        except (ValueError, TypeError):
            return None

    for root, _, files in os.walk(EXTRACT_PATH):
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
                            feature["properties"].get("Sev_NENV", "").lower(),
                            feature["properties"].get("Sev_VIRM", "").lower()
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
                        
                        # Solo procesar zonas con alertas (nivel_maximo > 0)
                        if nivel_maximo > 0:
                            color = None
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

                            alertas = []
                            if feature["properties"].get("Onset_PRP1"):
                                alertas.append({
                                    "resumen": feature["properties"].get("Resum_PRP1"),
                                    "descripcion": feature["properties"].get("Des_PRP1"),
                                    "inicio": obtener_fecha_dt(feature["properties"].get("Onset_PRP1")),
                                    "fin": obtener_fecha_dt(feature["properties"].get("Expire_PRP1"))
                                })
                            if feature["properties"].get("Onset_PRP2"):
                                alertas.append({
                                    "resumen": feature["properties"].get("Resum_PRP2"),
                                    "descripcion": feature["properties"].get("Des_PRP2"),
                                    "inicio": obtener_fecha_dt(feature["properties"].get("Onset_PRP2")),
                                    "fin": obtener_fecha_dt(feature["properties"].get("Expire_PRP2"))
                                })
                            if feature["properties"].get("Onset_NENV"):
                                alertas.append({
                                    "resumen": feature["properties"].get("Resum_NENV"),
                                    "descripcion": feature["properties"].get("Des_NENV"),
                                    "inicio": obtener_fecha_dt(feature["properties"].get("Onset_NENV")),
                                    "fin": obtener_fecha_dt(feature["properties"].get("Expire_NENV"))
                                })
                            
                            alertas_ordenadas = sorted(alertas, key=lambda x: x["inicio"] if x["inicio"] else datetime.max)
                            
                            description_parts = []
                            for alerta in alertas_ordenadas:
                                if alerta["resumen"]:
                                    description_parts.append(f"<b>Resumen:</b> {alerta['resumen']}<br>")
                                if alerta["descripcion"]:
                                    description_parts.append(f"<b>Descripción:</b> {alerta['descripcion']}<br>")
                                if alerta["inicio"]:
                                    description_parts.append(f"<b>Fecha de inicio:</b> {alerta['inicio'].strftime('%d-%m-%y %H:%M')}<br>")
                                if alerta["fin"]:
                                    description_parts.append(f"<b>Fecha de expiración:</b> {alerta['fin'].strftime('%d-%m-%y %H:%M')}<br><br>")
                            description_parts.append(f"<b>Zona:</b> {zona}<br><br>")
                            description_parts.append(f"<b>⚠️ Advertencia:</b> {mensaje_advertencia}")

                            feature["properties"]["description"] = "".join(description_parts)

                            feature["properties"].pop("style", None)
                            geojson_combinado["features"].append(feature)

    with open(SALIDA_GEOJSON, "w", encoding="utf-8") as f:
        json.dump(geojson_combinado, f, ensure_ascii=False, indent=4)
    print(f"✅ GeoJSON procesado y guardado en {SALIDA_GEOJSON}.")


if __name__ == "__main__":
    descargar_tar()
    extraer_tar()
    procesar_geojson()
