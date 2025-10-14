from ElementoMenu import CrearMenu 
class Pedido:
    def __init__(self):
        self.menus = []  

    def agregar_menu(self, menu: CrearMenu):
        self.menus.append(menu)

    def eliminar_menu(self, nombre_menu: str):
        self.menus = [menu for menu in self.menus if menu.nombre != nombre_menu]

    def mostrar_pedido(self):
        for menu in self.menus:
            print(f"Menu: {menu.nombre}, Precio: {menu.precio}")

    def calcular_total(self) -> float:
        return sum(menu.precio for menu in self.menus)
