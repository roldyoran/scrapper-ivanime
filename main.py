from database import init_db, save_count, get_count, get_history
from scraper import request, get_episode_count
from ui import show_menu, show_history, show_update_result
from colorama import Fore

# Definir las URLs disponibles con sus nombres
ANIME_LIST = {
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

def check_updates(url, anime_name):
    """Verifica si hay actualizaciones para un anime específico"""
    html_text = request(url)
    if not html_text:
        return

    current_count = get_episode_count(html_text)
    previous_count = get_count(url)
    
    show_update_result(anime_name, current_count, previous_count)
    
    if current_count > previous_count:
        save_count(url, anime_name, current_count)

def main():
    """Función principal del programa"""
    # Inicializar la base de datos
    init_db()
    
    while True:
        choice = show_menu(ANIME_LIST)
        choice_int = int(choice)
        total_animes = len(ANIME_LIST)
        
        if choice_int == total_animes + 2:  # Opción Salir
            print(Fore.YELLOW + "Saliendo del script...")
            break
        elif choice_int == total_animes + 1:  # Opción Historial
            history_data = get_history()
            show_history(history_data)
        else:
            selected = ANIME_LIST[choice]
            print(f"\n{Fore.CYAN}Verificando actualizaciones para {selected['name']}...{Fore.RESET}")
            check_updates(selected['url'], selected['name'])
        
        # Preguntar si quiere realizar otra acción
        another = input("\n¿Deseas realizar otra acción? (s/n): ").lower()
        if another != 's':
            print(Fore.YELLOW + "Saliendo del script...")
            break

if __name__ == "__main__":
    main()