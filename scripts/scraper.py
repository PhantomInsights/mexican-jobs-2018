"""
This module connnects to https://empleos.gob.mx and checks each state in Mexico for new listings.
The job listings are downloaded into their respective state folder.
"""

import os
import time
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

STATES_URLS = [
    "1-busqueda-de-ofertas-de-empleo-en-aguascalientes",
    "2-busqueda-de-ofertas-de-empleo-en-baja-california",
    "3-busqueda-de-ofertas-de-empleo-en-baja-california-sur",
    "4-busqueda-de-ofertas-de-empleo-en-campeche",
    "5-busqueda-de-ofertas-de-empleo-en-coahuila",
    "6-busqueda-de-ofertas-de-empleo-en-colima",
    "7-busqueda-de-ofertas-de-empleo-en-chiapas",
    "8-busqueda-de-ofertas-de-empleo-en-chihuahua",
    "9-busqueda-de-ofertas-de-empleo-en-ciudad-de-mexico",
    "10-busqueda-de-ofertas-de-empleo-en-durango",
    "11-busqueda-de-ofertas-de-empleo-en-guanajuato",
    "12-busqueda-de-ofertas-de-empleo-en-guerrero",
    "13-busqueda-de-ofertas-de-empleo-en-hidalgo",
    "14-busqueda-de-ofertas-de-empleo-en-jalisco",
    "15-busqueda-de-ofertas-de-empleo-en-mexico",
    "16-busqueda-de-ofertas-de-empleo-en-michoacan",
    "17-busqueda-de-ofertas-de-empleo-en-morelos",
    "18-busqueda-de-ofertas-de-empleo-en-nayarit",
    "19-busqueda-de-ofertas-de-empleo-en-nuevo-leon",
    "20-busqueda-de-ofertas-de-empleo-en-oaxaca",
    "21-busqueda-de-ofertas-de-empleo-en-puebla",
    "22-busqueda-de-ofertas-de-empleo-en-queretaro",
    "23-busqueda-de-ofertas-de-empleo-en-quintana-roo",
    "24-busqueda-de-ofertas-de-empleo-en-san-luis-potosi",
    "25-busqueda-de-ofertas-de-empleo-en-sinaloa",
    "26-busqueda-de-ofertas-de-empleo-en-sonora",
    "27-busqueda-de-ofertas-de-empleo-en-tabasco",
    "28-busqueda-de-ofertas-de-empleo-en-tamaulipas",
    "29-busqueda-de-ofertas-de-empleo-en-tlaxcala",
    "30-busqueda-de-ofertas-de-empleo-en-veracruz",
    "31-busqueda-de-ofertas-de-empleo-en-yucatan",
    "32-busqueda-de-ofertas-de-empleo-en-zacatecas"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:61.0) Gecko/20100101 Firefox/61.0"}

BASE_URL = "https://www.empleo.gob.mx"
ROOT_FOLDER = "./states/"
DELTA_HOURS = 0  # 0 for local time, 5 for Mexico Central Time.


def create_folders():
    """Creates folders that will contain the listings html files.
    Each folder is named after the state number (1 - 32).
    """

    for state in STATES_URLS:
        folder_path = ROOT_FOLDER + state.split("-")[0]
        os.makedirs(folder_path, exist_ok=True)


def download_state(state_url):
    """Checks for new listings on the specified url and downloads any new ones.

    Parameters
    ----------
    state_url : str
        The url part of the current state to download.

    """

    # We prepare the url to download and the folder path.
    state_listings_url = BASE_URL + "/" + state_url
    state_folder = ROOT_FOLDER + state_url.split("-")[0] + "/"
    print("Downloading:", state_listings_url)

    with main_session.get(state_listings_url, timeout=5) as response:

        soup = BeautifulSoup(response.text, "html.parser")

        # Only the anchor tags that contain 'detallesoferta' in the url are job listings.
        for link in soup.find("table").find_all("a"):
            if "detalleoferta" in link["href"]:

                listing_id = link["href"].split("=")[-1]
                file_name = listing_id + ".html"

                # If the job listing is not already saved we save it.
                if file_name not in os.listdir(state_folder):

                    listing_url = BASE_URL + link["href"]

                    with main_session.get(listing_url, timeout=5) as listing_response:

                        with open(state_folder + file_name, "w", encoding="utf-8") as temp_file:
                            temp_file.write(listing_response.text)
                            print("Successfully Saved:", file_name)
                            update_log(state_folder + file_name)
                            time.sleep(0.5)


def update_log(file_name):
    """Updates the log file with the file name and the current timestamp.

    Parameters
    ----------
    file_name : str
        The name of the file.

    """

    with open("log.txt", "a", encoding="utf-8") as temp_file:
        now = datetime.now() - timedelta(hours=DELTA_HOURS)
        temp_file.write("{},{}\n".format(file_name, now))


if __name__ == "__main__":

    create_folders()

    # Using a session greatly reduces timeouts and other errors.
    main_session = requests.Session()
    main_session.headers.update(HEADERS)
    main_session.mount(
        "https://", requests.adapters.HTTPAdapter(max_retries=3))

    for state in STATES_URLS:
        download_state(state)
        time.sleep(0.5)
