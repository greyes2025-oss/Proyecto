from sqlalchemy.orm import Session
from models import Menu, Ingrediente, MenuIngrediente
from . import ingrediente_crud # Importamos el CRUD de ingredientes para validaciones
from sqlalchemy.exc import IntegrityError

# --- Funciones de LECTURA (Read) ---

def leer_menu_por_id(db: Session, menu_id: int):
    """
    Busca un menu por su ID.
    """
    return db.query(Menu).filter(Menu.id == menu_id).first()

def leer_menu_por_nombre(db: Session, nombre: str):
    """
    Busca un menu por su nombre.
    """
    return db.query(Menu).filter(Menu.nombre == nombre).first()

def leer_todos_los_menus(db: Session):
    """
    Devuelve una lista de todos los menus.
    """
    return db.query(Menu).all()

# --- Función de CREACIÓN (Create) ---

def crear_menu(db: Session, nombre: str, descripcion: str, precio: float, receta: list):
    """
    Crea un nuevo menu y sus asociaciones con ingredientes.
    receta debe ser una lista de dicts:
    [
        {"ingrediente_id": 1, "cantidad": 1},  # Ej: 1 vienesa
        {"ingrediente_id": 5, "cantidad": 0.5} # Ej: 0.5 palta
    ]
    """
    
    # Validacion: nombre de menu unico
    if leer_menu_por_nombre(db, nombre):
        print(f"Error: El menu '{nombre}' ya existe.")
        return None
    
    # Validacion: precio positivo
    if precio <= 0:
        print("Error: El precio debe ser un numero positivo.")
        return None
        
    try:
        # 1. Crear el objeto Menu principal
        db_menu = Menu(
            nombre=nombre.strip().title(),
            descripcion=descripcion.strip(),
            precio=precio
        )
        db.add(db_menu)
        
        # 2. Asociar los ingredientes de la receta
        if not receta:
            raise Exception("La receta no puede estar vacia.")

        for item in receta:
            ingrediente_id = item['ingrediente_id']
            cantidad_requerida = item['cantidad']
            
            # Validacion: El ingrediente existe en la BD?
            db_ingrediente = ingrediente_crud.obtener_ingrediente_por_id(db, ingrediente_id) # (Asume que esta funcion existe en ingrediente_crud.py)
            if not db_ingrediente:
                raise Exception(f"El ingrediente con ID {ingrediente_id} no existe.")
            
            # Validacion: Cantidad positiva
            if cantidad_requerida <= 0:
                raise Exception(f"La cantidad para el ingrediente ID {ingrediente_id} debe ser positiva.")
                
            # 3. Crear el Objeto de Asociacion (MenuIngrediente)
            db_menu_ingrediente = MenuIngrediente(
                menu=db_menu, # Asocia con el menu que acabamos de crear
                ingrediente=db_ingrediente, # Asocia con el ingrediente encontrado
                cantidad=cantidad_requerida
            )
            db.add(db_menu_ingrediente)

        # 4. Guardar todo (Menu y Asociaciones) en la BD
        db.commit()
        db.refresh(db_menu)
        print(f"Menu '{db_menu.nombre}' creado con exito.")
        return db_menu

    except IntegrityError as e:
        db.rollback() # Revertir todo si algo falla
        print(f"Error de integridad al crear menu (nombre duplicado?): {e}")
        return None
    except Exception as e:
        db.rollback() # Revertir todo si algo falla
        print(f"Error al crear menu: {e}")
        return None

# --- Funciones de ACTUALIZACION (Update) ---

def actualizar_menu(db: Session, menu_id: int, nombre: str, descripcion: str, precio: float):
    """
    Actualiza los datos basicos de un menu (no su receta).
    """
    db_menu = leer_menu_por_id(db, menu_id)
    if not db_menu:
        print(f"Error: Menu con ID {menu_id} no encontrado.")
        return None
    
    try:
        db_menu.nombre = nombre.strip().title()
        db_menu.descripcion = descripcion.strip()
        db_menu.precio = precio
        db.commit()
        db.refresh(db_menu)
        print(f"Menu '{db_menu.nombre}' actualizado con exito.")
        return db_menu
    except Exception as e:
        db.rollback()
        print(f"Error al actualizar menu: {e}")
        return None

# --- Función de ELIMINACION (Delete) ---

def eliminar_menu(db: Session, menu_id: int):
    """
    Elimina un menu y sus asociaciones en la tabla MenuIngrediente.
    (Falta validacion de si esta en un pedido)
    """
    db_menu = leer_menu_por_id(db, menu_id)
    if not db_menu:
        print(f"Error: Menu con ID {menu_id} no encontrado.")
        return False 
    try:
        db.delete(db_menu)
        db.commit()
        print(f"Menu '{db_menu.nombre}' eliminado con exito.")
        return True
    except Exception as e:
        db.rollback()
        print(f"Error al eliminar menu: {e}")
        return False