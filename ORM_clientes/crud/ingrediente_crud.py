from sqlalchemy.orm import Session
import models
from sqlalchemy.exc import IntegrityError # para manejar errores de la base de datos

def crear_ingrediente(db: Session, nombre: str, unidad: str, cantidad: float):
# Crear un nuevo ingrediente en la base de datos
    try:
        nuevo_ingrediente = models.Ingredientes(
            nombre=nombre.strip().title(),
            unidad=unidad.strip().lower() if unidad else None,
            cantidad=cantidad
        )



        db.add(nuevo_ingrediente) #añade el objeto a la sesion 

        db.commit() #confirma los cambios en la base de datos

        db.refresh(nuevo_ingrediente) #actualiza el objeto con los datos de la bd

        print (f"Ingrediente '{nuevo_ingrediente.nombre}' creado con exito.")
        return nuevo_ingrediente
    

    except IntegrityError as e:
        db.rollback() #revertir los cambios en caso de error
        print(f"Error: El ingrediente con nombre '{nombre}' ya existe.")
        return None
    
    except Exception as e:
        db.rollback() #revertir los cambios en caso de error
        print(f"Error al crear el ingrediente: {e}")
        return None

#Funciones -----------------------------------------------------------------------------

def obtener_ingrediente_por_nombre(db: Session, nombre: str):

    nombre_normalizado = nombre.strip().title() #normalizamos el nombre para la busqueda
    return db.query(models.Ingredientes).filter(models.Ingredientes.nombre == nombre_normalizado).first() # devuelve el primer ingrediente que coincida con el nombre

def listar_ingredientes(db: Session, skip: int = 0, limit: int = 100):

    return db.query(models.Ingredientes).offset(skip).limit(limit).all() # devuelve una lista de ingredientes con paginacion


def actualizar_cantidad_ingrediente(db: Session, nombre: str, cantidad: float):
  
    db_ingrediente = obtener_ingrediente_por_nombre(db, nombre)
    
    if not db_ingrediente:
        print(f"Error: No se encontró el ingrediente '{nombre}' para actualizar.")
        return None
    
    # Sumamos o restamos al stock actual
    nueva_cantidad = db_ingrediente.cantidad + cantidad
    
    if nueva_cantidad <= 0:
        # Si el stock queda en 0 o negativo, lo eliminamos
        print(f"Stock de '{nombre}' agotado. Eliminando ingrediente.")
        db.delete(db_ingrediente)
    else:
        # Actualizamos la cantidad
        db_ingrediente.cantidad = nueva_cantidad
        print(f"Stock de '{nombre}' actualizado a {nueva_cantidad}.")
    
    try:
        db.commit() # Confirma el cambio (actualización o eliminación)
        return db_ingrediente
    except Exception as e:
        db.rollback()
        print(f"Error al actualizar el ingrediente: {e}")
        return None



def eliminar_ingrediente(db: Session, nombre: str):
  
    db_ingrediente = obtener_ingrediente_por_nombre(db, nombre)
    
    if not db_ingrediente:
        print(f"Error: No se encontró el ingrediente '{nombre}' para eliminar.")
        return False
    
    try:
        db.delete(db_ingrediente)
        db.commit()
        print(f"Ingrediente '{nombre}' eliminado con éxito.")
        return True
    except Exception as e:
        db.rollback()
        print(f"Error al eliminar el ingrediente: {e}")
        return False