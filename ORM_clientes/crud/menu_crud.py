# Archivo: crud/menu_crud.py

from sqlalchemy.orm import Session
from models import Menu, Ingrediente, MenuIngrediente
from . import ingrediente_crud 
from sqlalchemy.exc import IntegrityError

# --- Funciones de LECTURA (Read) ---

def leer_menu_por_id(db: Session, menu_id: int):
    return db.query(Menu).filter(Menu.id == menu_id).first()

def leer_menu_por_nombre(db: Session, nombre: str):
    return db.query(Menu).filter(Menu.nombre == nombre).first()

def leer_todos_los_menus(db: Session):
    return db.query(Menu).all()

# --- Función de CREACIÓN (Create) ---

def crear_menu(db: Session, nombre: str, descripcion: str, precio: float, receta: list = None):
    """
    Crea un nuevo menú. Si se pasa una receta (lista de dicts), también crea las asociaciones.
    """
    # Validacion basica
    if precio <= 0:
        return "Error: El precio debe ser positivo."
        
    if leer_menu_por_nombre(db, nombre):
        return f"Error: El menú '{nombre}' ya existe."

    try:
        # 1. Crear el objeto Menu
        db_menu = Menu(
            nombre=nombre.strip().title(),
            descripcion=descripcion.strip(),
            precio=precio
        )
        db.add(db_menu)
        
        # 2. Asociar ingredientes si vienen en la receta
        if receta:
            for item in receta:
                ingrediente_id = item['ingrediente_id']
                cantidad = item['cantidad']
                
                db_ingrediente = ingrediente_crud.obtener_ingrediente_por_id(db, ingrediente_id)
                if not db_ingrediente:
                    raise Exception(f"Ingrediente ID {ingrediente_id} no encontrado.")
                
                if cantidad <= 0:
                    raise Exception(f"Cantidad inválida para ingrediente {db_ingrediente.nombre}")

                asoc = MenuIngrediente(menu=db_menu, ingrediente=db_ingrediente, cantidad=cantidad)
                db.add(asoc)
        
        db.commit()
        db.refresh(db_menu)
        return db_menu

    except Exception as e:
        db.rollback()
        return f"Error al crear menú: {e}"

# --- Funciones de ACTUALIZACION (Update) ---

# Archivo: crud/menu_crud.py
# (Mantén las importaciones y las funciones de leer/crear/eliminar como estaban)
# SOLO REEMPLAZA O AÑADE ESTA FUNCIÓN DE ACTUALIZACIÓN:

def actualizar_menu_completo(db: Session, menu_id: int, nombre: str, descripcion: str, precio: float, nueva_receta: list):
    """
    Actualiza un menú y REEMPLAZA su receta completa.
    """
    # 1. Buscar el menú
    db_menu = leer_menu_por_id(db, menu_id)
    if not db_menu:
        return f"Error: Menú ID {menu_id} no encontrado."

    if precio <= 0:
        return "Error: El precio debe ser positivo."

    try:
        # 2. Actualizar datos básicos
        db_menu.nombre = nombre.strip().title()
        db_menu.descripcion = descripcion.strip()
        db_menu.precio = precio

        # 3. ACTUALIZAR LA RECETA (La parte difícil)
        # Estrategia: Borramos todas las asociaciones viejas y creamos las nuevas.
        
        # Borrar ingredientes actuales de este menú
        db.query(MenuIngrediente).filter(MenuIngrediente.menu_id == menu_id).delete()
        
        # Agregar los nuevos ingredientes (si hay)
        if nueva_receta:
            for item in nueva_receta:
                ing_id = item['ingrediente_id']
                cant = item['cantidad']
                
                db_ing = ingrediente_crud.obtener_ingrediente_por_id(db, ing_id)
                if not db_ing:
                    raise Exception(f"Ingrediente ID {ing_id} no existe.")
                
                # Crear nueva asociación
                nuevo_item = MenuIngrediente(menu=db_menu, ingrediente=db_ing, cantidad=cant)
                db.add(nuevo_item)

        db.commit()
        db.refresh(db_menu)
        return db_menu

    except Exception as e:
        db.rollback()
        return f"Error al actualizar menú: {e}"
    
def eliminar_menu(db: Session, menu_id: int):
    db_menu = leer_menu_por_id(db, menu_id)
    if not db_menu:
        return False
        
    try:
        # SQLAlchemy borrará las asociaciones MenuIngrediente automáticamente
        # Pero debemos verificar si está en pedidos (pendiente)
        db.delete(db_menu)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error al eliminar menu: {e}")
        return False

# --- Función para Añadir Receta a un Menú Existente ---

def crear_receta_existente(db: Session, menu_id: int, receta: list):
    """
    Añade ingredientes a un menú que YA existe.
    """
    try:
        db_menu = leer_menu_por_id(db, menu_id)
        if not db_menu:
            return "Error: Menú no encontrado."
            
        # Si ya tiene receta, no hacemos nada (para evitar duplicados en la carga masiva)
        if db_menu.items_receta: 
             return "Advertencia: El menú ya tiene una receta asignada."

        for item in receta:
            ing_id = item['ingrediente_id']
            cant = item['cantidad']
            
            db_ing = ingrediente_crud.obtener_ingrediente_por_id(db, ing_id)
            if not db_ing:
                 raise Exception(f"Ingrediente ID {ing_id} no encontrado")

            asoc = MenuIngrediente(menu=db_menu, ingrediente=db_ing, cantidad=cant)
            db.add(asoc)

        db.commit()
        return db_menu

    except Exception as e:
        db.rollback()
        return f"Error al añadir receta: {e}"