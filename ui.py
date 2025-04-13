from colorama import Fore

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

def show_history(history_data):
    """Muestra el historial de todas las URLs monitoreadas"""
    if not history_data:
        print(Fore.YELLOW + "\nNo hay registros en el historial\n")
        return
    
    print("\n" + Fore.CYAN + "HISTORIAL COMPLETO".center(60, '-') + Fore.RESET)
    for anime_name, url, count, last_checked in history_data:
        print(f"\nAnime: {Fore.MAGENTA}{anime_name}{Fore.RESET}")
        print(f"URL: {url}")
        print(f"Último conteo: {Fore.GREEN}{count}{Fore.RESET} episodios")
        print(f"Última verificación: {last_checked}")
    print("\n" + Fore.CYAN + "-"*60 + Fore.RESET + "\n")

def show_update_result(anime_name, current_count, previous_count):
    """Muestra el resultado de la verificación de actualizaciones"""
    if current_count > previous_count:
        print(Fore.GREEN + f"    ---- NUEVO CAPITULO 1080p DISPONIBLE PARA {anime_name.upper()} ----") 
        print(f"Capitulos Totales al dia de Hoy {current_count}\n")
    else:
        print(Fore.YELLOW + f"No hay nuevos capitulos 1080p para {anime_name}")
        print(f"Capitulos Totales a dia de Hoy {current_count}\n")