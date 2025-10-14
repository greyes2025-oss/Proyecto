# Archivo: Stock.py
from Ingrediente import Ingrediente
from typing import List, Dict

class Stock:
    def __init__(self):
        """
        Constructor de la clase Stock
        """
        self.ingredientes: Dict[str, Ingrediente] = {}

    def agregar(self, nombre: str, unidad: str, cantidad: float):
        """
        Agrega un nuevo ingrediente al stock o actualiza la cantidad si ya existe
        """
    
        if nombre in self.ingredientes:
            self.ingredientes[nombre].cantidad += cantidad
        else:
            self.ingredientes[nombre] = Ingrediente(nombre=nombre, unidad=unidad, cantidad=cantidad)

    def eliminar(self, nombre_ingrediente: str) -> bool:
        """
        Elimina un ingrediente del stock por su nombre
        """

        if nombre_ingrediente in self.ingredientes:
            del self.ingredientes[nombre_ingrediente]
            return True
        return False

    def descontar(self, nombre_ingrediente: str, cantidad_a_descontar: float) -> bool:
        """
        Reduce la cantidad de un ingrediente especifico
        """
        
        if nombre_ingrediente in self.ingredientes and self.ingredientes[nombre_ingrediente].cantidad >= cantidad_a_descontar:
            self.ingredientes[nombre_ingrediente].cantidad -= cantidad_a_descontar
            return True
        return False

    def get_stock_list(self) -> List[Ingrediente]:
        """
        Devuelve una lista de todos los objetos ingrediente en el stock
        """
        return list(self.ingredientes.values())
    