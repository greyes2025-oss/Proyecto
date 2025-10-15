# ElementoMenu.py
from IMenu import IMenu
from typing import List
from Ingrediente import Ingrediente

class CrearMenu(IMenu):
    def __init__(self, nombre: str, ingredientes: List[Ingrediente], precio: float, icono_path: str = None, cantidad: int = 1):
        self.nombre = nombre
        self.ingredientes = ingredientes
        self.precio = precio
        self.icono_path = icono_path
        self.cantidad = cantidad
