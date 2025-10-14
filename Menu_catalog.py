# menu_catalog.py
from typing import List
from ElementoMenu import CrearMenu
from Ingrediente import Ingrediente
from IMenu import IMenu

def get_default_menus() -> List[IMenu]:
    return [
        CrearMenu(
            "Completo",
            [
                Ingrediente("Vienesa","unid", 1),
                Ingrediente("Pan de completo","unid", 1),
                Ingrediente("Palta","unid",1),
                Ingrediente("Tomate","unid",1),
            ],
            precio=1800,
        ),
        CrearMenu(
            "Hamburguesa",
            [
                Ingrediente("Churrasco de carne","unid", 1),
                Ingrediente("Pan de hamburguesa","unid", 1),
                Ingrediente("Lamina de queso","unid",1),
            ],
            precio=3500,
        ),
        CrearMenu(
            "Empanada",
            [
                Ingrediente("Carne","unid", 1),
                Ingrediente("Cebolla","unid", 1),
                Ingrediente("Masa de empanada","unid",1),
            ],
            precio=1000,
        ),
        CrearMenu(
            "Papas fritas",
            [
                Ingrediente("Papas","unid", 5),
                
            ],
            precio=500
        ),
        CrearMenu(
            "Pepsi",
            [
                Ingrediente("Pepsi","unid", 1),
            ],
            precio=1100
        ),
        CrearMenu(
            "Coca cola",
            [
                Ingrediente("Coca cola","unid", 1),
            ],
            precio=1200
        ),
        CrearMenu(
            "Panqueques",
            [
                Ingrediente("Panqueques","unid", 2),
                Ingrediente("Manjar","unid", 1),
                Ingrediente("Azucar flor","unid",1),
            ],
            precio=2000
        ),
        CrearMenu(
            "Pollo frito",
            [
                Ingrediente("Presa de pollo","unid", 1),
                Ingrediente("Harina","unid", 1),
                Ingrediente("Aceite","unid",1),
            ],
            precio=2800
        ),
        CrearMenu(
            "Ensalada Mixta",
            [
                Ingrediente("Lechuga","unid", 1),
                Ingrediente("Tomate","unid", 1),
                Ingrediente("Zanahoria","unid",1),
            ],
            precio=1500
        ),
        CrearMenu(
            "Chorrillana",
            [
                Ingrediente("Carne","unid", 2),
                Ingrediente("Huevos","unid", 2),
                Ingrediente("Papas","unid", 3),
                Ingrediente("Cebolla","unid",1),
            ],
            precio=3500
        )
    ]