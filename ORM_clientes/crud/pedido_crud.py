# Archivo: crud/pedido_crud.py

from sqlalchemy.orm import Session
from models import Pedido, PedidoMenu, Menu, Ingrediente, Cliente
from . import cliente_crud, menu_crud, ingrediente_crud 
from datetime import datetime
from functools import reduce 
from sqlalchemy.exc import IntegrityError

# --- Funciones de LECTURA (Read) ---

def leer_pedido_por_id(db: Session, pedido_id: int):
    return db.query(Pedido).filter(Pedido.id == pedido_id).first()

def leer_pedidos_por_cliente(db: Session, cliente_id: int):
    return db.query(Pedido).filter(Pedido.cliente_id == cliente_id).all()

def leer_todos_los_pedidos(db: Session):
    return db.query(Pedido).order_by(Pedido.fecha.desc()).all()

# --- Función de CREACIÓN (Create) ---

def crear_pedido(db: Session, cliente_id: int, menus_pedido: list):
    """
    Crea un nuevo pedido, descuenta stock y calcula el total.
    """
    
    try:
        # 1. Validar Cliente
        db_cliente = cliente_crud.obtener_cliente_por_id(db, cliente_id)
        if not db_cliente:
            raise Exception("El cliente seleccionado no existe.")
            
        # 2. Validar que el pedido no este vacio
        if not menus_pedido:
            raise Exception("El pedido esta vacio.")

        lista_menus_obj = [] 
        
        # 3. Validar Menus
        for item in menus_pedido:
            menu_id = item['id']
            cantidad = item['cantidad']
            
            if cantidad <= 0:
                raise Exception(f"La cantidad para el menu ID {menu_id} debe ser positiva.")

            db_menu = menu_crud.leer_menu_por_id(db, menu_id)
            if not db_menu:
                raise Exception(f"El menu con ID {menu_id} no existe.")
            
            lista_menus_obj.append( (db_menu, cantidad) )

        # 4. Calcular Total (usando reduce)
        total_pedido = reduce(
            lambda acumulador, item: acumulador + (item[0].precio * item[1]),
            lista_menus_obj, 
            0 
        )

        # 5. Validar y Descontar Stock (Paso critico)
        for db_menu, cantidad_pedida in lista_menus_obj:
            # Iterar sobre la receta del menu
            for item_receta in db_menu.items_receta:
                db_ingrediente = item_receta.ingrediente
                cantidad_necesaria_total = item_receta.cantidad * cantidad_pedida
                
                # Validacion de stock
                if db_ingrediente.stock < cantidad_necesaria_total:
                    raise Exception(f"Stock insuficiente: Falta '{db_ingrediente.nombre}' (Tienes {db_ingrediente.stock}, necesitas {cantidad_necesaria_total})")
                
                # Descontar el stock
                db_ingrediente.stock -= cantidad_necesaria_total

        # 6. Crear el Pedido
        db_pedido = Pedido(
            cliente=db_cliente,
            fecha=datetime.now(), # <--- CORREGIDO: Se envia el objeto datetime directo
            total=total_pedido
        )
        db.add(db_pedido)
        
        # 7. Crear las asociaciones
        for db_menu, cantidad_pedida in lista_menus_obj:
            db_pedido_menu = PedidoMenu(
                pedido=db_pedido, 
                menu=db_menu,     
                cantidad=cantidad_pedida
            )
            db.add(db_pedido_menu)
            
        # 8. Guardar todo
        db.commit()
        db.refresh(db_pedido)
        print(f"Pedido ID {db_pedido.id} creado con exito.")
        return db_pedido
        
    except Exception as e:
        db.rollback() # Revertir todo si falla
        print(f"Error al crear pedido: {e}")
        raise e
    

def eliminar_pedido(db: Session, pedido_id: int):
    """
    Elimina un pedido por su ID.
    """
    pedido = leer_pedido_por_id(db, pedido_id)
    if not pedido:
        return False
    
    try:
        # Al borrar el pedido, SQLAlchemy borrará en cascada los items 
        # (si la relación está bien configurada) o los borrará manualmente.
        db.delete(pedido)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error al eliminar pedido: {e}")
        return False