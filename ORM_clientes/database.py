import os 
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base   

#creamos el nombre del archivo de la bd
database_archivo = "restaurante.db"

#creamos la ruta absoluta del archivo
ruta_base_datos = os.path.abspath(os.path.dirname(__file__))

#creamos la url de conexion para sqlite
database_url = f"sqlite:///{os.path.join(ruta_base_datos, database_archivo)}"

#----------------------------------

#creamos el motor de la base de datos
engine = create_engine(
    database_url,
    echo=True,  #para ver las consultas que se ejecutan
    connect_args={"check_same_thread": False}, #para sqlite
    poolclass="StaticPool" 
    )

#creamos la sesion
SessionLocal = sessionmaker(
    bind=engine, #para enlazar el motor
    autocommit=False, 
    autoflush=False, #para que no se guarden los cambios automaticamente
)

#creamos la base de modelos
class Base(declarative_base()):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()