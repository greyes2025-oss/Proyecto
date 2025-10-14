# Archivo: Stock.py
from Ingrediente import Ingrediente
from typing import List, Dict

class Stock:
    def __init__(self):
        """
        constructor de la clase stock.
        Se utiliza un diccionario para un acceso y modificación de datos optimiizada
        La clave es el nombre del ingrediente  y el valor es el objeto ingrediente
        """
        self.ingredientes: Dict[str, Ingrediente] = {}

    def agregar(self, nombre: str, unidad: str, cantidad: float):
        """
        agrega un nuevo ingrediente al stock o actualiza la cantidad si ya existe
        
        """
        # Convertimos el nombre a minusculas
        nombre = nombre.lower()
        
        # Si el ingrediente ya existe se suma la cantidad
        if nombre in self.ingredientes:
            self.ingredientes[nombre].cantidad += cantidad
        # Si es nuevo crea una instancia de ingrediente y la añadimos al diccionario
        else:
            self.ingredientes[nombre] = Ingrediente(nombre=nombre, unidad=unidad, cantidad=cantidad)

    def eliminar(self, nombre_ingrediente: str) -> bool:
        """
        elimina un ingrediente del stock por su nombre
        Devuelve true si se elimino false si no se encontro
        """
        nombre_ingrediente = nombre_ingrediente.lower()
        if nombre_ingrediente in self.ingredientes:
            del self.ingredientes[nombre_ingrediente]
            return True
        return False

    def descontar(self, nombre_ingrediente: str, cantidad_a_descontar: float) -> bool:
        """
        reduce la cantidad de un ingrediente especifico .
        devuelve true si se desconto false si no hay suficiente stock
        """
        nombre_ingrediente = nombre_ingrediente.lower()
        # Comprueba si el ingrediente existe y si hay suficiente cantidad
        if nombre_ingrediente in self.ingredientes and self.ingredientes[nombre_ingrediente].cantidad >= cantidad_a_descontar:
            self.ingredientes[nombre_ingrediente].cantidad -= cantidad_a_descontar
            return True
        return False

    def get_stock_list(self) -> List[Ingrediente]:
        """
        Devuelve una lista de todos los objetos ingrediente en el stock
        """
        return list(self.ingredientes.values())
    