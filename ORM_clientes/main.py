from database import engine, Base
import models

def manin():
    #creamos las tablas en la base de datos

    print("Creando las tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)

    print(f"¡Base de datos '{engine.url.database}' y tablas creadas exitosamente!")


if __name__ == "__main__":
    manin()