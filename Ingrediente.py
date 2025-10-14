# Ingrediente.py
from dataclasses import dataclass
from typing import Optional

@dataclass(eq=True, frozen=False)

class Ingrediente:
    nombre: str
    unidad: Optional[str]  
    cantidad: float          

    def __post_init__(self):
        self.cantidad = int(self.cantidad) #Convertir a int en caso de que venga como string

        if self.cantidad < 0:
            raise ValueError("La cantidad no puede ser negativa")
        
        self.nombre = self.nombre.strip().title()  # Normalizar el nombre, quitar espacios y poner en mayuscula la primera letra
        if self.unidad:
            self.unidad = self.unidad.strip().lower()  # Normalizar la unidad, quitar espacios y poner en minuscula

    def __str__(self):
        # Representacion del ingrediente
        if self.unidad:
            return f"{self.nombre} ({self.unidad}) x {self.cantidad}"
        return f"{self.nombre} x {self.cantidad}"