import sqlite3
import datetime

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

def get_history():
    """Obtiene todo el historial de la base de datos"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT anime_name, url, count, last_checked 
    FROM anime_counters 
    ORDER BY last_checked DESC
    ''')
    results = cursor.fetchall()
    
    conn.close()
    return results