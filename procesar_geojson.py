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
    "Amarillo": "#FFFF00",
    "Naranja": "#FFA500",
    "Rojo": "#FF0000"
}

# Color por defecto si el nivel no está definido o es desconocido
DEFAULT_COLOR = "#808080"

def descargar_tar():
    try:
        response = requests.get(URL_TAR)
        response.raise_for_status()
        file_name = URL_TAR.split("/")[-1]
        with open(file_name, "wb") as f:
            f.write(response.content)
        print(f"✅ Archivo descargado: {file_name}")
        return file_name
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al descargar: {e}")
        return None

def extraer_tar(file_name):
    if not os.path.exists(CARPETA_TEMP):
        os.makedirs(CARPETA_TEMP)
    with tarfile.open(file_name, "r:gz") as tar:
        tar.extractall(CARPETA_TEMP)
    print(f"✅ Archivos extraídos a: {CARPETA_TEMP}")

def procesar_geojson():
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
                        nivel = max([("rojo" in niveles) * 3, ("naranja" in niveles) * 2, ("amarillo" in niveles) * 1], default=0)
                        niveles_maximos[zona] = max(nivel, niveles_maximos.get(zona, 0))

    for root, _, files in os.walk(CARPETA_TEMP):
        for file in files:
            if file.endswith(".geojson"):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for feature in data.get("features", []):
                        zona = feature["properties"].get("Nombre_zona", "Zona desconocida")
                        nivel_maximo = niveles_maximos.get(zona, 0)
                        color = COLORS.get(["Amarillo", "Naranja", "Rojo"][nivel_maximo-1], DEFAULT_COLOR) if nivel_maximo else DEFAULT_COLOR

                        descripcion = feature["properties"].get("Des_PRP1", "Sin descripción disponible.")
                        resumido = feature["properties"].get("Resum_PRP1", "Sin resumen disponible.")
                        fecha_expiracion = feature["properties"].get("Expire_PRP1", "Sin fecha de expiración.")
                        identificador = feature["properties"].get("Identf_PRP1", "Sin ID")
                        nombre_zona = feature["properties"].get("Nombre_zona", "Zona no disponible.")
                        
                        feature["properties"]["_umap_options"] = {
                            "color": "#000000",
                            "weight": 2,
                            "opacity": 1,
                            "fillOpacity": 0.3,
                            "dashArray": "1",
                            "fillColor": color,
                            "stroke": True,
                            "fill": True
                        }

                        feature["properties"]["description"] = f"""
                        <b>Zona:</b> {nombre_zona}<br>
                        <b>ID Aviso:</b> {identificador}<br>
                        <b>Resumen:</b> {resumido}<br>
                        <b>Descripción:</b> {descripcion}<br>
                        <b>Fecha de Expiración:</b> {fecha_expiracion}<br>
                        <b>Nivel Máximo:</b> {['Sin Aviso', 'Amarillo', 'Naranja', 'Rojo'][nivel_maximo]}<br>
                        """
                        
                        geojson_combinado["features"].append(feature)

    if os.path.exists(SALIDA_GEOJSON):
        os.remove(SALIDA_GEOJSON)
    
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
