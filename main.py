import sys
import requests
from io import BytesIO
from PIL import Image
import math

# Ключи API
GEOCODER_API_KEY = "ваш_ключ_геокодера"
SEARCH_API_KEY = "ваш_ключ_поиска_по_организациям"
STATIC_MAPS_API_KEY = "ваш_ключ_static_maps"

# Функция для получения координат по адресу
def get_coordinates(address):
    geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"
    geocoder_params = {
        "apikey": GEOCODER_API_KEY,
        "geocode": address,
        "format": "json",
    }
    response = requests.get(geocoder_api_server, params=geocoder_params)
    if not response:
        raise Exception("Ошибка запроса к геокодеру")

    json_response = response.json()
    toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
    toponym_coordinates = toponym["Point"]["pos"]
    return list(map(float, toponym_coordinates.split(" ")))

# Функция для поиска ближайшей аптеки
def find_nearest_pharmacy(coords):
    search_api_server = "https://search-maps.yandex.ru/v1/"
    search_params = {
        "apikey": SEARCH_API_KEY,
        "text": "аптека",
        "lang": "ru_RU",
        "ll": f"{coords[0]},{coords[1]}",
        "type": "biz",
        "results": 1,  # Ищем только одну ближайшую аптеку
    }
    response = requests.get(search_api_server, params=search_params)
    if not response:
        raise Exception("Ошибка запроса к API поиска по организациям")

    json_response = response.json()
    if not json_response["features"]:
        raise Exception("Аптеки не найдены")

    organization = json_response["features"][0]
    org_name = organization["properties"]["CompanyMetaData"]["name"]
    org_address = organization["properties"]["CompanyMetaData"]["address"]
    org_hours = organization["properties"]["CompanyMetaData"].get("Hours", {}).get("text", "Время работы не указано")
    org_coords = organization["geometry"]["coordinates"]
    return {
        "name": org_name,
        "address": org_address,
        "hours": org_hours,
        "coords": org_coords,
    }

# Функция для расчета расстояния между двумя точками (в км)
def calculate_distance(coord1, coord2):
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    radius = 6371  # Радиус Земли в км
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) * math.sin(dlon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c

# Функция для отображения карты с двумя точками
def show_map(coord1, coord2):
    map_api_server = "https://static-maps.yandex.ru/1.x"
    map_params = {
        "l": "map",
        "pt": f"{coord1[0]},{coord1[1]},pm2rdl~{coord2[0]},{coord2[1]},pm2grl",  # Точки: красная и зеленая
        "apikey": STATIC_MAPS_API_KEY,
    }
    response = requests.get(map_api_server, params=map_params)
    if not response:
        raise Exception("Ошибка запроса к StaticMapsAPI")

    image = Image.open(BytesIO(response.content))
    image.show()

# Основная функция
def main():
    if len(sys.argv) < 2:
        print("Использование: python main.py <адрес>")
        return

    address = " ".join(sys.argv[1:])
    print(f"Исходный адрес: {address}")

    try:
        # Получаем координаты исходного адреса
        address_coords = get_coordinates(address)
        print(f"Координаты адреса: {address_coords}")

        # Ищем ближайшую аптеку
        pharmacy = find_nearest_pharmacy(address_coords)
        print("\nНайдена аптека:")
        print(f"Название: {pharmacy['name']}")
        print(f"Адрес: {pharmacy['address']}")
        print(f"Время работы: {pharmacy['hours']}")

        # Рассчитываем расстояние
        distance = calculate_distance(address_coords, pharmacy["coords"])
        print(f"Расстояние до аптеки: {distance:.2f} км")

        # Показываем карту
        show_map(address_coords, pharmacy["coords"])

    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()
