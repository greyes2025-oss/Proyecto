from Ingrediente import Ingrediente
from typing import List, Dict

def normalizar_nombre(nombre: str) -> str:
    return nombre.strip().title()

class Stock:
    def __init__(self):
        self.ingredientes: Dict[str, Ingrediente] = {}

    def agregar(self, nombre: str, unidad: str, cantidad: float):
        nombre = normalizar_nombre(nombre)
        unidad = unidad.strip().lower() if unidad else None

        if nombre in self.ingredientes:
            self.ingredientes[nombre].cantidad += cantidad
        else:
            self.ingredientes[nombre] = Ingrediente(nombre=nombre, unidad=unidad, cantidad=cantidad)

    def eliminar(self, nombre_ingrediente: str) -> bool:
        nombre_ingrediente = normalizar_nombre(nombre_ingrediente)
        if nombre_ingrediente in self.ingredientes:
            del self.ingredientes[nombre_ingrediente]
            return True
        return False

    def descontar(self, nombre_ingrediente: str, cantidad_a_descontar: float) -> bool:
        nombre_ingrediente = normalizar_nombre(nombre_ingrediente)
        if nombre_ingrediente in self.ingredientes and self.ingredientes[nombre_ingrediente].cantidad >= cantidad_a_descontar:
            self.ingredientes[nombre_ingrediente].cantidad -= cantidad_a_descontar
            return True
        return False

    def get_stock_list(self) -> List[Ingrediente]:
        return list(self.ingredientes.values())
