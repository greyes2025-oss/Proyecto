# 1. --- Importaciones ---
from database import SessionLocal, engine, Base
import models 
import crud.ingrediente_crud as icrud
import crud.cliente_crud as ccrud
import crud.menu_crud as mcrud
import crud.pedido_crud as pcrud
from sqlalchemy.orm import Session # <-- Correcto


def inicializar_bd():
    """Crea las tablas en la BD (si no existen)"""
    Base.metadata.create_all(bind=engine)
    print("Tablas verificadas/creadas.")

def limpiar_tablas(db: Session): # <-- Correcto
    """Funcion rapida para borrar todo y empezar de cero."""
    print("Limpiando datos antiguos...")
    # Borramos en orden inverso para evitar errores de clave foranea
    db.query(models.PedidoMenu).delete()
    db.query(models.MenuIngrediente).delete()
    db.query(models.Pedido).delete()
    db.query(models.Menu).delete()
    db.query(models.Cliente).delete()
    db.query(models.Ingrediente).delete()
    db.commit()
    print("Datos limpiados.")

# --- (Las funciones de prueba de tu amigo se mantienen) ---

def probar_crud_ingredientes(db: Session): # <-- Añadido type hint
    """Prueba el CRUD de Ingredientes"""
    print("\n--- (Iniciando prueba CRUD Ingredientes) ---")
    
    # --- Prueba CREATE ---
    print("\n[Prueba CREATE Ingrediente]")
    # (Usamos el CRUD actualizado, solo nombre y stock)
    ing1 = icrud.crear_ingrediente(db, nombre="Tomate", stock=10)
    ing2 = icrud.crear_ingrediente(db, nombre="Pan de Completo", stock=20)
    ing3 = icrud.crear_ingrediente(db, nombre="Vienesa", stock=30)
    ing4 = icrud.crear_ingrediente(db, nombre="Palta", stock=15.5)
    
    # --- Prueba duplicado ---
    print("\nIntentando crear duplicado (esto debe fallar):")
    icrud.crear_ingrediente(db, nombre="Tomate", stock=5)

    # --- Prueba READ ---
    print("\n[Prueba READ Ingrediente]")
    ingredientes = icrud.listar_ingredientes(db)
    print(f"Se encontraron {len(ingredientes)} ingredientes.")
    
    # --- Prueba UPDATE ---
    print("\n[Prueba UPDATE Ingrediente]")
    # (Usamos el CRUD actualizado, actualiza a un valor fijo, no suma)
    icrud.actualizar_stock_ingrediente(db, ingrediente_id=ing1.id, nuevo_stock=25.0) 
    tomate = icrud.obtener_ingrediente_por_id(db, ing1.id)
    print(f"Nuevo stock de Tomate: {tomate.stock}") # Debería ser 25.0

    # --- Prueba DELETE ---
    print("\n[Prueba DELETE Ingrediente]")
    icrud.eliminar_ingrediente(db, ingrediente_id=ing2.id) # Eliminamos "Pan de Completo"
    ingredientes_final = icrud.listar_ingredientes(db)
    print(f"Quedan {len(ingredientes_final)} ingredientes.")
    print("--- (Fin prueba CRUD Ingredientes) ---")
    
    # Devolvemos los IDs de los ingredientes que SI quedaron
    return {"vienesa_id": ing3.id, "palta_id": ing4.id, "tomate_id": ing1.id}


