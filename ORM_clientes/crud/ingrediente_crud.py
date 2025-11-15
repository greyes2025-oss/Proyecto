from sqlalchemy.orm import Session
import models 
from sqlalchemy.exc import IntegrityError 
import csv 

# --- Función de CREACIÓN (Create) ---
def crear_ingrediente(db: Session, nombre: str, stock: float):
    """
    Crea un nuevo ingrediente en la base de datos.
    """
    # Validacion: nombre no vacio y stock positivo (pauta)
    if not nombre or stock < 0:
        print("Error: El nombre no puede estar vacio y el stock no puede ser negativo.")
        return None

    try:
        # 1. Crea el objeto Python
        #    Usa el modelo Ingrediente  y el campo stock
        db_ingrediente = models.Ingrediente(
            nombre=nombre.strip().title(),
            stock=stock
        )

        # 2. Añade el objeto a la sesión
        db.add(db_ingrediente)
        
        # 3. Confirma (guarda) los cambios en la base de datos
        db.commit()
        
        # 4. Refresca el objeto (para obtener el 'id' generado)
        db.refresh(db_ingrediente)
        
        print (f"Ingrediente '{db_ingrediente.nombre}' creado con exito.")
        return db_ingrediente
    
    except IntegrityError as e:
        # Esto pasa si el nombre ya existe (porque pusimos unique=True)
        db.rollback() #revertir los cambios en caso de error
        print(f"Error: El ingrediente con nombre '{nombre}' ya existe.")
        return None
    
    except Exception as e:
        db.rollback() #revertir los cambios en caso de error
        print(f"Error al crear el ingrediente: {e}")
        return None

# --- Funciones de LECTURA (Read) ---

def obtener_ingrediente_por_id(db: Session, ingrediente_id: int):
    """
    Busca un ingrediente por su ID.
    Esta funcion es esencial para menu_crud y pedido_crud.
    """
    return db.query(models.Ingrediente).filter(models.Ingrediente.id == ingrediente_id).first()

def obtener_ingrediente_por_nombre(db: Session, nombre: str):
    """
    Busca y devuelve un ingrediente específico por su nombre.
    """
    nombre_normalizado = nombre.strip().title()
    return db.query(models.Ingrediente).filter(models.Ingrediente.nombre == nombre_normalizado).first()

def listar_ingredientes(db: Session):
    """
    Devuelve una lista de todos los ingredientes en la base de datos.
    """
    return db.query(models.Ingrediente).all()

# --- Función de ACTUALIZACIÓN (Update) ---

def actualizar_stock_ingrediente(db: Session, ingrediente_id: int, nuevo_stock: float):
    """
    Actualiza el stock de un ingrediente (lo reemplaza, no lo suma).
    """
    db_ingrediente = obtener_ingrediente_por_id(db, ingrediente_id)
    
    if not db_ingrediente:
        print(f"Error: No se encontró el ingrediente ID '{ingrediente_id}' para actualizar.")
        return None
    
    # Validacion: stock positivo
    if nuevo_stock < 0:
        print(f"Error: El stock no puede ser negativo.")
        return None
    
    try:
        # Actualizamos la cantidad
        db_ingrediente.stock = nuevo_stock
        db.commit() # Confirma el cambio
        db.refresh(db_ingrediente)
        print(f"Stock de '{db_ingrediente.nombre}' actualizado a {nuevo_stock}.")
        return db_ingrediente
    except Exception as e:
        db.rollback()
        print(f"Error al actualizar el ingrediente: {e}")
        return None

# --- Función de ELIMINACIÓN (Delete) ---

def eliminar_ingrediente(db: Session, ingrediente_id: int):
    """
    Elimina un ingrediente de la base de datos por su ID.
    """
    db_ingrediente = obtener_ingrediente_por_id(db, ingrediente_id)
    
    if not db_ingrediente:
        print(f"Error: No se encontró el ingrediente ID '{ingrediente_id}' para eliminar.")
        return False
    
    # Validacion: No eliminar si es parte de un menu
    if db_ingrediente.menus_donde_aparece:
        print(f"Error: No se puede eliminar '{db_ingrediente.nombre}', esta usado en {len(db_ingrediente.menus_donde_aparece)} menu(s).")
        return False
        
    try:
        db.delete(db_ingrediente)
        db.commit()
        print(f"Ingrediente '{db_ingrediente.nombre}' eliminado con éxito.")
        return True
    except Exception as e:
        db.rollback()
        print(f"Error al eliminar el ingrediente: {e}")
        return False

# --- Función de Carga CSV
def cargar_ingredientes_csv(db: Session, ruta_archivo: str):
    """
    Carga ingredientes desde un archivo CSV.
    Si el ingrediente existe, actualiza su stock (lo suma).
    Si no existe, lo crea con el stock dado.
    Formato CSV esperado: nombre,stock_a_cargar
    Ej: Pan,100
    """
    print(f"Iniciando carga de stock desde {ruta_archivo}...")
    try:
        with open(ruta_archivo, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
        
            for fila in reader:
                # Validacion: formato de fila (pauta)
                if len(fila) != 2:
                    print(f"Error de formato en CSV, linea ignorada: {fila}")
                    continue
                
                nombre_ingrediente = fila[0]
                try:
                    stock_a_cargar = float(fila[1])
                    if stock_a_cargar < 0:
                        raise ValueError("Stock no puede ser negativo")
                except ValueError:
                    print(f"Error de formato en CSV, stock invalido, linea ignorada: {fila}")
                    continue

                # Buscar si el ingrediente ya existe
                db_ingrediente = obtener_ingrediente_por_nombre(db, nombre_ingrediente)
                
                if db_ingrediente:
                    # Si existe, SUMA el stock
                    stock_nuevo = db_ingrediente.stock + stock_a_cargar
                    actualizar_stock_ingrediente(db, db_ingrediente.id, stock_nuevo)
                else:
                    # Si no existe, lo CREA
                    crear_ingrediente(db, nombre_ingrediente, stock_a_cargar)
            
        print("Carga de CSV completada.")
        return True
        
    except FileNotFoundError:
        print(f"Error: Archivo CSV no encontrado en {ruta_archivo}")
        return False
    except Exception as e:
        print(f"Error inesperado durante la carga CSV: {e}")
        return False
    
    