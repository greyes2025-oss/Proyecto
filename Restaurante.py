from ElementoMenu import CrearMenu
import customtkinter as ctk
from tkinter import ttk, Toplevel, Label, messagebox
from Ingrediente import Ingrediente
from Stock import Stock
import re
from PIL import Image
from CTkMessagebox import CTkMessagebox
from Pedido import Pedido
from BoletaFacade import BoletaFacade
import pandas as pd
from tkinter import filedialog
from Menu_catalog import get_default_menus
from menu_pdf import create_menu_pdf
from ctk_pdf_viewer import CTkPDFViewer
import os
from tkinter.font import nametofont

class AplicacionConPestanas(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Gestión de ingredientes y pedidos")
        self.geometry("870x700")
        nametofont("TkHeadingFont").configure(size=14)
        nametofont("TkDefaultFont").configure(size=11)

        self.stock = Stock()
        self.menus_creados = set()

        self.pedido = Pedido()

        self.menus = get_default_menus()  
  
        self.tabview = ctk.CTkTabview(self,command=self.on_tab_change)
        self.tabview.pack(expand=True, fill="both", padx=10, pady=10)

        self.crear_pestanas()
    
    def normalizar_nombre(self,nombre: str) -> str:
        return nombre.strip().title()

    def on_tab_change(self):
        selected_tab = self.tabview.get()

        if selected_tab == "carga de ingredientes":
            print('carga de ingredientes')
        if selected_tab == "Stock":
            self.actualizar_treeview()
        if selected_tab == "Pedido":
            self.actualizar_treeview()
            self.actualizar_treeview_pedido()
            self.cargar_tarjetas_pedido() 
            print('pedido')
        if selected_tab == "Carta restorante":
            self.actualizar_treeview()
            print('Carta restorante')
        if selected_tab == "Boleta":
            self.actualizar_treeview()
            print('Boleta')
        
    def crear_pestanas(self):
        self.tab3 = self.tabview.add("carga de ingredientes")  
        self.tab1 = self.tabview.add("Stock")
        self.tab4 = self.tabview.add("Carta restorante")  
        self.tab2 = self.tabview.add("Pedido")
        self.tab5 = self.tabview.add("Boleta")
        
        self.configurar_pestana1()
        self.configurar_pestana2()
        self.configurar_pestana3()
        self._configurar_pestana_crear_menu()
        self._configurar_pestana_ver_boleta()

    def cargar_tarjetas_pedido(self):
        #limpiar tarjetas anteriores
        for u in tarjetas_frame.winfo_children():
            u.destroy()

        self.menus_creados.clear()

        #crear tarjetas para cada menu
        for menu in self.menus:
            self.crear_tarjeta(menu, True)
            self.menus_creados.add(menu.nombre)

    def configurar_pestana3(self):
        label = ctk.CTkLabel(self.tab3, text="Carga de archivo CSV")
        label.pack(pady=20)
        #boton de agregar csv
        boton_cargar_csv = ctk.CTkButton(self.tab3, text="Cargar CSV", fg_color="#1976D2", text_color="white",command=self.cargar_csv)

        boton_cargar_csv.pack(pady=10) 

        #frame para la tabla del csv
        self.frame_tabla_csv = ctk.CTkFrame(self.tab3)
        self.frame_tabla_csv.pack(fill="both", expand=True, padx=10, pady=10)

        self.df_csv = None    #DataFrame cargado desde el CSV
        self.tabla_csv = None  #Tabla Treeview para mostrar el DataFrame

        self.boton_agregar_stock = ctk.CTkButton(self.frame_tabla_csv, text="Agregar al Stock")
        self.boton_agregar_stock.configure(command=self.agregar_csv_al_stock) #####
        self.boton_agregar_stock.pack(side="bottom", pady=10)
 
    def agregar_csv_al_stock(self):
        if self.df_csv is None:
            CTkMessagebox(title="Error", message="Primero debes cargar un archivo CSV.", icon="warning")
            return

        if 'nombre' not in self.df_csv.columns or 'cantidad' not in self.df_csv.columns:
            CTkMessagebox(title="Error", message="El CSV debe tener columnas 'nombre' y 'cantidad'.", icon="warning")
            return

        for _, row in self.df_csv.iterrows():
            nombre = self.normalizar_nombre(str(row['nombre']))
            cantidad = int(row['cantidad'])
            unidad = str(row['unidad']).strip().lower() if 'unidad' in row and row['unidad'] else None

            self.stock.agregar(nombre, unidad, cantidad)

        CTkMessagebox(title="Stock Actualizado", message="Ingredientes agregados al stock correctamente.", icon="info")
        self.actualizar_treeview()


    def cargar_csv(self): ###
        #abirir un dialogo para seleccionar el archivo
        archivo = filedialog.askopenfilename(
            title="Seleccionar archivo CSV",
            filetypes=(("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*"))
        )
        if not archivo:
            return #si el usuario cancela
        
        try:
            self.df_csv = pd.read_csv(archivo) #LEER el csv con pandas

            #mostrar en la tabla del tab
            self.mostrar_dataframe_en_tabla(self.df_csv)
            #habilitar el boton de agregar al stock
            self.boton_agregar_stock.configure(command=self.agregar_csv_al_stock)

        except Exception as e:
            CTkMessagebox(title="Error", message=f"No se pudo cargar el archivo CSV.\n{e}", icon="warning")
        
        
    def mostrar_dataframe_en_tabla(self, df):
        if self.tabla_csv:
            self.tabla_csv.destroy()

        self.tabla_csv = ttk.Treeview(self.frame_tabla_csv, columns=list(df.columns), show="headings")
        for col in df.columns:
            self.tabla_csv.heading(col, text=col)
            self.tabla_csv.column(col, width=100, anchor="center")


        for _, row in df.iterrows():
            self.tabla_csv.insert("", "end", values=list(row))

        self.tabla_csv.pack(expand=True, fill="both", padx=10, pady=10)

    def actualizar_treeview_pedido(self):
        for item in self.treeview_menu.get_children():
            self.treeview_menu.delete(item)

        for menu in self.pedido.menus:
            self.treeview_menu.insert("", "end", values=(menu.nombre, menu.cantidad, f"${menu.precio:.2f}"))
            
    def _configurar_pestana_crear_menu(self):
        contenedor = ctk.CTkFrame(self.tab4)
        contenedor.pack(expand=True, fill="both", padx=10, pady=10)

        boton_menu = ctk.CTkButton(
            contenedor,
            text="Generar Carta (PDF)",
            command=self.generar_y_mostrar_carta_pdf
        )
        boton_menu.pack(pady=10)

        self.pdf_frame_carta = ctk.CTkFrame(contenedor)
        self.pdf_frame_carta.pack(expand=True, fill="both", padx=10, pady=10)

        self.pdf_viewer_carta = None
    def generar_y_mostrar_carta_pdf(self):
        try:
            pdf_path = "carta.pdf"
            create_menu_pdf(self.menus, pdf_path,
                titulo_negocio="Restaurante",
                subtitulo="Carta Primavera 2025",
                moneda="$")
            
            if self.pdf_viewer_carta is not None:
                try:
                    self.pdf_viewer_carta.pack_forget()
                    self.pdf_viewer_carta.destroy()
                except Exception:
                    pass
                self.pdf_viewer_carta = None

            abs_pdf = os.path.abspath(pdf_path)
            self.pdf_viewer_carta = CTkPDFViewer(self.pdf_frame_carta, file=abs_pdf)
            self.pdf_viewer_carta.pack(expand=True, fill="both")

        except Exception as e:
            CTkMessagebox(title="Error", message=f"No se pudo generar/mostrar la carta.\n{e}", icon="warning")

    def _configurar_pestana_ver_boleta(self):
        contenedor = ctk.CTkFrame(self.tab5)
        contenedor.pack(expand=True, fill="both", padx=10, pady=10)

        boton_boleta = ctk.CTkButton(
            contenedor,
            text="Generar y Mostrar Boleta (PDF)",
            command=self.generar_boleta  # el mismo metodo generara y mostrara la boleta
        )
        boton_boleta.pack(pady=10)

        self.pdf_frame_boleta = ctk.CTkFrame(contenedor)
        self.pdf_frame_boleta.pack(expand=True, fill="both", padx=10, pady=10)

    # inicializamos la referencia a None 
        self.pdf_viewer_boleta = None

        
#----------------------------------------------------------------------------------------------------------
    def generar_boleta(self):
    # Validacion: debe haber menus en el pedido
        if not self.pedido.menus:
            CTkMessagebox(title="Error", message="No hay menús en el pedido para generar una boleta.", icon="warning")
            return

        try:
        # Generar boleta (BoletaFacade puede ser una clase con metodo generar_boleta)
            boleta = BoletaFacade(self.pedido)
            resultado = boleta.generar_boleta()  # puede devolver ruta relativa, absoluta, o nombre

        # Normalizar ruta resultante
            if not resultado:
                raise RuntimeError("BoletaFacade no devolvió ruta de archivo.")
            ruta = resultado
        # Si la ruta no es absoluta, conviértela
            if not os.path.isabs(ruta):
                ruta = os.path.abspath(ruta)

        # Guardamos la ruta para uso futuro
            self.ruta_boleta = ruta

        # Mostrar mensaje de exito en terminal y con ventana (opcional)
            print(f"Boleta generada en: {self.ruta_boleta}")
            CTkMessagebox(title="Éxito", message="Boleta generada correctamente.", icon="info")

        # Si ya hay un PDF cargado en el viewer, eliminarlo primero
            try:
                if hasattr(self, "pdf_viewer_boleta") and self.pdf_viewer_boleta is not None:
                    self.pdf_viewer_boleta.pack_forget()
                    self.pdf_viewer_boleta.destroy()
                    self.pdf_viewer_boleta = None
            except Exception:
                pass

        # Verificar que el archivo exista
            if not os.path.exists(self.ruta_boleta):
                raise FileNotFoundError(f"Archivo no encontrado: {self.ruta_boleta}")

        # Crear y mostrar el visor PDF dentro de self.pdf_frame_boleta
            self.pdf_viewer_boleta = CTkPDFViewer(self.pdf_frame_boleta, file=self.ruta_boleta)
            self.pdf_viewer_boleta.pack(expand=True, fill="both")

        # Asegurar que la pestaña Boleta quede visible (opcional)
            try:
                self.tabview.set("Boleta")
            except Exception:
                pass

        except Exception as e:
        # Mostrar error en terminal y con mensaje
            print("ERROR generando/mostrando boleta:", e)
            CTkMessagebox(title="Error", message=f"No se pudo generar/mostrar la boleta.\n{e}", icon="warning")


    def ver_boleta(self):
        if not hasattr(self, "ruta_boleta") or not os.path.exists(self.ruta_boleta):
            CTkMessagebox(title="Error", message="No se ha generado la boleta aún.", icon="warning")
            return

    # Si ya hay un PDF cargado, eliminarlo
        if hasattr(self, "pdf_viewer_boleta") and self.pdf_viewer_boleta is not None:
            self.pdf_viewer_boleta.pack_forget()
            self.pdf_viewer_boleta.destroy()
            self.pdf_viewer_boleta = None

    # Mostrar PDF
        self.pdf_viewer_boleta = CTkPDFViewer(self.pdf_frame_boleta, file=self.ruta_boleta)
        self.pdf_viewer_boleta.pack(expand=True, fill="both")


    def configurar_pestana1(self):
        # Dividir la Pestaña 1 en dos frames
        frame_formulario = ctk.CTkFrame(self.tab1)
        frame_formulario.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        frame_treeview = ctk.CTkFrame(self.tab1)
        frame_treeview.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Formulario en el primer frame
        label_nombre = ctk.CTkLabel(frame_formulario, text="Nombre del Ingrediente:")
        label_nombre.pack(pady=5)
        self.entry_nombre = ctk.CTkEntry(frame_formulario)
        self.entry_nombre.pack(pady=5)

        label_cantidad = ctk.CTkLabel(frame_formulario, text="Unidad:")
        label_cantidad.pack(pady=5)
        self.combo_unidad = ctk.CTkComboBox(frame_formulario, values=["kg", "unid"])
        self.combo_unidad.pack(pady=5)

        label_cantidad = ctk.CTkLabel(frame_formulario, text="Cantidad:")
        label_cantidad.pack(pady=5)
        self.entry_cantidad = ctk.CTkEntry(frame_formulario)
        self.entry_cantidad.pack(pady=5)

        self.boton_ingresar = ctk.CTkButton(frame_formulario, text="Ingresar Ingrediente")
        self.boton_ingresar.configure(command=self.ingresar_ingrediente)
        self.boton_ingresar.pack(pady=10)

        self.boton_eliminar = ctk.CTkButton(frame_treeview, text="Eliminar Ingrediente", fg_color="black", text_color="white")
        self.boton_eliminar.configure(command=self.eliminar_ingrediente)
        self.boton_eliminar.pack(pady=10)

        self.tree = ttk.Treeview(self.tab1, columns=("Nombre", "Unidad","Cantidad"), show="headings",height=25)
        
        self.tree.heading("Nombre", text="Nombre")
        self.tree.heading("Unidad", text="Unidad")
        self.tree.heading("Cantidad", text="Cantidad")
        self.tree.pack(expand=True, fill="both", padx=10, pady=10)

        self.boton_generar_menu = ctk.CTkButton(frame_treeview, text="Generar Menú", command=self.generar_menus)
        self.boton_generar_menu.pack(pady=10)

    def tarjeta_click(self, event, menu):
        suficiente_stock = True

        for ingrediente in menu.ingredientes:
            stock = self.stock.ingredientes.get(self.normalizar_nombre(ingrediente.nombre))
            if not stock or stock.cantidad < ingrediente.cantidad:
                suficiente_stock = False
                break

        if suficiente_stock:
        # Descontar ingredientes del stock por cada menú agregado
            for ingrediente in menu.ingredientes:
                self.stock.descontar(self.normalizar_nombre(ingrediente.nombre), ingrediente.cantidad)
        
        # Agregar al pedido sumando cantidades si ya existe
            for m in self.pedido.menus:
                if m.nombre == menu.nombre:
                    m.cantidad += 1
                    break
            else:
                menu_copy = CrearMenu(
                    nombre=menu.nombre,
                    ingredientes=menu.ingredientes,
                    precio=menu.precio,
                    icono_path=menu.icono_path,
                    cantidad=1
                )
                self.pedido.menus.append(menu_copy)

        # Actualizar interfaz
            self.actualizar_treeview_pedido()
            Total = self.pedido.calcular_total()
            self.label_total.configure(text=f"Total: ${Total:.2f}")
            self.actualizar_treeview()  # actualizar stock


            
    def cargar_icono_menu(self, ruta_icono):
        imagen = Image.open(ruta_icono)
        icono_menu = ctk.CTkImage(imagen, size=(64, 64))
        return icono_menu
    
    def generar_menus(self):
    # Llama al metodo .esta_disponible() de cada menú
        disponibles = [m.nombre for m in self.menus if m.esta_disponible(self.stock)]
    
        if not disponibles:
            mensaje = "No hay suficientes ingredientes para preparar ningun menú."
        else:
            mensaje = "Con el stock actual se puede preparar:\n\n- " + "\n- ".join(disponibles)
    
    #ventana emergente
        messagebox.showinfo("Menús Disponibles", mensaje)

    def eliminar_menu(self):
        seleccionado = self.treeview_menu.selection()
        if not seleccionado:
            return  # Si no hay selección, no hace nada

        for item in seleccionado:
            nombre_menu = self.treeview_menu.item(item, "values")[0]

        # Buscar el menu en el pedido
            for menu in self.pedido.menus:
                if menu.nombre == nombre_menu:
                # Devolver todos los ingredientes según la cantidad del menu
                    for ingrediente_necesario in menu.ingredientes:
                        total_a_devolver = ingrediente_necesario.cantidad * menu.cantidad
                        self.stock.agregar(
                            ingrediente_necesario.nombre,
                            ingrediente_necesario.unidad,
                            total_a_devolver
                        )
                # Eliminar completamente el menú del pedido
                    self.pedido.menus.remove(menu)
                    break

    # Actualizar interfaz
        self.actualizar_treeview_pedido()
        Total = self.pedido.calcular_total()
        self.label_total.configure(text=f"Total: ${Total:.2f}")
        self.actualizar_treeview()  # Actualizar stock


    def configurar_pestana2(self):
        frame_superior = ctk.CTkFrame(self.tab2)
        frame_superior.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        frame_intermedio = ctk.CTkFrame(self.tab2)
        frame_intermedio.pack(side="top", fill="x", padx=10, pady=5)

        global tarjetas_frame
        tarjetas_frame = ctk.CTkFrame(frame_superior)
        tarjetas_frame.pack(expand=True, fill="both", padx=10, pady=10)

        self.boton_eliminar_menu = ctk.CTkButton(frame_intermedio, text="Eliminar Menú", command=self.eliminar_menu)
        self.boton_eliminar_menu.pack(side="right", padx=10)

        self.label_total = ctk.CTkLabel(frame_intermedio, text="Total: $0.00", anchor="e", font=("Helvetica", 12, "bold"))
        self.label_total.pack(side="right", padx=10)

        frame_inferior = ctk.CTkFrame(self.tab2)
        frame_inferior.pack(side="bottom", fill="both", expand=True, padx=10, pady=10)

        self.treeview_menu = ttk.Treeview(frame_inferior, columns=("Nombre", "Cantidad", "Precio Unitario"), show="headings")
        self.treeview_menu.heading("Nombre", text="Nombre del Menú")
        self.treeview_menu.heading("Cantidad", text="Cantidad")
        self.treeview_menu.heading("Precio Unitario", text="Precio Unitario")
        self.treeview_menu.pack(expand=True, fill="both", padx=10, pady=10)

        self.boton_generar_boleta=ctk.CTkButton(frame_inferior,text="Generar Boleta",command=self.generar_boleta)
        self.boton_generar_boleta.pack(side="bottom",pady=10)

    def crear_tarjeta(self, menu, suficiente_stock): #####
        num_tarjetas = len(self.menus_creados)
        fila = 0
        columna = num_tarjetas


        tarjeta = ctk.CTkFrame(
            tarjetas_frame,
            corner_radius=10,
            border_width=2,
            border_color="#4CAF50",
            width=64,
            height=140,
            fg_color="gray",
        )
        tarjeta.grid(row=fila, column=columna, padx=15, pady=15, sticky="nsew")

        tarjeta.bind("<Button-1>", lambda event: self.tarjeta_click(event, menu))
        tarjeta.bind("<Enter>", lambda event: tarjeta.configure(border_color="#FF0000"))
        tarjeta.bind("<Leave>", lambda event: tarjeta.configure(border_color="#4CAF50"))

#-------------
        if menu.icono_path:
            icono = self.cargar_icono_menu(menu.icono_path)
            label_icono = ctk.CTkLabel(tarjeta, image=icono, text="")
            label_icono.image = icono  # Mantener una referencia para evitar que se elimine
            label_icono.pack(pady=5)

        #label muestra el nombre del menu
        texto_label = ctk.CTkLabel( # hace que el texto se ajuste al ancho de la tarjeta
            tarjeta,
            text=menu.nombre,
            font=("Helvetica", 12, "bold"), # negrita
            wraplength=100, #ajusta el texto al ancho de la tarjeta
            justify="center",
        )
        texto_label.pack(anchor="center", pady=1)
        texto_label.bind("<Button-1>", lambda event: self.tarjeta_click(event, menu)) #hace que el label tambien sea clickeable

    def validar_nombre(self, nombre):
        if re.match(r"^[a-zA-Z\s]+$", nombre):
            return True
        else:
            CTkMessagebox(title="Error de Validación", message="El nombre debe contener solo letras y espacios.", icon="warning")
            return False

    def validar_cantidad(self, cantidad):
        if cantidad.isdigit():
            return True
        else:
            CTkMessagebox(title="Error de Validación", message="La cantidad debe ser un número entero positivo.", icon="warning")
            return False
#-------------------------------------------------------------------------------#
    def ingresar_ingrediente(self):
        nombre = self.entry_nombre.get().strip()
        unidad = self.combo_unidad.get()
        cantidad_str = self.entry_cantidad.get()

    # Validacion de datos
        if not nombre:
            messagebox.showerror("Error de validacion", "El nombre no puede estar vacio")
            return
        try:
            cantidad = int(cantidad_str)
            if cantidad <= 0:
                messagebox.showerror("Error de validacion", "La cantidad debe ser un numero entero positivo")
                return
        except ValueError:
            messagebox.showerror("Error de validacion", "La cantidad debe ser un número entero valido")
            return
    
    # Llama al matodo de la clase Stock
        self.stock.agregar(nombre, unidad, cantidad)
        messagebox.showinfo("exito", f"'{nombre}' ha sido agregado en el stock")
    
    # Limpia los campos y actualiza la tabla
        self.entry_nombre.delete(0, 'end')
        self.entry_cantidad.delete(0, 'end')
        self.actualizar_treeview()


    
    def eliminar_ingrediente(self):
        seleccionado = self.tree.focus()
        if not seleccionado:
            messagebox.showwarning("Sin selección", "Por favor, selecciona un ingrediente de la tabla para eliminar.")
            return

        nombre_ingrediente = self.normalizar_nombre(self.tree.item(seleccionado)['values'][0])

        if messagebox.askyesno("Confirmar", f"¿Estás seguro de que quieres eliminar '{nombre_ingrediente}'?"):
            self.stock.eliminar(nombre_ingrediente)
            self.actualizar_treeview()


    def actualizar_treeview(self):
    # Limpia la tabla de cualquier dato antiguo
        for item in self.tree.get_children():
            self.tree.delete(item)
    
    # Llama al metodo correcto de la clase Stock
    # para obtener los ingredientes y los añade a la tabla
        for ingrediente in self.stock.get_stock_list():
            self.tree.insert("", "end", values=(ingrediente.nombre, ingrediente.unidad, ingrediente.cantidad))


        
#-------------------------------------modificacion de ingresar ingre, eliminar ingre y actualizar treeview-------------------------
if __name__ == "__main__":
    import customtkinter as ctk
    from tkinter import ttk

    ctk.set_appearance_mode("Dark")  
    ctk.set_default_color_theme("blue") 
    ctk.set_widget_scaling(1.0)
    ctk.set_window_scaling(1.0)

    app = AplicacionConPestanas()

    try:
        style = ttk.Style(app)   
        style.theme_use("clam")
    except Exception:
        pass

    app.mainloop()
