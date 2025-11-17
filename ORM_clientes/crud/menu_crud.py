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
# menu_crud.py (Función 'crear_menu' CORREGIDA)

# menu_crud.py (Función 'crear_menu' CORREGIDA)

def crear_menu(db: Session, nombre: str, descripcion: str, precio: float, receta: list):
    """
    Crea un nuevo menú. Si la receta está vacía, solo crea el menú.
    Si la receta tiene items, los asocia.
    """
    
    if leer_menu_por_nombre(db, nombre) or precio <= 0:
        print(f"Error: Menu '{nombre}' ya existe o precio es inválido.")
        return None
        
    from . import ingrediente_crud 
    from models import Menu, MenuIngrediente 

    try:
        # 1. Crear el objeto Menu principal
        db_menu = Menu(
            nombre=nombre.strip().title(), 
            descripcion=descripcion.strip(), 
            precio=precio
        )
        db.add(db_menu)
        
        # 2. Asociar los ingredientes (SOLO SI LA RECETA NO ESTÁ VACÍA)
        # ESTA ES LA CORRECCIÓN: Quitamos el 'if not receta: raise Exception'
        if receta: 
            for item in receta:
                ingrediente_id = item['ingrediente_id']
                cantidad_requerida = item['cantidad']
                
                db_ingrediente = ingrediente_crud.obtener_ingrediente_por_id(db, ingrediente_id)
                
                if not db_ingrediente or cantidad_requerida <= 0:
                    raise Exception(f"Ingrediente ID {ingrediente_id} inválido o cantidad negativa.")
                    
                db_menu_ingrediente = MenuIngrediente(
                    menu=db_menu, 
                    ingrediente=db_ingrediente, 
                    cantidad=cantidad_requerida
                )
                db.add(db_menu_ingrediente)

        # 3. Guardar (el menú solo, o el menú + la receta)
        db.commit()
        db.refresh(db_menu)
        return db_menu

    except Exception as e:
        db.rollback()
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
    

# menu_crud.py (Añadir esta función)

def crear_receta_existente(db: Session, menu_id: int, receta: list):
    """
    Función que crea las asociaciones MenuIngrediente para un menú que ya existe.
    receta: [{"ingrediente_id": ID, "cantidad": Cantidad}, ...]
    """
    from . import ingrediente_crud # Importación local

    try:
        db_menu = leer_menu_por_id(db, menu_id)
        if not db_menu:
            return "Error: Menú no encontrado."
            
        # 1. Si la receta ya existe (tiene ítems), la saltamos para evitar duplicados
        if db.query(MenuIngrediente).filter(MenuIngrediente.menu_id == menu_id).count() > 0:
            return "Advertencia: La receta ya existe para este menú."

        # 2. Crear las nuevas asociaciones
        for item in receta:
            ingrediente_id = item['ingrediente_id']
            cantidad_requerida = item['cantidad']
            
            db_ingrediente = ingrediente_crud.obtener_ingrediente_por_id(db, ingrediente_id)
            if not db_ingrediente or cantidad_requerida <= 0:
                raise Exception(f"Ingrediente ID {ingrediente_id} inválido o cantidad negativa.")
                
            db_menu_ingrediente = MenuIngrediente(
                menu=db_menu, 
                ingrediente=db_ingrediente, 
                cantidad=cantidad_requerida
            )
            db.add(db_menu_ingrediente)

        db.commit()
        return db_menu

    except Exception as e:
        db.rollback()
        return f"Error al crear receta: {e}"