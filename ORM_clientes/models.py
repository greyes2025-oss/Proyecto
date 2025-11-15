from sqlalchemy import Column, Integer, String, Float,  ForeignKey
from sqlalchemy.orm import relationship
from database import Base #importamos la base de modelos

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


# ---  Modelo de Cliente ---

class Cliente(Base):

    __tablename__ = "clientes"

 

    id = Column(Integer, primary_key=True, autoincrement=True)
    
   
    nombre = Column(String(100), nullable=False)
    
 
    email = Column(String(100), unique=True, nullable=False, index=True)


    #pedidos = relationship("Pedido", back_populates="cliente")

    def __repr__(self):
        return f"<Cliente(id={self.id}, nombre='{self.nombre}', email='{self.email}')>"