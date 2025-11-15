# 1. --- Importaciones ---
from database import SessionLocal, engine, Base
import models
import crud.ingrediente_crud as icrud
import crud.cliente_crud as ccrud

def inicializar_bd():
    """Crea las tablas en la BD (si no existen)"""
    Base.metadata.create_all(bind=engine)
    print("Tablas verificadas/creadas.")

def probar_crud_ingredientes(db):
    """Prueba el CRUD de Ingredientes"""
    print("\n--- (Iniciando prueba CRUD Ingredientes) ---")
    
    # --- Prueba CREATE ---
    print("\n[Prueba CREATE Ingrediente]")
    icrud.crear_ingrediente(db, nombre="Tomate", unidad="unid", cantidad=10)
    icrud.crear_ingrediente(db, nombre="Pan de Completo", unidad="unid", cantidad=20)
    icrud.crear_ingrediente(db, nombre="Vienesa", unidad="unid", cantidad=30)
    
    # --- Prueba duplicado ---
    print("\nIntentando crear duplicado (esto debe fallar):")
    icrud.crear_ingrediente(db, nombre="Tomate", unidad="unid", cantidad=5)

    # --- Prueba READ ---
    print("\n[Prueba READ Ingrediente]")
    ingredientes = icrud.listar_ingredientes(db)
    print(f"Se encontraron {len(ingredientes)} ingredientes.")
    
    # --- Prueba UPDATE ---
    print("\n[Prueba UPDATE Ingrediente]")
    icrud.actualizar_cantidad_ingrediente(db, nombre="Tomate", cantidad=5) # Suma 5
    tomate = icrud.obtener_ingrediente_por_nombre(db, "Tomate")
    print(f"Nuevo stock de Tomate: {tomate.cantidad}") # Debería ser 15

    # --- Prueba DELETE ---
    print("\n[Prueba DELETE Ingrediente]")
    icrud.eliminar_ingrediente(db, nombre="Pan de Completo")
    ingredientes_final = icrud.listar_ingredientes(db)
    print(f"Quedan {len(ingredientes_final)} ingredientes.")
    print("--- (Fin prueba CRUD Ingredientes) ---")


def probar_crud_clientes(db):
    """
    Función para probar las operaciones CRUD de Clientes.
    """
    print("\n--- (Iniciando prueba CRUD Clientes) ---")
    
    # --- Prueba 1: CREAR ---
    print("\n[Prueba CREATE Cliente]")
    ccrud.crear_cliente(db, nombre="Juan Perez", email="juan.perez@correo.com")
    ccrud.crear_cliente(db, nombre="Ana Gomez", email="ana.gomez@correo.com")
    
    # Prueba de duplicado
    print("\nIntentando crear duplicado (esto debe fallar):")
    ccrud.crear_cliente(db, nombre="Pedro", email="juan.perez@correo.com")

    # --- Prueba 2: LEER (Listar) ---
    print("\n[Prueba READ Cliente (Listar)]")
    clientes = ccrud.listar_clientes(db)
    print(f"Se encontraron {len(clientes)} clientes:")
    for c in clientes:
        print(f"  - ID: {c.id}, Nombre: {c.nombre}, Email: {c.email}")

    # --- Prueba 3: ACTUALIZAR ---
    print("\n[Prueba UPDATE Cliente]")
    ccrud.actualizar_cliente(db, email="ana.gomez@correo.com", nuevo_nombre="Ana Gonzalez")
    
    # Verificamos el cambio
    # ¡¡¡ ESTA ES LA LÍNEA CORREGIDA !!!
    ana = ccrud.obtener_cliente_por_email(db, "ana.gomez@correo.com") 
    
    print(f"Nombre actualizado: {ana.nombre}") # Debería ser Ana Gonzalez

    # --- Prueba 4: ELIMINAR (Debe funcionar) ---
    print("\n[Prueba DELETE Cliente (Debe funcionar)]")
    # 'Ana' no tiene pedidos, así que se puede eliminar.
    ccrud.eliminar_cliente(db, email="ana.gomez@correo.com")

    # --- Prueba 5: LEER (Verificar eliminación) ---
    print("\n[Prueba READ Cliente (Verificar eliminación)]")
    clientes_final = ccrud.listar_clientes(db)
    print(f"Quedan {len(clientes_final)} clientes:")
    for c in clientes_final:
        print(f"  - {c.nombre}")
    
    print("--- (Fin prueba CRUD Clientes) ---")


# --- Ejecución Principal ---
if __name__ == "__main__":
    
    # 1. Asegura que las tablas existan
    inicializar_bd()
    
    # 2. Obtiene una sesión de la base de datos
    db = SessionLocal()
    
    try:
        # 3. Ejecuta las pruebas de Ingredientes
        # (Las comento para que no se ejecuten cada vez)
        # probar_crud_ingredientes(db) 
        
        # 4. Ejecuta las pruebas de Clientes
        probar_crud_clientes(db)
        
    except Exception as e:
        print(f"\n¡¡¡ OCURRIÓ UN ERROR EN LA PRUEBA !!!: {e}")
        db.rollback() # Deshacer todo si algo falla
    
    finally:
        db.close() # Siempre cerrar la sesión al terminar
        print("\n--- Pruebas finalizadas ---")