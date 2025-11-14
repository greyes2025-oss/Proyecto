from database import SessionLocal, engine, Base
import models
import crud.ingrediente_crud as icrud

def init_db():
    #creamos las tablas
    Base.metadata.create_all(bind=engine)
    
def probar_crud():

    print("Probando operaciones CRUD de Ingredientes")

    db = SessionLocal()

    try:
        print("\n[Prueba CREATE]")
        # Ahora usamos el alias 'icrud.'
        icrud.crear_ingrediente(db, nombre="Tomate", unidad="unid", cantidad=10)
        icrud.crear_ingrediente(db, nombre="Pan de Completo", unidad="unid", cantidad=20)
        icrud.crear_ingrediente(db, nombre="Vienesa", unidad="unid", cantidad=30)
        
        # Prueba de duplicado
        print("\nIntentando crear duplicado (esto debe fallar):")
        icrud.crear_ingrediente(db, nombre="Tomate", unidad="unid", cantidad=5)

        # --- Prueba 2: LEER (Listar) ---
        print("\n[Prueba READ (Listar)]")
        ingredientes = icrud.listar_ingredientes(db)
        if not ingredientes:
            print("No se encontraron ingredientes.")
        else:
            print(f"Se encontraron {len(ingredientes)} ingredientes:")
            for ing in ingredientes:
                print(f"  - ID: {ing.id}, Nombre: {ing.nombre}, Stock: {ing.cantidad} {ing.unidad}")

        # --- Prueba 3: ACTUALIZAR (Sumar stock) ---
        print("\n[Prueba UPDATE (Sumar 5 Tomates)]")
        icrud.actualizar_cantidad_ingrediente(db, nombre="Tomate", cantidad=5)
        
        # Verificamos el cambio
        tomate = icrud.obtener_ingrediente_por_nombre(db, "Tomate")
        print(f"Nuevo stock de Tomate: {tomate.cantidad}") # Debería ser 15

        # --- Prueba 4: ACTUALIZAR (Restar stock) ---
        print("\n[Prueba UPDATE (Restar 10 Vienesas)]")
        icrud.actualizar_cantidad_ingrediente(db, nombre="Vienesa", cantidad=-10)
        
        vienesa = icrud.obtener_ingrediente_por_nombre(db, "Vienesa")
        print(f"Nuevo stock de Vienesa: {vienesa.cantidad}") # Debería ser 20

        # --- Prueba 5: ELIMINAR ---
        print("\n[Prueba DELETE (Eliminar 'Pan de Completo')]")
        icrud.eliminar_ingrediente(db, nombre="Pan de Completo")

        # --- Prueba 6: LEER (Verificar eliminación) ---
        print("\n[Prueba READ (Verificar eliminación)]")
        ingredientes_final = icrud.listar_ingredientes(db)
        print(f"Quedan {len(ingredientes_final)} ingredientes:")
        for ing in ingredientes_final:
            print(f"  - {ing.nombre}")
    
    except Exception as e:
        print(f"\n¡¡¡ OCURRIÓ UN ERROR EN LA PRUEBA !!!: {e}")
        db.rollback() # Deshacer todo si algo falla
    
    finally:
        db.close() # Siempre cerrar la sesión al terminar
        print("\n--- Prueba del CRUD finalizada ---")

# --- Ejecución Principal ---
if __name__ == "__main__":
    # 1. Asegura que las tablas existan
    init_db()
    
    # 2. Ejecuta las pruebas CRUD
    probar_crud()