import os
import requests
import urllib.parse

key = os.environ.get("GRAPHHOPPER_API_KEY")
if not key:
    raise SystemExit("Falta definir la variable de entorno GRAPHHOPPER_API_KEY")

SALIDAS = ("s", "salir")
PERFILES = {"auto": "car", "bicicleta": "bike", "a pie": "foot",
            "car": "car", "bike": "bike", "foot": "foot"}
NOMBRE_PERFIL = {"car": "auto", "bike": "bicicleta", "foot": "a pie"}


def es_salida(texto):
    return texto.strip().lower() in SALIDAS


def pedir_ubicacion(mensaje):
    ubicacion = input(mensaje).strip()
    while ubicacion == "":
        ubicacion = input("No ingresó nada. " + mensaje).strip()
    return ubicacion


def geocodificar(ubicacion, key):
    url = "https://graphhopper.com/api/1/geocode?" + urllib.parse.urlencode(
        {"q": ubicacion, "limit": "1", "locale": "es", "key": key})
    respuesta = requests.get(url)
    json_data = respuesta.json()
    json_status = respuesta.status_code

    if json_status == 200 and len(json_data["hits"]) != 0:
        hit = json_data["hits"][0]
        lat = hit["point"]["lat"]
        lng = hit["point"]["lng"]
        partes = [p for p in (hit["name"], hit.get("state", ""), hit.get("country", "")) if p]
        nueva_ubicacion = ", ".join(partes)
        print("Ubicación encontrada: " + nueva_ubicacion +
              " (Tipo de ubicación: " + hit["osm_value"] + ")")
    else:
        lat = None
        lng = None
        nueva_ubicacion = ubicacion
        if json_status != 200:
            print("Estado de la API de geocodificación: " + str(json_status))
            print("Mensaje de error: " + str(json_data.get("message", "desconocido")))
        else:
            print("No se encontró la ubicación: " + ubicacion)
    return json_status, lat, lng, nueva_ubicacion


route_url = "https://graphhopper.com/api/1/route?"

while True:
    print("\n+++++++++++++++++++++++++++++++++++++++++++++")
    print("Perfiles de vehículo disponibles en Graphhopper:")
    print("+++++++++++++++++++++++++++++++++++++++++++++")
    print("auto, bicicleta, a pie")
    print("(Escriba 's' o 'salir' para terminar el programa)")
    print("+++++++++++++++++++++++++++++++++++++++++++++")
    entrada = input("Ingrese un perfil de vehículo de la lista anterior: ").strip().lower()
    if es_salida(entrada):
        break
    if entrada in PERFILES:
        vehicle = PERFILES[entrada]
    else:
        vehicle = "car"
        print("No se ingresó un perfil válido. Se usará el perfil auto.")

    loc1 = pedir_ubicacion("Ubicación de origen: ")
    if es_salida(loc1):
        break
    orig = geocodificar(loc1, key)

    loc2 = pedir_ubicacion("Destino: ")
    if es_salida(loc2):
        break
    dest = geocodificar(loc2, key)

    print("=================================================")
    if orig[1] is not None and dest[1] is not None:
        parametros = urllib.parse.urlencode({
            "key": key,
            "vehicle": vehicle,
            "locale": "es",
            "point": [str(orig[1]) + "," + str(orig[2]), str(dest[1]) + "," + str(dest[2])],
        }, doseq=True)
        paths_url = route_url + parametros
        respuesta = requests.get(paths_url)
        paths_status = respuesta.status_code
        paths_data = respuesta.json()
        print("Estado de la API de rutas: " + str(paths_status))
        print("=================================================")
        print("Indicaciones desde " + orig[3] + " hasta " + dest[3] +
              " en " + NOMBRE_PERFIL[vehicle])
        print("=================================================")

        if paths_status == 200:
            metros = paths_data["paths"][0]["distance"]
            km = metros / 1000
            millas = km / 1.61
            ms = paths_data["paths"][0]["time"]
            seg = int(ms / 1000 % 60)
            minutos = int(ms / 1000 / 60 % 60)
            horas = int(ms / 1000 / 60 / 60)
            print("Distancia recorrida: {0:.2f} millas / {1:.2f} km".format(millas, km))
            print("Duración del viaje: {0:02d}:{1:02d}:{2:02d}".format(horas, minutos, seg))
            print("=================================================")
            for paso in paths_data["paths"][0]["instructions"]:
                d = paso["distance"]
                print("{0} ( {1:.2f} km / {2:.2f} millas )".format(
                    paso["text"], d / 1000, d / 1000 / 1.61))
            print("=================================================")
        else:
            print("Mensaje de error: " + str(paths_data.get("message", "desconocido")))
            print("*************************************************")
    else:
        print("No se pudo calcular la ruta porque falló la geocodificación.")

print("Programa finalizado. ¡Hasta pronto!")