def probar_crud_clientes(db: Session): # <-- Añadido type hint
    """
    Función para probar las operaciones CRUD de Clientes.
    """
    print("\n--- (Iniciando prueba CRUD Clientes) ---")
    
    # --- Prueba 1: CREAR ---
    print("\n[Prueba CREATE Cliente]")
    cliente1 = ccrud.crear_cliente(db, nombre="Juan Perez", email="juan.perez@correo.com")
    cliente2 = ccrud.crear_cliente(db, nombre="Ana Gomez", email="ana.gomez@correo.com")
    
    print("\nIntentando crear duplicado (esto debe fallar):")
    ccrud.crear_cliente(db, nombre="Pedro", email="juan.perez@correo.com")

    # --- Prueba 2: LEER (Listar) ---
    print("\n[Prueba READ Cliente (Listar)]")
    clientes = ccrud.listar_clientes(db)
    print(f"Se encontraron {len(clientes)} clientes:")
    for c in clientes:
        print(f"   - ID: {c.id}, Nombre: {c.nombre}, Email: {c.email}")

    # --- Prueba 3: ACTUALIZAR ---
    print("\n[Prueba UPDATE Cliente]")
    # (Usamos el CRUD actualizado, buscamos por ID)
    ccrud.actualizar_cliente(db, cliente_id=cliente2.id, nuevo_nombre="Ana Gonzalez", nuevo_email="ana.gonzalez@correo.com")
    
    ana = ccrud.obtener_cliente_por_id(db, cliente2.id) 
    print(f"Nombre actualizado: {ana.nombre}, Email actualizado: {ana.email}")

    # --- Prueba 4: ELIMINAR (Debe funcionar) ---
    print("\n[Prueba DELETE Cliente (Debe funcionar)]")
    ccrud.eliminar_cliente(db, cliente_id=ana.id) # Usamos el ID

    # --- Prueba 5: LEER (Verificar eliminación) ---
    print("\n[Prueba READ Cliente (Verificar eliminación)]")
    clientes_final = ccrud.listar_clientes(db)
    print(f"Quedan {len(clientes_final)} clientes:")
    for c in clientes_final:
        print(f"   - {c.nombre}")
    
    print("--- (Fin prueba CRUD Clientes) ---")
    return {"cliente1_id": cliente1.id} # Devolvemos el ID del cliente que SI quedo

def probar_crud_menu(db: Session, ids_ingredientes: dict):
    """
    Prueba el CRUD de Menus usando los ingredientes creados.
    """
    print("\n--- (Iniciando prueba CRUD Menu) ---")
    
    # --- Prueba 1: CREAR Menu ---
    print("\n[Prueba CREATE Menu 'Completo Sin Pan']")
    
    # Definimos la receta usando los IDs que nos envio la prueba anterior
    receta_completo = [
        {"ingrediente_id": ids_ingredientes['vienesa_id'], "cantidad": 1},
        {"ingrediente_id": ids_ingredientes['tomate_id'], "cantidad": 1},
        {"ingrediente_id": ids_ingredientes['palta_id'], "cantidad": 0.3}
    ]
    
    menu1 = mcrud.crear_menu(db, "Completo Sin Pan", "Un completo pero sin pan", 2500, receta_completo)
    
    if not menu1:
        # Hacemos que la prueba falle si no se crea el menu
        print("Error critico en la prueba de menu. Abortando.")
        return None 
        
    print("\n[Prueba READ Menu (Listar)]")
    menus = mcrud.leer_todos_los_menus(db)
    print(f"Se encontraron {len(menus)} menus:")
    print(f" - {menus[0].nombre} (Precio: ${menus[0].precio})")
    
    print("\nVerificando receta del menu...")
    # Verificamos que los ingredientes se asociaron
    db.refresh(menu1) # Recargamos el menu desde la BD
    print(f"El menu '{menu1.nombre}' tiene {len(menu1.items_receta)} ingredientes:")
    for item_receta in menu1.items_receta:
        print(f"  - {item_receta.ingrediente.nombre} (Cantidad: {item_receta.cantidad})")
        
    print("--- (Fin prueba CRUD Menu) ---")
    return {"menu1_id": menu1.id} # Devolvemos el ID del menu creado


