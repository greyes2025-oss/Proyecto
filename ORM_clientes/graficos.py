# Archivo: graficos.py

import matplotlib.pyplot as plt
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Pedido, PedidoMenu, Menu, MenuIngrediente, Ingrediente
from datetime import datetime

# Configuración para que los gráficos se vean bien en fondo oscuro
plt.style.use('dark_background')

# --- Función Auxiliar para Ventas (CORREGIDA) ---
def obtener_datos_ventas(db: Session, periodo: str):
    """
    Agrupa las ventas por fecha (diaria, mensual, anual).
    Retorna dos listas: etiquetas (fechas) y valores (total $).
    """
    pedidos = db.query(Pedido).all()
    
    datos = {}
    for p in pedidos:
        if not p.fecha: continue 
        
        # CORRECCIÓN: Manejamos la fecha como Objeto o como String
        # para evitar el error 'not subscriptable'.
        fecha_obj = p.fecha
        
        # Si por alguna razón llega como string, lo convertimos a objeto
        if isinstance(fecha_obj, str):
            try:
                # Intentamos parsear formatos comunes
                if len(fecha_obj) > 10:
                    fecha_obj = datetime.strptime(fecha_obj, "%Y-%m-%d %H:%M:%S")
                else:
                    fecha_obj = datetime.strptime(fecha_obj, "%Y-%m-%d")
            except:
                continue # Si falla, saltamos este pedido

        # Ahora generamos la "key" (la etiqueta del gráfico) usando strftime
        if periodo == 'mensual' or periodo == 'month':
            key = fecha_obj.strftime('%Y-%m') # Año-Mes
        elif periodo == 'anual' or periodo == 'year':
            key = fecha_obj.strftime('%Y')    # Año
        else:
            key = fecha_obj.strftime('%Y-%m-%d') # Diario (default)

        datos[key] = datos.get(key, 0) + p.total

    # Ordenar por fecha
    fechas_ordenadas = sorted(datos.keys())
    totales = [datos[k] for k in fechas_ordenadas]
    
    return fechas_ordenadas, totales

# --- 1. Gráfico de Ventas (Barras) ---
# En graficos.py

def generar_grafico_ventas(db: Session, tipo: str):
    # Mapeamos los nombres del combo box a los internos
    tipo_interno = "day"
    titulo_bonito = "Diarias" # Default

    if "Mensual" in tipo or tipo == "month": 
        tipo_interno = "month"
        titulo_bonito = "Mensuales"
    elif "Anual" in tipo or tipo == "year": 
        tipo_interno = "year"
        titulo_bonito = "Anuales"
    elif "Diaria" in tipo or tipo == "day":
        tipo_interno = "day"
        titulo_bonito = "Diarias"

    x, y = obtener_datos_ventas(db, tipo_interno)
    
    if not x: return None 

    fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
    ax.bar(x, y, color='#1f77b4') 
    
    # Usamos el título bonito en español
    ax.set_title(f"Ventas {titulo_bonito}")
    ax.set_ylabel("Total ($)")
    ax.set_xlabel("Fecha")
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return fig

# --- 2. Gráfico de Menús (Torta/Pie) ---
def generar_grafico_menus(db: Session):
    resultados = db.query(Menu.nombre, func.sum(PedidoMenu.cantidad))\
                   .join(PedidoMenu, Menu.id == PedidoMenu.menu_id)\
                   .group_by(Menu.nombre).all()

    if not resultados: return None

    nombres = [r[0] for r in resultados]
    cantidades = [r[1] for r in resultados]

    fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
    ax.pie(cantidades, labels=nombres, autopct='%1.1f%%', startangle=140)
    ax.set_title("Distribución de Menús Vendidos")
    plt.tight_layout()
    return fig

# --- 3. Gráfico de Ingredientes (Barras Horizontales) ---
def generar_grafico_ingredientes(db: Session):
    pedidos_items = db.query(PedidoMenu).all()
    uso_ingredientes = {}

    if not pedidos_items: return None

    for item in pedidos_items:
        menu = item.menu
        cantidad_comprada = item.cantidad
        
        if not menu: continue
        
        for receta in menu.items_receta:
            nombre_ing = receta.ingrediente.nombre
            cantidad_usada = receta.cantidad * cantidad_comprada
            uso_ingredientes[nombre_ing] = uso_ingredientes.get(nombre_ing, 0) + cantidad_usada

    if not uso_ingredientes: return None

    nombres = list(uso_ingredientes.keys())
    totales = list(uso_ingredientes.values())

    fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
    ax.barh(nombres, totales, color='#2ca02c') 
    ax.set_title("Uso Total de Ingredientes")
    ax.set_xlabel("Cantidad Consumida (Unidades/Kg)")
    plt.tight_layout()
    return fig 