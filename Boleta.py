from fpdf import FPDF
from datetime import datetime

class BoletaFacade:
    def __init__(self, pedido, nombre_negocio="Restaurante", rut="12345678-9",
                 direccion="Calle Falsa 123", telefono="+56 9 1234 5678"):
        self.pedido = pedido
        self.nombre_negocio = nombre_negocio
        self.rut = rut
        self.direccion = direccion
        self.telefono = telefono

    def generar_detalle_boleta(self):
        self.detalle = ""
        for item in self.pedido.menus:
            subtotal = item.precio * item.cantidad
            self.detalle += f"{item.nombre:<30} {item.cantidad:<10} ${item.precio:<10} ${subtotal:<10}\n"

        self.subtotal = sum(item.precio * item.cantidad for item in self.pedido.menus)
        self.iva = int(self.subtotal * 0.19)
        self.total = self.subtotal + self.iva

    def crear_pdf(self):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Boleta Restaurante", ln=True)
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 10, f"Razón Social: {self.nombre_negocio}", ln=True)
        pdf.cell(0, 10, f"RUT: {self.rut}", ln=True)
        pdf.cell(0, 10, f"Dirección: {self.direccion}", ln=True)
        pdf.cell(0, 10, f"Teléfono: {self.telefono}", ln=True)
        pdf.cell(0, 10, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", ln=True)
        pdf.ln(10)

        # Encabezado de tabla
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(70, 10, "Nombre", border=1)
        pdf.cell(20, 10, "Cant.", border=1)
        pdf.cell(35, 10, "Precio", border=1)
        pdf.cell(30, 10, "Subtotal", border=1)
        pdf.ln()

        # Detalle de items
        pdf.set_font("Arial", '', 12)
        for item in self.pedido.menus:
            subtotal = item.precio * item.cantidad
            pdf.cell(70, 10, item.nombre, border=1)
            pdf.cell(20, 10, str(item.cantidad), border=1)
            pdf.cell(35, 10, f"${item.precio}", border=1)
            pdf.cell(30, 10, f"${subtotal}", border=1)
            pdf.ln()

        # Totales
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(120, 10, "Subtotal:", 0, 0, 'R')
        pdf.cell(30, 10, f"${self.subtotal}", ln=True)
        pdf.cell(120, 10, "IVA (19%):", 0, 0, 'R')
        pdf.cell(30, 10, f"${self.iva}", ln=True)
        pdf.cell(120, 10, "Total:", 0, 0, 'R')
        pdf.cell(30, 10, f"${self.total}", ln=True)

        # Mensaje final
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(0, 10, "Gracias por su compra. Para consultas llámenos al +56 9 777 5678.", 0, 1, 'C')
        pdf.cell(0, 10, "Los productos adquiridos no tienen garantía.", 0, 1, 'C')

        pdf_filename = "boleta.pdf"
        pdf.output(pdf_filename)
        return pdf_filename

    def generar_boleta(self):
        self.generar_detalle_boleta()
        return self.crear_pdf()
