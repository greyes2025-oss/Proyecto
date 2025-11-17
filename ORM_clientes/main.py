# main.py - Código actualizado para la inicialización y carga de datos predefinidos

from database import SessionLocal, engine, Base
import models 
import crud.ingrediente_crud as icrud
import crud.menu_crud as mcrud
from sqlalchemy.orm import Session 
import os 

# Importamos la aplicación para iniciarla al final
import app 


def inicializar_bd():
    """Crea las tablas en la BD (si no existen)"""
    Base.metadata.create_all(bind=engine)
    print("--- Tablas de la base de datos verificadas/creadas con éxito. ---")

def get_db_session() -> Session:
    """Proporciona una sesión de BD para la inicialización."""
    db = SessionLocal()
    return db

# main.py (Función CORREGIDA)

def cargar_datos_iniciales():
    """
    Función vaciada. Los menús e ingredientes se cargan 100% 
    desde la interfaz de usuario (CSV y 'Crear Recetas').
    """
    db = get_db_session()
    
    # Comprobar si ya hay menús o ingredientes
    if mcrud.leer_todos_los_menus(db) or icrud.listar_ingredientes(db):
        db.close()
        print("La base de datos ya tiene datos. Saltando carga inicial.")
        return

    db.close()
    print("Base de datos lista. El inventario está vacío.")

# --- Ejecución Principal ---
if __name__ == "__main__":
    inicializar_bd()
    cargar_datos_iniciales()
    
    # Inicia la interfaz gráfica
    app_instance = app.RestauranteApp()
    app_instance.mainloop()