# Author: roldyoran
# Oshi-no-ko: https://www.ivanime.com/paste/3425829/
import requests
from bs4 import BeautifulSoup
from colorama import Fore
import datetime



def saveCount1080(count):
    with open("count1080.txt", "w") as file:
        file.write(str(count))
    # get date in day/month/year
    date = datetime.datetime.now().strftime("%d/%m/%Y")
    print(f"\nContador guardado en count1080.txt hoy {date}\n")


def main():

    url = "https://www.ivanime.com/paste/3425829/"

    response = requests.get(url)

    if response.status_code == 200:
        # print("Todo bien")
        soup = BeautifulSoup(response.text, "html.parser")

        # Search div with id qlt-1080p
        lista = soup.find_all('div', id="qlt-1080p")
        contador1080 = 0
        for item in lista:
            todos_ep_lista = item.find('div', class_="episodios drv")
            sopa2 = BeautifulSoup(str(todos_ep_lista), "html.parser")
            episodios = sopa2.find_all('div', class_="ep no1")
            contador1080 = len(episodios)
            # span_ultimo_ep = (episodios[-1].find_all('span'))
            ultimo_ep = episodios[-1].find('a')
            print(f"Ultimo Capitulo link 1080p: {ultimo_ep['href']}")
        

        # Get count from file count1080.txt
        count = 0
        # add try if not exist file count1080.txt   
        try:
            with open("count1080.txt", "r") as file:
                count = file.read()
                count = int(count)
        except FileNotFoundError:
            with open("count1080.txt", "w") as file:
                file.write("0")
                count = 0   
        
        if contador1080 > count:
            print(Fore.GREEN + "    ----NUEVO CAPITULO 1080p DISPONIBLE----") 
            print("Capitulos Totales al dia de Hoy", contador1080)

            saveCount1080(contador1080) 
        else:
            print(Fore.RED + "No hay nuevos capitulos 1080p")
            print(f"Capitulos Totales al dia de Hoy {contador1080}\n")

    else:
        print("Error", response.status_code)




if __name__ == "__main__":
    print("""
    --------------------------------
        -- IVANIME 1080P --
    --------------------------------
        -- Oshi-no-ko --
    --------------------------------
        -- https://www.ivanime.com/paste/3425829/ --
    --------------------------------
        ** Script by roldyoran **
    --------------------------------
        ** STARTING SCRIPT **
    --------------------------------
    """)
    main()