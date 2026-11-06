"""
Script de reinicio total de base de datos para producción.
Borra todas las tablas, recrea el esquema public y ejecuta el semillero inicial
dejando únicamente el Super Administrador y los 43 trabajadores del Excel oficial.
"""

from sqlalchemy import text
from app.database.connection import engine
from app.database.seed import init_db


def reiniciar_base_de_datos():
    print("=================================================================")
    print("REINICIO DE BASE DE DATOS - SISTEMAS RAÍCES")
    print("=================================================================")
    print("1. Eliminando todas las tablas anteriores (DROP SCHEMA public CASCADE)...")
    
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE;"))
        conn.execute(text("CREATE SCHEMA public;"))
        conn.commit()

    print("2. Recreando tablas y sembrando datos oficiales...")
    init_db()

    print("=================================================================")
    print("¡Base de datos reiniciada con éxito!")
    print("- Super Administrador: juanpablovacacarvalho@gmail.com")
    print("- 43 Trabajadores del Excel cargados limpiamente.")
    print("- Tablas de anticipos, liquidaciones, inventario y bitácora vacías y listas.")
    print("=================================================================")


if __name__ == "__main__":
    reiniciar_base_de_datos()