def probar_crud_pedido(db: Session, ids_clientes: dict, ids_menus: dict):
    """
    Prueba el flujo completo de crear un pedido, validando stock y rollback.
    """
    print("\n--- (Iniciando prueba CRUD Pedido) ---")

    # IDs que usaremos
    id_cliente = ids_clientes['cliente1_id']
    id_menu = ids_menus['menu1_id']
    
    # Consultamos stock inicial
    vienesa = icrud.obtener_ingrediente_por_nombre(db, "Vienesa")
    print(f"Stock INICIAL de Vienesa: {vienesa.stock}") # Deberia ser 30

    # --- Prueba 1: CREAR PEDIDO (Debe funcionar) ---
    print("\n[Prueba CREATE Pedido (Comprando 10 Completos)]")
    
    compra_1 = [
        {"id": id_menu, "cantidad": 10} # 10 Completos
    ]
    
    pedido_1 = pcrud.crear_pedido(db, cliente_id=id_cliente, menus_pedido=compra_1)
    if not pedido_1:
        print("FALLO la creacion del Pedido 1 (stock deberia estar OK).")
        return # Detenemos la prueba
    
    # --- Prueba 2: VERIFICAR DESCUENTO DE STOCK ---
    print("\n[Prueba VERIFICAR Stock]")
    db.refresh(vienesa) # Recargamos la vienesa desde la BD
    print(f"Stock NUEVO de Vienesa (esperado 20): {vienesa.stock}")
    
    if vienesa.stock != 20:
        print(f"FALLO EL DESCUENTO DE STOCK. Stock actual: {vienesa.stock}, se esperaba 20.")
        return
    
    print("¡Descuento de stock exitoso!")

    # --- Prueba 3: PRUEBA DE ERROR (STOCK INSUFICIENTE) ---
    print("\n[Prueba ERROR Pedido (Stock insuficiente - 1000 Completos)]")
    
    compra_2 = [ {"id": id_menu, "cantidad": 1000} ]
    
    pedido_2 = pcrud.crear_pedido(db, cliente_id=id_cliente, menus_pedido=compra_2)
    
    if pedido_2: # Si el pedido se creo, es un error
        print("FALLO LA VALIDACION. El pedido 2 se creo cuando debio fallar por stock.")
        return
    
    print("Prueba de error exitosa: El pedido 2 fue bloqueado por falta de stock (ver error arriba).")
    
    # --- Prueba 4: VERIFICAR ROLLBACK ---
    print("\n[Prueba VERIFICAR Rollback]")
    db.refresh(vienesa)
    print(f"Stock de Vienesa despues de pedido fallido (esperado 20): {vienesa.stock}")
    if vienesa.stock != 20:
        print("FALLO EL ROLLBACK. El stock se desconto parcialmente.")
        return
        
    print("¡Rollback exitoso!")
    
    # --- Prueba 5: VERIFICAR ELIMINAR CLIENTE (Debe fallar) ---
    print("\n[Prueba DELETE Cliente (Debe fallar)]")
    # El cliente 'Juan Perez' (cliente1) ahora tiene un pedido.
    se_elimino = ccrud.eliminar_cliente(db, cliente_id=id_cliente)
    if se_elimino:
        print("FALLO LA VALIDACION. Se elimino un cliente con pedidos.")
        return
    
    print("Prueba de validacion exitosa: No se permitio eliminar cliente con pedidos (ver error arriba).")


# --- Ejecución Principal ---
if __name__ == "__main__":
    
    # 1. Asegura que las tablas existan
    inicializar_bd()
    
    # 2. Obtiene una sesión de la base de datos
    db = SessionLocal()
    
    # ✅ CORRECCION: Se elimino el bloque 'try...except...finally' de aqui.
    # Cada funcion CRUD ahora maneja sus propios errores (commit/rollback).
    
    # 3. Limpia la BD para una prueba nueva
    limpiar_tablas(db) 
    
    # 4. Ejecuta las pruebas de Ingredientes y Clientes
    # (Los 'print' dentro de las funciones nos diran si algo falla)
    ids_ingredientes = probar_crud_ingredientes(db) 
    ids_clientes = probar_crud_clientes(db)
    
    # 5. Ejecuta las pruebas de Menu
    # Solo continuamos si las pruebas anteriores no devolvieron 'None'
    if ids_ingredientes and ids_clientes:
        ids_menus = probar_crud_menu(db, ids_ingredientes)
        
        # 6. Ejecuta las pruebas de Pedido (el flujo completo)
        if ids_menus:
            probar_crud_pedido(db, ids_clientes, ids_menus)

    # 7. Cerrar la sesion
    db.close() 
    print("\n--- Pruebas finalizadas ---")
    