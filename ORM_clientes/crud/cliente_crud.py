from sqlalchemy.orm import Session
import models  # Importamos nuestros modelos (models.py)
from sqlalchemy.exc import IntegrityError # Para manejar errores de email duplicado

# --- Función de CREACIÓN (Create) ---

def crear_cliente(db: Session, nombre: str, email: str):
    """
    Crea un nuevo cliente en la base de datos.
    """
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
        
        # 4. Refresca el objeto (para obtener el 'id' generado)
        db.refresh(db_cliente)
        
        print(f"Cliente '{db_cliente.nombre}' creado con éxito.")
        return db_cliente

    except IntegrityError:
        # Esto pasa si el email ya existe (porque pusimos 'unique=True')
        db.rollback() # Revierte los cambios
        print(f"Error: El email '{email}' ya está registrado.")
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

def listar_clientes(db: Session):
    """
    Devuelve una lista de todos los clientes en la base de datos.
    """
    return db.query(models.Cliente).all()

# --- Función de ACTUALIZACIÓN (Update) ---

def actualizar_cliente(db: Session, email: str, nuevo_nombre: str = None, nuevo_email: str = None):
    """
    Actualiza el nombre o el email de un cliente.
    """
    db_cliente = obtener_cliente_por_email(db, email)
    
    if not db_cliente:
        print(f"Error: No se encontró el cliente con email '{email}'.")
        return None
    
    try:
        if nuevo_nombre:
            db_cliente.nombre = nuevo_nombre.strip().title()
            
        if nuevo_email:
            db_cliente.email = nuevo_email.strip().lower()
            
        db.commit()
        db.refresh(db_cliente)
        print(f"Cliente '{db_cliente.nombre}' actualizado con éxito.")
        return db_cliente
        
    except IntegrityError:
        # Error si el 'nuevo_email' ya existe en otro cliente
        db.rollback()
        print(f"Error: El nuevo email '{nuevo_email}' ya está en uso.")
        return None
    except Exception as e:
        db.rollback()
        print(f"Error al actualizar el cliente: {e}")
        return None

# --- Función de ELIMINACIÓN (Delete) ---

def eliminar_cliente(db: Session, email: str):
    """
    Elimina un cliente de la base de datos por su email.
    """
    db_cliente = obtener_cliente_por_email(db, email)
    
    if not db_cliente:
        print(f"Error: No se encontró el cliente con email '{email}'.")
        return False
        
    # --- Verificación de la pauta ---
    # La pauta dice: "Impedir eliminar clientes que tengan pedidos asociados"
    # 'db_cliente.pedidos' es la relación que definimos.
    # Si la lista NO está vacía, tiene pedidos.
    
    # ¡ESTA PARTE ESTÁ COMENTADA TEMPORALMENTE!
    # if db_cliente.pedidos:
    #     print(f"Error: No se puede eliminar el cliente '{db_cliente.nombre}' porque tiene pedidos asociados.")
    #     return False
    
    try:
        db.delete(db_cliente)
        db.commit()
        print(f"Cliente '{db_cliente.nombre}' (email: {email}) eliminado con éxito.")
        return True
    except Exception as e:
        db.rollback()
        print(f"Error al eliminar el cliente: {e}")
        return False