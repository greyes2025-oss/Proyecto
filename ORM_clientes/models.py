from sqlalchemy import Column, Integer, String, Float, ForeignKey, Table, DateTime # <--- AÑADIDO: DateTime
from sqlalchemy.orm import relationship
from datetime import datetime # <--- AÑADIDO: datetime
from database import Base 

# --- Modelo de Ingrediente
class Ingrediente(Base):
    __tablename__ = "ingredientes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), unique=True, nullable=False, index=True)
    stock = Column(Float, nullable=False, default=0.0) 

    menus_donde_aparece = relationship("MenuIngrediente", back_populates="ingrediente")
    
    def __repr__(self):
        return f"Ingrediente(id={self.id}, nombre={self.nombre}, stock={self.stock})"


# ---  Modelo de Cliente
class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)

    pedidos = relationship("Pedido", back_populates="cliente")

    def __repr__(self):
        return f"<Cliente(id={self.id}, nombre='{self.nombre}', email='{self.email}')>"


# 1. Objeto de Asociacion (Menu <-> Ingrediente)
class MenuIngrediente(Base):
    __tablename__ = "menu_ingredientes"
    menu_id = Column(Integer, ForeignKey("menus.id"), primary_key=True)
    ingrediente_id = Column(Integer, ForeignKey("ingredientes.id"), primary_key=True)
    cantidad = Column(Float, nullable=False) 

    ingrediente = relationship("Ingrediente", back_populates="menus_donde_aparece")
    menu = relationship("Menu", back_populates="items_receta")

# 2. Clase Menu
class Menu(Base):
    __tablename__ = "menus"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), unique=True, nullable=False)
    descripcion = Column(String(255))
    precio = Column(Float, nullable=False)
    
    items_receta = relationship("MenuIngrediente", back_populates="menu", cascade="all, delete-orphan")
    pedidos_donde_aparece = relationship("PedidoMenu", back_populates="menu")

    def __repr__(self):
        return f"<Menu(id={self.id}, nombre='{self.nombre}', precio={self.precio})>"

# 3. Objeto de Asociacion (Pedido <-> Menu)
class PedidoMenu(Base):
    __tablename__ = "pedido_menus"
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), primary_key=True)
    menu_id = Column(Integer, ForeignKey("menus.id"), primary_key=True)
    cantidad = Column(Integer, nullable=False) 

    menu = relationship("Menu", back_populates="pedidos_donde_aparece")
    pedido = relationship("Pedido", back_populates="items_comprados")

# 4. Clase Pedido
class Pedido(Base):
    __tablename__ = "pedidos"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # CRÍTICO: CAMBIADO de String(100) a DateTime
    fecha = Column(DateTime, nullable=False, default=datetime.now) 
    
    total = Column(Float, nullable=False)
    
    cliente_id = Column(Integer, ForeignKey('clientes.id'))
    
    cliente = relationship("Cliente", back_populates="pedidos")
    items_comprados = relationship("PedidoMenu", back_populates="pedido")

    def __repr__(self):
        return f"<Pedido(id={self.id}, cliente_id={self.cliente_id}, total={self.total})>"