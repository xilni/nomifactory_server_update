import os
import shutil
from zipfile import ZipFile

import requests
import tqdm
from bs4 import BeautifulSoup


# Config, adjust these to your liking

NOMIFACTORY_NIGHTLY_URL = "https://nightly.link/Nomifactory/Nomifactory/workflows/nightly/dev"
NOMIFACTORY_DIRECTORY = "/home/minecraft/servers/nomifactory"
NOMIFACTORY_OLD_DIRECTORY = f"{NOMIFACTORY_DIRECTORY}_old"
SERVER_FILES_TO_COPY = [
    "server.properties",
    "eula.txt",
    "ops.json",
    "white-list.json",
    "banned-ips.json",
    "banned-players.json",
    "world"
]


# Do not modify below this line

def archive_existing_nomifactory(original_directory: str, archive_directory: str) -> bool:
    """Archives existing nomifactory directory to nomifactory_old directory.

    Returns:
        bool: Returns True on success, else false
    """

    if not os.path.exists(original_directory):
        print("No nomifactory directory found to archive")
        return False

    print(f"Preserving existing nomifactory directory ({original_directory}) as {archive_directory}")
    if os.path.exists(archive_directory):
        print("Old directory of nomifactory already exists. Deleting old directory")
        shutil.rmtree(archive_directory)

    print("Moving nomifactory directory to nomifactory_old directory")
    shutil.move(original_directory, archive_directory)

    return True

def get_server_nightly_url() -> str:
    """Gets the latest nightly url from nomifactory nightly server.

    Returns:
        str: Returns the nightly url
    """

    r = requests.get(NOMIFACTORY_NIGHTLY_URL)
    soup = BeautifulSoup(r.text, "html.parser")

    download_table = soup.find("table")
    server_row = download_table.find_all("tr")[3]
    url = server_row.find("td").find("a").get("href")
    print(f"Found latest nightly url: {url}")
    return url


def download_new_server_files(download_directory: str, file_url: str):
    """Downloads the latest nightly server zip from nomifactory nightly server.

    Args:
        download_directory (str): The directory to download the server zip to
        file_url (str): The url to download the server zip from
    """

    file_name = file_url.split("/")[-1]

    # Download the latest version of nomifactory
    response = requests.get(file_url, stream=True)
    total_size_in_bytes= int(response.headers.get('content-length', 0))
    block_size = 1024 #1 Kibibyte
    progress_bar = tqdm.tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
    with open(f"{download_directory}/{file_name}", "wb") as file:
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            file.write(data)

    progress_bar.close()
    if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
        print("ERROR, something went wrong with the download")


def install_new_server(directory: str, server_zip: str, old_server_directory: str = None):
    """Installs the specified server zip into the specified directory. Optionally copies over the old server files that are needed.

    Args:
        directory (str): The directory to install the server zip to
        server_zip (str): The server zip to install
        old_server_directory (str, optional): The old server directory to copy files from. Defaults to None.
    """
    print("Unzipping server zip")
    with ZipFile(server_zip, 'r') as zipObj:
        zipObj.extractall(directory)

    if old_server_directory and os.path.exists(old_server_directory):
        print("Copying over essentials from old server directory")
        for file in SERVER_FILES_TO_COPY:
            if os.path.exists(f"{old_server_directory}/{file}"):
                print(f"Copying {old_server_directory}/{file} to {directory}/{file}")
                shutil.copy(f"{old_server_directory}/{file}", f"{directory}/{file}")


if __name__ == "__main__":
    archive_existing_nomifactory(NOMIFACTORY_DIRECTORY, NOMIFACTORY_OLD_DIRECTORY)

    nightly_url = get_server_nightly_url()
    print("Downloading server zip")
    os.makedirs(NOMIFACTORY_DIRECTORY)
    download_new_server_files(NOMIFACTORY_DIRECTORY, nightly_url)

    print("Installing server")
    install_new_server(NOMIFACTORY_DIRECTORY, f"{NOMIFACTORY_DIRECTORY}/{nightly_url.split('/')[-1]}", NOMIFACTORY_OLD_DIRECTORY)

    print("Please restart nomifactory server")
