from ElementoMenu import CrearMenu 

class Pedido:
    def __init__(self):
        self.menus = []  

    def agregar_menu(self, menu: CrearMenu): #agregar un menu al pedido
        for i in self.menus:
            if i.nombre == menu.nombre:
                i.cantidad += 1
                return
            
        #si no existe lo agrega
        menu.cantidad = 1
        self.menus.append(menu)

    def eliminar_menu(self, nombre_menu: str): #eliminar un menu del pedido por su nombre
        for m in self.menus:
            if m.nombre == nombre_menu:
                if m.cantidad > 1:
                    m.cantidad -= 1
                    return
                
                else:
                    self.menus.remove(m) #elimina el menu si la cantidad es 1
                return True
        return False

    def mostrar_pedido(self): #devuleve una lista con los menus del pedido
        return[(m.nombre, m.cantidad, m.precio) for m in self.menus] #tupla con nombre, cantidad y precio
    

    def calcular_total(self) -> int: #calcula el total del pedido
        total = 0
        for m in self.menus:
            total += m.precio * m.cantidad
        return total