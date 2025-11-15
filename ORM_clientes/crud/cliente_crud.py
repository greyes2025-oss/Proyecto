from sqlalchemy.orm import Session
import models  
from sqlalchemy.exc import IntegrityError 

# --- Función de CREACIÓN (Create) ---

def crear_cliente(db: Session, nombre: str, email: str):
    """
    Crea un nuevo cliente en la base de datos.
    """
    # Validacion: nombre y email no vacios
    if not nombre or not email:
        print("Error: Nombre y Email no pueden estar vacios.")
        return None
        
    # Validacion: email unico 
    if obtener_cliente_por_email(db, email):
        print(f"Error: El email '{email}' ya está registrado.")
        return None
        
    try:
        # 1. Crea el objeto Python
        db_cliente = models.Cliente(
            nombre=nombre.strip().title(),
            email=email.strip().lower() # Guardamos el email en minúsculas
        )

        # 2. Añade el objeto a la sesión
        db.add(db_cliente)
        
        # 3. Confirma (guarda) los cambios en la BD
        db.commit()
        
        # 4. Refresca el objeto (para obtener el id generado)
        db.refresh(db_cliente)
        
        print(f"Cliente '{db_cliente.nombre}' creado con éxito.")
        return db_cliente

    except IntegrityError:
        # Esto pasa si el email ya existe (doble check por si acaso)
        db.rollback() # Revierte los cambios
        print(f"Error de Integridad: El email '{email}' ya está registrado.")
        return None
    
    except Exception as e:
        # Manejo de cualquier otro error
        db.rollback()
        print(f"Ocurrió un error inesperado al crear el cliente: {e}")
        return None

# --- Funciones de LECTURA (Read) ---

def obtener_cliente_por_email(db: Session, email: str):
    """
    Busca y devuelve un cliente específico por su email.
    """
    email_normalizado = email.strip().lower()
    return db.query(models.Cliente).filter(models.Cliente.email == email_normalizado).first()

def obtener_cliente_por_id(db: Session, cliente_id: int):

    return db.query(models.Cliente).filter(models.Cliente.id == cliente_id).first()

def listar_clientes(db: Session):
    """
    Devuelve una lista de todos los clientes en la base de datos.
    """
    return db.query(models.Cliente).all()

# --- Función de ACTUALIZACIÓN (Update) ---

def actualizar_cliente(db: Session, cliente_id: int, nuevo_nombre: str, nuevo_email: str):
    
    db_cliente = obtener_cliente_por_id(db, cliente_id)
    
    if not db_cliente:
        print(f"Error: No se encontró el cliente con ID '{cliente_id}'.")
        return None
    
    # Validacion: no vacios
    if not nuevo_nombre or not nuevo_email:
        print("Error: Nombre y Email no pueden estar vacios.")
        return None
        
    try:
        db_cliente.nombre = nuevo_nombre.strip().title()
        db_cliente.email = nuevo_email.strip().lower()
            
        db.commit()
        db.refresh(db_cliente)
        print(f"Cliente '{db_cliente.nombre}' actualizado con éxito.")
        return db_cliente
        
    except IntegrityError:
        # Error si el nuevo_email ya existe en otro cliente
        db.rollback()
        print(f"Error: El nuevo email '{nuevo_email}' ya está en uso.")
        return None
    except Exception as e:
        db.rollback()
        print(f"Error al actualizar el cliente: {e}")
        return None

# --- Función de ELIMINACIÓN (Delete) ---

def eliminar_cliente(db: Session, cliente_id: int):
    """
    Elimina usando el ID del cliente.
    """
    db_cliente = obtener_cliente_por_id(db, cliente_id)
    
    if not db_cliente:
        print(f"Error: No se encontró el cliente con ID '{cliente_id}'.")
        return False
        

    if db_cliente.pedidos:
        print(f"Error: No se puede eliminar el cliente '{db_cliente.nombre}' porque tiene {len(db_cliente.pedidos)} pedido(s) asociados.")
        return False
    
    try:
        db.delete(db_cliente)
        db.commit()
        print(f"Cliente '{db_cliente.nombre}' (ID: {cliente_id}) eliminado con éxito.")
        return True
    except Exception as e:
        db.rollback()
        print(f"Error al eliminar el cliente: {e}")
        return False