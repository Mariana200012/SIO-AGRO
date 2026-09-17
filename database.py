import sqlite3
import os

DATABASE = 'Bd_SIO-AGRO.db' 

def get_db_connection():
    # Buscamos la ruta absoluta para que no haya pierde
    base_dir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(base_dir, DATABASE)
    
    # 1. Este print te dirá en la terminal EXACTAMENTE qué ruta está abriendo
    print(f"\n[BD INFO] Intentando abrir: {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # 2. Este print te listará las tablas que realmente existen en ese archivo
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tablas = cursor.fetchall()
    print(f"[BD INFO] Tablas encontradas: {[t['name'] for t in tablas]}\n")
    
    return conn