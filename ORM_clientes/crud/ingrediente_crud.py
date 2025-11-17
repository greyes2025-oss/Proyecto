from sqlalchemy.orm import Session
import models 
from sqlalchemy.exc import IntegrityError 
import csv 

# --- Funciones de LECTURA (Read) ---
def obtener_ingrediente_por_id(db: Session, ingrediente_id: int):
    """Busca un ingrediente por su ID."""
    return db.query(models.Ingrediente).filter(models.Ingrediente.id == ingrediente_id).first()

def obtener_ingrediente_por_nombre(db: Session, nombre: str):
    """Busca y devuelve un ingrediente específico por su nombre (formateado)."""
    nombre_normalizado = nombre.strip().title()
    return db.query(models.Ingrediente).filter(models.Ingrediente.nombre == nombre_normalizado).first()

def listar_ingredientes(db: Session):
    """Devuelve una lista de todos los ingredientes."""
    return db.query(models.Ingrediente).all()

# --- Función de CREACIÓN/UPSERT (Create or Sum Stock) ---
def crear_ingrediente(db: Session, nombre: str, stock: float):
    """
    Busca el ingrediente por nombre. Si existe, SUMA el stock. Si no existe, lo crea.
    Devuelve el objeto Ingrediente o un string de error.
    """
    
    if not nombre or stock < 0:
        return "Error: El nombre no puede estar vacio y el stock no puede ser negativo."

    nombre_formateado = nombre.strip().title()
    db_ingrediente = obtener_ingrediente_por_nombre(db, nombre_formateado)
    
    try:
        if db_ingrediente:
            # 1. Si existe, SUMAR el stock
            stock_nuevo = db_ingrediente.stock + stock
            db_ingrediente.stock = stock_nuevo
            db.commit()
            db.refresh(db_ingrediente)
            return db_ingrediente
        else:
            # 2. Si no existe, CREAR
            db_ingrediente = models.Ingrediente(
                nombre=nombre_formateado,
                stock=stock
            )
            db.add(db_ingrediente)
            db.commit()
            db.refresh(db_ingrediente)
            return db_ingrediente
            
    except Exception as e:
        db.rollback() 
        return f"Ocurrió un error en la BD: {e}" 

# --- Función de ACTUALIZACIÓN (Update - Fija un valor) ---
def actualizar_stock_ingrediente(db: Session, ingrediente_id: int, nuevo_stock: float):
    """Actualiza el stock de un ingrediente al valor especificado (reemplaza)."""
    db_ingrediente = obtener_ingrediente_por_id(db, ingrediente_id)
    
    if not db_ingrediente or nuevo_stock < 0:
        return None
    
    try:
        db_ingrediente.stock = nuevo_stock
        db.commit()
        db.refresh(db_ingrediente)
        return db_ingrediente
    except Exception:
        db.rollback()
        return None

# --- Función de ELIMINACIÓN (Delete) ---
def eliminar_ingrediente(db: Session, ingrediente_id: int):
    """Elimina un ingrediente."""
    db_ingrediente = obtener_ingrediente_por_id(db, ingrediente_id)
    
    if not db_ingrediente:
        return False
    
    # Se eliminó la restricción de menús para cumplir el requisito.
        
    try:
        db.delete(db_ingrediente)
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False

# --- Función de Carga CSV ---


def cargar_ingredientes_csv(db: Session, ruta_archivo: str):
    """
    Carga ingredientes desde un archivo CSV. Usa la lógica de crear_ingrediente (upsert).
    MODIFICADO: Acepta 3 columnas (nombre, unidad, cantidad) e ignora 'unidad'.
    """
    print(f"Iniciando carga de stock desde {ruta_archivo}...")
    try:
        with open(ruta_archivo, mode='r', encoding='utf-8-sig') as file: # 'utf-8-sig' maneja el BOM \ufeff
            reader = csv.reader(file)
            
            # Omitir la cabecera si existe (ej: 'nombre', 'unidad', 'cantidad')
            try:
                next(reader) 
            except StopIteration:
                pass # Archivo vacío

            for fila in reader:
                # Si la fila está vacía, la saltamos
                if not fila:
                    continue
                
                # CORRECCIÓN: Esperamos 3 columnas (nombre, unidad, cantidad)
                if len(fila) == 3:
                    nombre_ingrediente = fila[0]
                    # Ignoramos fila[1] (unidad)
                    stock_str = fila[2]
                
                # (Mantenemos la lógica de 2 columnas por si acaso)
                elif len(fila) == 2:
                    nombre_ingrediente = fila[0]
                    stock_str = fila[1]
                
                else:
                    print(f"Error de formato en CSV, linea ignorada (se esperaban 2 o 3 columnas): {fila}")
                    continue
                
                try:
                    stock_a_cargar = float(stock_str)
                    if stock_a_cargar < 0:
                        raise ValueError("Stock no puede ser negativo")
                except ValueError:
                    print(f"Error de formato en CSV, stock invalido ('{stock_str}'), linea ignorada: {fila}")
                    continue

                # Llama a la función que GUARDA EN LA BD (crear o sumar)
                resultado = crear_ingrediente(db, nombre_ingrediente, stock_a_cargar)
                
                if isinstance(resultado, str):
                    print(f"Fallo al procesar '{nombre_ingrediente}': {resultado}")
            
        print("Carga de CSV completada.")
        return True
        
    except FileNotFoundError:
        print(f"Error: Archivo CSV no encontrado en {ruta_archivo}")
        return False
    except Exception as e:
        print(f"Error inesperado durante la carga CSV: {e}")
        return False