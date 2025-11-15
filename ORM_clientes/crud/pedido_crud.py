from sqlalchemy.orm import Session
from models import Pedido, PedidoMenu, Menu, Ingrediente, Cliente
from . import cliente_crud, menu_crud, ingrediente_crud 
from datetime import datetime
from functools import reduce 
from sqlalchemy.exc import IntegrityError

# --- Funciones de LECTURA (Read) ---

def leer_pedido_por_id(db: Session, pedido_id: int):
    """
    Busca un pedido por su ID.
    """
    return db.query(Pedido).filter(Pedido.id == pedido_id).first()

def leer_pedidos_por_cliente(db: Session, cliente_id: int):
    """
    Busca todos los pedidos de un cliente especifico.
    Cumple requisito de la pauta.
    """
    return db.query(Pedido).filter(Pedido.cliente_id == cliente_id).all()

def leer_todos_los_pedidos(db: Session):
    """
    Devuelve una lista de todos los pedidos.
    """
    return db.query(Pedido).order_by(Pedido.fecha.desc()).all()

# --- Función de CREACIÓN (Create) ---

def crear_pedido(db: Session, cliente_id: int, menus_pedido: list):
    """
    Crea un nuevo pedido, descuenta stock y calcula el total.
    'menus_pedido' debe ser una lista de dicts:
    [
        {"id": 1, "cantidad": 2},  # Ej: 2 Completos
        {"id": 3, "cantidad": 1}   # Ej: 1 Barros Luco
    ]
    """
    
    # Iniciamos una transaccion. Si algo falla, db.rollback() revertira todo.
    try:
        # 1. Validar Cliente
        db_cliente = cliente_crud.obtener_cliente_por_id(db, cliente_id)
        if not db_cliente:
            raise Exception("El cliente seleccionado no existe.")
            
        # 2. Validar que el pedido no este vacio
        if not menus_pedido:
            raise Exception("El pedido esta vacio.")

        lista_menus_obj = [] # Lista para guardar los (objeto_menu, cantidad_pedida)
        
        # 3. Validar Menus y Preparar la lista para el calculo
        for item in menus_pedido:
            menu_id = item['id']
            cantidad = item['cantidad']
            
            if cantidad <= 0:
                raise Exception(f"La cantidad para el menu ID {menu_id} debe ser positiva.")

            db_menu = menu_crud.leer_menu_por_id(db, menu_id)
            if not db_menu:
                raise Exception(f"El menu con ID {menu_id} no existe.")
            
            # Guardamos el objeto menu y la cantidad pedida
            lista_menus_obj.append( (db_menu, cantidad) )

        # 4. Calcular Total (usando reduce)
        # (precio_menu * cantidad) + acumulador
        total_pedido = reduce(
            lambda acumulador, item: acumulador + (item[0].precio * item[1]),
            lista_menus_obj, # La lista de (objeto_menu, cantidad_pedida)
            0 # Valor inicial del acumulador
        )

        # 5. Validar y Descontar Stock (Paso critico)
        for db_menu, cantidad_pedida in lista_menus_obj:
            # Iterar sobre la receta (items_receta) de ESE menu
            for item_receta in db_menu.items_receta:
                # 'item_receta' es un objeto MenuIngrediente
                db_ingrediente = item_receta.ingrediente
                cantidad_necesaria_total = item_receta.cantidad * cantidad_pedida
                
                # Validacion de stock (pauta)
                if db_ingrediente.stock < cantidad_necesaria_total:
                    raise Exception(f"Stock insuficiente para '{db_ingrediente.nombre}' (necesario: {cantidad_necesaria_total}, disponible: {db_ingrediente.stock})")
                
                # Descontar el stock
                db_ingrediente.stock -= cantidad_necesaria_total

        # 6. Si todo el stock esta OK, crear el Pedido en la BD
        db_pedido = Pedido(
            cliente=db_cliente,
            fecha=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total=total_pedido
        )
        db.add(db_pedido)
        
        # 7. Crear las asociaciones PedidoMenu
        for db_menu, cantidad_pedida in lista_menus_obj:
            db_pedido_menu = PedidoMenu(
                pedido=db_pedido, # Asocia con el pedido recien creado
                menu=db_menu,     # Asocia con el menu
                cantidad=cantidad_pedida
            )
            db.add(db_pedido_menu)
            
        # 8. Guardar todo en la BD (Pedido, asociaciones y descuentos de stock)
        db.commit()
        db.refresh(db_pedido)
        print(f"Pedido ID {db_pedido.id} creado con exito por un total de ${total_pedido}.")
        return db_pedido
        
    except Exception as e:
        db.rollback() # Revertir todo si algo falla (ej. stock insuficiente)
        print(f"Error al crear pedido: {e}")
        return None