# =======================================================
# Archivo: graficos.py
# Módulo para generar las consultas de reportes estadísticos
# =======================================================

from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from models import Pedido, PedidoMenu, Menu, MenuIngrediente
from datetime import datetime

def _check_data(results, grafico_nombre: str):
    """Funcion auxiliar para verificar si hay datos y reportar el error."""
    if not results:
        # Se imprime a la consola, ya que la GUI maneja el mensaje de "No hay datos disponibles"
        print(f"\n--- [Reporte] No hay datos disponibles para el gráfico: {grafico_nombre} ---")
        return False
    return True

# --------------------------------------------------------------------
# 1. Ventas por Fecha (Diarias, Mensuales, Anuales)
# --------------------------------------------------------------------

def ventas_por_periodo(db: Session, periodo: str):
    """
    Calcula el total de ventas agrupado por el periodo especificado.
    Periodos válidos: 'day', 'month', 'year'. (Usando términos en inglés para func.strftime)
    """
    
    # Define la unidad de tiempo para agrupar (SQLite/SQLAlchemy)
    if periodo == 'day':
        # Agrupa por día específico (YYYY-MM-DD)
        label_group = func.strftime('%Y-%m-%d', Pedido.fecha) 
        nombre_grafico = "Ventas Diarias"
    elif periodo == 'month':
        # Agrupa por mes (YYYY-MM)
        label_group = func.strftime('%Y-%m', Pedido.fecha)
        nombre_grafico = "Ventas Mensuales"
    elif periodo == 'year':
        # Agrupa por año (YYYY)
        label_group = func.strftime('%Y', Pedido.fecha)
        nombre_grafico = "Ventas Anuales"
    else:
        raise ValueError("Período inválido. Use 'day', 'month' o 'year'.")

    try:
        resultados = db.query(
            label_group.label('periodo'),
            func.sum(Pedido.total).label('total_ventas')
        ).filter(
            Pedido.fecha != None # Asegura que solo se consideren pedidos con fecha
        ).group_by(label_group).order_by(label_group).all()

    except Exception as e:
        print(f"Error al generar gráfico de ventas por periodo: {e}")
        return None

    if _check_data(resultados, nombre_grafico):
        # Usa map y lambda para formatear la salida como lista de diccionarios
        return list(map(
            lambda r: {'periodo': r.periodo, 'total_ventas': f"${r.total_ventas:,.2f}"}, 
            resultados
        ))
    return None


# --------------------------------------------------------------------
# 2. Distribución de Menús más Comprados
# --------------------------------------------------------------------

def distribucion_menus_mas_comprados(db: Session):
    """
    Muestra la cantidad total vendida de cada menú.
    """
    nombre_grafico = "Distribución de Menús Comprados"
    
    try:
        # Consulta al ORM: Suma la cantidad comprada (PedidoMenu.cantidad) agrupada por el nombre del Menú.
        resultados = db.query(
            Menu.nombre.label('menu'),
            func.sum(PedidoMenu.cantidad).label('cantidad_vendida')
        ).join(PedidoMenu, Menu.id == PedidoMenu.menu_id) \
        .group_by(Menu.nombre) \
        .order_by(desc('cantidad_vendida')) \
        .all()
        
    except Exception as e:
        print(f"Error al generar gráfico de menús más comprados: {e}")
        return None
        
    if _check_data(resultados, nombre_grafico):
        return list(map(lambda r: {'menu': r.menu, 'cantidad_vendida': int(r.cantidad_vendida)}, resultados))
    return None

# --------------------------------------------------------------------
# 3. Uso de Ingredientes en todos los Pedidos
# --------------------------------------------------------------------

def uso_ingredientes_en_pedidos(db: Session):
    """
    Calcula la cantidad total de cada ingrediente consumida en todos los pedidos.
    """
    nombre_grafico = "Uso Total de Ingredientes"

    try:
        # Consulta al ORM: 
        # Calcula el total consumido: (MenuIngrediente.cantidad * PedidoMenu.cantidad)
        resultados = db.query(
            MenuIngrediente.ingrediente.nombre.label('ingrediente'),
            func.sum(MenuIngrediente.cantidad * PedidoMenu.cantidad).label('cantidad_total_consumida')
        ).join(Menu, Menu.id == MenuIngrediente.menu_id) \
        .join(PedidoMenu, Menu.id == PedidoMenu.menu_id) \
        .group_by(MenuIngrediente.ingrediente.nombre) \
        .order_by(desc('cantidad_total_consumida')) \
        .all()
        
    except Exception as e:
        print(f"Error al generar gráfico de uso de ingredientes: {e}")
        return None
        
    if _check_data(resultados, nombre_grafico):
        # Usa map y lambda para devolver los resultados formateados
        return list(map(
            lambda r: {'ingrediente': r.ingrediente, 'cantidad_consumida': f"{r.cantidad_total_consumida:,.2f}"}, 
            resultados
        ))
    return None