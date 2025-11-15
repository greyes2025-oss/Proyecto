from sqlalchemy import Column, Integer, String, Float, ForeignKey, Table
from sqlalchemy.orm import relationship
from database import Base #importamos la base de modelos

# --- Modelo de Ingrediente
class Ingrediente(Base):
    #definimos el nombre de la tabla
    __tablename__ = "ingredientes"

    #definimos las columnas
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), unique=True, nullable=False, index=True)
    
    # cantidad > stock 
    stock = Column(Float, nullable=False, default=0.0) 

    # Relacion: Un ingrediente esta en muchos items de menu
    menus_donde_aparece = relationship("MenuIngrediente", back_populates="ingrediente")
    
    def __repr__(self):
        # Actualizado el repr
        return f"Ingrediente(id={self.id}, nombre={self.nombre}, stock={self.stock})"


# ---  Modelo de Cliente
class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)


    # Relacion: Un cliente puede tener muchos pedidos
    pedidos = relationship("Pedido", back_populates="cliente")

    def __repr__(self):
        return f"<Cliente(id={self.id}, nombre='{self.nombre}', email='{self.email}')>"


# 1. Objeto de Asociacion (Menu <-> Ingrediente)
#    Guarda la cantidad de un ingrediente en un menu
class MenuIngrediente(Base):
    __tablename__ = "menu_ingredientes"
    menu_id = Column(Integer, ForeignKey("menus.id"), primary_key=True)
    ingrediente_id = Column(Integer, ForeignKey("ingredientes.id"), primary_key=True)
    cantidad = Column(Float, nullable=False) # Ej: 1 (pan), 0.5 (palta)

    # Relaciones
    ingrediente = relationship("Ingrediente", back_populates="menus_donde_aparece")
    menu = relationship("Menu", back_populates="items_receta")

# 2. Clase Menu
class Menu(Base):
    __tablename__ = "menus"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), unique=True, nullable=False)
    descripcion = Column(String(255))
    precio = Column(Float, nullable=False)
    
    # Relacion: Un menu tiene muchos "items" (ingredientes y cantidades)
    items_receta = relationship("MenuIngrediente", back_populates="menu")
    
    # Relacion: Un menu puede estar en muchos pedidos
    pedidos_donde_aparece = relationship("PedidoMenu", back_populates="menu")

    def __repr__(self):
        return f"<Menu(id={self.id}, nombre='{self.nombre}', precio={self.precio})>"

# 3. Objeto de Asociacion (Pedido <-> Menu)
#    Guarda la cantidad de un menu en un pedido [cite: 69]
class PedidoMenu(Base):
    __tablename__ = "pedido_menus"
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), primary_key=True)
    menu_id = Column(Integer, ForeignKey("menus.id"), primary_key=True)
    cantidad = Column(Integer, nullable=False) # Ej: 2 (para 2 completos)

    # Relaciones
    menu = relationship("Menu", back_populates="pedidos_donde_aparece")
    pedido = relationship("Pedido", back_populates="items_comprados")

# 4. Clase Pedido
class Pedido(Base):
    __tablename__ = "pedidos"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    fecha = Column(String(100), nullable=False) # Mantenido como String por simplicidad
    total = Column(Float, nullable=False)
    
    # Clave foranea para la relacion con Cliente
    cliente_id = Column(Integer, ForeignKey('clientes.id'))
    
    # Relacion: Un pedido pertenece a UN cliente
    cliente = relationship("Cliente", back_populates="pedidos")
    
    # Relacion: Un pedido tiene muchos "items" (menus y cantidades)
    items_comprados = relationship("PedidoMenu", back_populates="pedido")

    def __repr__(self):
        return f"<Pedido(id={self.id}, cliente_id={self.cliente_id}, total={self.total})>"