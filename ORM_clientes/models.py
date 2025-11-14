from sqlalchemy import Column, Integer, String, Float,  ForeignKey
from sqlalchemy.orm import relationship
from .database import Base #importamos la base de modelos

class Ingredientes(Base):
    #definimos el nombre de la tabla
    __tablename__ = "ingredientes"

    #definimos las columnas

    id = Column(Integer, primary_key=True, autoincrement=True)

    nombre = Column(String(100), unique=True, nullable=False, index=True)

    unidad = Column(String(50), nullable=True)

    cantidad = Column(Float, nullable=True, default=0.0)

    #relaciones para ocupar mas trde 
    
    def __repr__(self):
        return f"Ingrediente(id={self.id}, nombre={self.nombre}, unidad={self.unidad}, cantidad={self.cantidad})"



