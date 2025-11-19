# IMenu.py
from typing import Protocol, List
from Ingrediente import Ingrediente

class IMenu(Protocol):
    nombre: str
    ingredientes: List[Ingrediente]
    precio: float
    icono_path: str
    cantidad: int

def calcular_total(self) -> float:
    ...