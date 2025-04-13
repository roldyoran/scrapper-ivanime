import requests
from bs4 import BeautifulSoup
from colorama import Fore

def request(url):
    """Realiza una petición HTTP a la URL"""
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        print(Fore.RED + f"Error {response.status_code}\n")
        return None

def get_episode_count(html_text):
    """Extrae el conteo de episodios del HTML"""
    if not html_text:
        return 0

    soup = BeautifulSoup(html_text, "html.parser")

    # Search div with id qlt-1080p
    lista = soup.find_all('div', id="qlt-1080p")
    if not lista:
        return 0
        
    item = lista[0]
    
    todos_ep_lista = item.find('div', class_="episodios drv")
    if not todos_ep_lista:
        return 0
        
    sopa2 = BeautifulSoup(str(todos_ep_lista), "html.parser")
    episodios = sopa2.find_all('div', class_="ep no1")
    return len(episodios)