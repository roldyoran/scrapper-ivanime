# Author: roldyoran
# Date: 2025
# Description: Script para verificar actualizaciones de episodios de anime en ivanime.com
import requests
from bs4 import BeautifulSoup
from colorama import Fore
import datetime
import sqlite3
import os

# Configuración de la base de datos
DB_NAME = "anime_counters.db"

def init_db():
    """Inicializa la base de datos y crea la tabla si no existe"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS anime_counters (
        url TEXT PRIMARY KEY,
        anime_name TEXT NOT NULL,
        count INTEGER NOT NULL,
        last_checked TEXT
    )
    ''')
    
    conn.commit()
    conn.close()

def save_count(url, anime_name, count):
    """Guarda el contador para una URL específica con nombre de anime"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    current_date = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    cursor.execute('''
    INSERT OR REPLACE INTO anime_counters (url, anime_name, count, last_checked)
    VALUES (?, ?, ?, ?)
    ''', (url, anime_name, count, current_date))
    
    conn.commit()
    conn.close()
    
    print(f"\nContador guardado para {anime_name} hoy {current_date}\n")

def get_count(url):
    """Obtiene el contador para una URL específica"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('SELECT count FROM anime_counters WHERE url = ?', (url,))
    result = cursor.fetchone()
    
    conn.close()
    
    if result:
        return int(result[0])
    else:
        return 0

def request(url):
    """Realiza una petición HTTP a la URL"""
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        print(Fore.RED + f"Error {response.status_code}\n")
        return None

def main(url, anime_name):
    """Función principal que verifica los episodios disponibles"""
    htmlText = request(url)
    if not htmlText:
        return

    soup = BeautifulSoup(htmlText, "html.parser")

    # Search div with id qlt-1080p
    lista = soup.find_all('div', id="qlt-1080p")
    contador1080 = 0
    # print(lista[1])
    item = lista[0]
    
    todos_ep_lista = item.find('div', class_="episodios drv")
    sopa2 = BeautifulSoup(str(todos_ep_lista), "html.parser")
    episodios = sopa2.find_all('div', class_="ep no1")
    contador1080 = len(episodios)
    # print(f"Contador igual a {contador1080}")
    # print(item)
    
    count = get_count(url)
    
    if contador1080 > count:
        print(Fore.GREEN + f"    ---- NUEVO CAPITULO 1080p DISPONIBLE PARA {anime_name.upper()} ----") 
        print(f"Capitulos Totales al dia de Hoy {contador1080}\n")
        save_count(url, anime_name, contador1080)
    else:
        print(Fore.YELLOW + f"No hay nuevos capitulos 1080p para {anime_name}")
        print(f"Capitulos Totales a dia de Hoy {contador1080}\n")

def show_menu(anime_list):
    """Muestra el menú de opciones y obtiene la selección del usuario"""
    print(f"""{Fore.RESET}
    --------------------------------
        -- IVANIME 1080P --
    --------------------------------
        ** Script by roldyoran **
    --------------------------------
        ** STARTING SCRIPT **
    --------------------------------
    """)
    print("Selecciona una opción:")
    
    # Mostrar opciones de anime dinámicamente
    for i, anime_data in enumerate(anime_list.values(), start=1):
        print(f"{i}. {anime_data['name']}")
    
    # Opciones fijas
    last_option = len(anime_list) + 1
    print(f"{last_option}. Mostrar historial completo")
    print(f"{last_option + 1}. Salir")
    
    while True:
        choice = input(f"Ingresa tu elección (1-{last_option + 1}): ")
        if choice.isdigit() and 1 <= int(choice) <= last_option + 1:
            return choice
        print(Fore.RED + f"Opción inválida. Por favor ingresa un número entre 1 y {last_option + 1}.")

def show_history():
    """Muestra el historial de todas las URLs monitoreadas"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT anime_name, url, count, last_checked 
    FROM anime_counters 
    ORDER BY last_checked DESC
    ''')
    results = cursor.fetchall()
    
    conn.close()
    
    if not results:
        print(Fore.YELLOW + "\nNo hay registros en el historial\n")
        return
    
    print("\n" + Fore.CYAN + "HISTORIAL COMPLETO".center(60, '-') + Fore.RESET)
    for anime_name, url, count, last_checked in results:
        print(f"\nAnime: {Fore.MAGENTA}{anime_name}{Fore.RESET}")
        print(f"URL: {url}")
        print(f"Último conteo: {Fore.GREEN}{count}{Fore.RESET} episodios")
        print(f"Última verificación: {last_checked}")
    print("\n" + Fore.CYAN+  "-"*60 + Fore.RESET + "\n")

if __name__ == "__main__":
    # Inicializar la base de datos
    init_db()
    
    # Definir las URLs disponibles con sus nombres
    anime_list = {
        '1': {
            'name': "To be Hero X",
            'url': "https://www.ivanime.com/paste/2031576/"
        },
        '2': {
            'name': "Fire Force",
            'url': "https://www.ivanime.com/paste/3031564/"
        }
        # Puedes agregar más animes aquí simplemente añadiendo más entradas
        # El formato es: 'número': {'name': "Nombre del Anime", 'url': "URL"}
    }
    
    while True:
        choice = show_menu(anime_list)
        choice_int = int(choice)
        total_animes = len(anime_list)
        
        if choice_int == total_animes + 2:  # Opción Salir
            print(Fore.YELLOW + "Saliendo del script...")
            break
        elif choice_int == total_animes + 1:  # Opción Historial
            show_history()
        else:
            selected = anime_list[choice]
            print(f"\n{Fore.CYAN}Verificando actualizaciones para {selected['name']}...{Fore.RESET}")
            main(selected['url'], selected['name'])
        
        # Preguntar si quiere realizar otra acción
        another = input("\n¿Deseas realizar otra acción? (s/n): ").lower()
        if another != 's':
            print(Fore.YELLOW + "Saliendo del script...")
            break