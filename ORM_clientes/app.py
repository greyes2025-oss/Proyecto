import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from sqlalchemy.orm import Session
from datetime import datetime
import os
from functools import reduce

# --- Importaciones de la lógica de negocio ---
from database import get_db
from crud import cliente_crud as ccrud
from crud import ingrediente_crud as icrud
from crud import menu_crud as mcrud
from crud import pedido_crud as pcrud
import graficos as gcrud


# Configuración inicial de CustomTkinter
ctk.set_appearance_mode("System")  
ctk.set_default_color_theme("blue") 


class RestauranteApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Configuración de la Ventana Principal ---
        self.title("Sistema de Gestión de Restaurante - ORM")
        self.geometry("1000x700")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Variables de estado para el Panel de Compra
        self.current_order_items = [] 
        self.menu_map = {} 
        self.cliente_map = {} 

        # --- Barra de Navegación (Tabs) ---
        self.tabview = ctk.CTkTabview(self, width=950, height=600)
        self.tabview.grid(row=0, column=0, padx=20, pady=(20, 0), sticky="nsew")

        self.tabview.add("Clientes")
        self.tabview.add("Ingredientes") 
        self.tabview.add("Menús")
        self.tabview.add("Panel de Compra")
        self.tabview.add("Estadísticas")
        
        self.tabview.grid_columnconfigure(0, weight=1)
        
        # Etiqueta de estado/feedback (Se coloca al final de la ventana principal)
        self.status_label = ctk.CTkLabel(self, text="Listo.", text_color="white")
        self.status_label.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Inicializar pestañas
        self.setup_clientes_tab()
        self.setup_ingredientes_tab()
        self.setup_menus_tab()
        self.setup_compra_tab()
        self.setup_graficos_tab()

        # Cargar datos iniciales al iniciar
        self.cargar_lista_clientes()
        self.cargar_lista_ingredientes()
        self.load_menus()
        self.load_pedidos_init_data()


    # --- Funciones Auxiliares ---

    def get_db_session(self) -> Session | None:
        try:
            db_session = next(get_db())
            return db_session
        except Exception as e:
            self.mostrar_mensaje(f"Error de Conexión a la BD: {e}", tipo="error")
            return None

    def mostrar_mensaje(self, mensaje: str, tipo: str = "info"):
        if tipo == "error":
            self.status_label.configure(text=f"ERROR: {mensaje}", text_color="red")
        elif tipo == "success":
            self.status_label.configure(text=f"ÉXITO: {mensaje}", text_color="green")
        else:
            self.status_label.configure(text=mensaje, text_color="white")
        print(f"[{tipo.upper()}] {mensaje}")
        
    def obtener_recetas_predefinidas(self):
        """Define la lista de menús predefinidos y sus recetas (ingrediente, cantidad)."""
        # Lista de menús y sus recetas
        return [
            ("Completo", 1800, [("Vienesa", 1), ("Pan de Completo", 1), ("Palta", 1), ("Tomate", 1)]),
            ("Hamburguesa", 3500, [("Churrasco de Carne", 1), ("Pan de Hamburguesa", 1), ("Lamina de Queso", 1)]),
            ("Empanada", 1000, [("Carne", 1), ("Cebolla", 1), ("Masa de Empanada", 1)]),
            ("Papas Fritas", 500, [("Papas", 5)]),
            ("Pepsi", 1100, [("Pepsi", 1)]),
            ("Coca Cola", 1200, [("Coca Cola", 1)]),
            ("Panqueques", 2000, [("Panqueques", 2), ("Manjar", 1), ("Azucar Flor", 1)]),
            ("Pollo Frito", 2800, [("Presa de Pollo", 1), ("Harina", 1), ("Aceite", 1)]),
            ("Ensalada Mixta", 1500, [("Lechuga", 1), ("Tomate", 1), ("Zanahoria", 1)]),
            ("Chorrillana", 3500, [("Carne", 2), ("Huevos", 2), ("Papas", 3), ("Cebolla", 1)]),
        ]

    # ====================================================
    # PESTAÑA 1: CLIENTES (Selección Directa - LIMPIO)
    # ====================================================
    
    def setup_clientes_tab(self):
        tab = self.tabview.tab("Clientes")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        gestion_frame = ctk.CTkFrame(tab)
        gestion_frame.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="ew")
        gestion_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(gestion_frame, text="Gestión de Clientes", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=4, padx=10, pady=(10, 5))
        
        # --- Entradas de Creación/Actualización ---
        
        ctk.CTkLabel(gestion_frame, text="Nombre:").grid(row=1, column=0, padx=10, pady=(5,0), sticky="w")
        self.cliente_nombre_entry = ctk.CTkEntry(gestion_frame, placeholder_text="Nombre Cliente")
        self.cliente_nombre_entry.grid(row=2, column=0, padx=10, pady=(0,5), sticky="ew")
        
        ctk.CTkLabel(gestion_frame, text="Email (Usuario):").grid(row=1, column=1, padx=10, pady=(5,0), sticky="w")
        self.email_user_entry = ctk.CTkEntry(gestion_frame, placeholder_text="usuario")
        self.email_user_entry.grid(row=2, column=1, padx=10, pady=(0,5), sticky="ew")
        
        ctk.CTkLabel(gestion_frame, text="Dominio:").grid(row=1, column=2, padx=10, pady=(5,0), sticky="w")
        self.email_dominio_var = ctk.StringVar(gestion_frame, value="@gmail.com") 
        dominios = ["@gmail.com", "@hotmail.com", "@outlook.com", "@yahoo.com", "@dominio.cl", "@empresa.com"]
        email_dominio_combo = ctk.CTkComboBox(gestion_frame, variable=self.email_dominio_var, values=dominios, state="readonly")
        email_dominio_combo.grid(row=2, column=2, padx=10, pady=(0,5), sticky="ew")

        # Botones de Acción
        ctk.CTkButton(gestion_frame, text="Crear Cliente", command=self.crear_cliente).grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(gestion_frame, text="Actualizar Seleccionado", command=self.actualizar_cliente_seleccionado).grid(row=3, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(gestion_frame, text="Eliminar Seleccionado", command=self.eliminar_cliente_seleccionado).grid(row=3, column=2, padx=10, pady=10, sticky="ew")


        # --- Área de Visualización (Treeview para selección) ---
        ctk.CTkLabel(tab, text="Lista de Clientes (Selecciona para actualizar/eliminar)", font=ctk.CTkFont(size=14)).grid(row=1, column=0, padx=20, pady=(10, 5), sticky="w")
        
        list_frame = ctk.CTkFrame(tab) 
        list_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        
        self.tree_clientes = ttk.Treeview(list_frame, columns=("ID", "Nombre", "Email"), show="headings")
        self.tree_clientes.heading("ID", text="ID")
        self.tree_clientes.heading("Nombre", text="Nombre")
        self.tree_clientes.heading("Email", text="Email")
        self.tree_clientes.column("ID", width=50, stretch=tk.NO)
        self.tree_clientes.column("Nombre", width=200, stretch=tk.YES)
        self.tree_clientes.column("Email", width=300, stretch=tk.YES)
        self.tree_clientes.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree_clientes.yview)
        self.tree_clientes.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        self.tree_clientes.bind("<<TreeviewSelect>>", self.cargar_cliente_seleccionado)
    
    def cargar_lista_clientes(self):
        db = self.get_db_session()
        if not db: return

        try:
            clientes = ccrud.listar_clientes(db)
            
            for item in self.tree_clientes.get_children():
                self.tree_clientes.delete(item)
            
            if not clientes:
                self.mostrar_mensaje("No hay clientes registrados.", tipo="info")
                return

            for c in clientes:
                self.tree_clientes.insert("", tk.END, values=(c.id, c.nombre, c.email))
            
            self.mostrar_mensaje(f"Lista de clientes actualizada. Total: {len(clientes)}", tipo="info")
        finally:
            db.close()
            self.load_pedidos_init_data() # Recarga datos de compra

    def cargar_cliente_seleccionado(self, event):
        """Carga los datos del cliente seleccionado a los campos de entrada."""
        selected_item = self.tree_clientes.focus()
        if not selected_item: return

        values = self.tree_clientes.item(selected_item, 'values')
        cliente_id = values[0]
        nombre = values[1]
        email = values[2]
        
        try:
            user, dominio = email.split('@', 1)
            dominio = "@" + dominio
        except ValueError:
            user = email
            dominio = self.email_dominio_var.get()

        self.cliente_nombre_entry.delete(0, "end")
        self.cliente_nombre_entry.insert(0, nombre)
        
        self.email_user_entry.delete(0, "end")
        self.email_user_entry.insert(0, user)
        
        self.email_dominio_var.set(dominio)
        
        self.mostrar_mensaje(f"Cliente ID {cliente_id} cargado para edición.", tipo="info")


    def crear_cliente(self):
        nombre = self.cliente_nombre_entry.get().strip()
        email_user = self.email_user_entry.get().strip()
        email_dominio = self.email_dominio_var.get()
        email = email_user + email_dominio

        if not nombre or not email_user:
            self.mostrar_mensaje("Debe ingresar Nombre y Usuario de Email.", tipo="error")
            return

        db = self.get_db_session()
        if not db: return

        try:
            resultado = ccrud.crear_cliente(db, nombre, email)
            if isinstance(resultado, str):
                self.mostrar_mensaje(resultado, tipo="error")
            else:
                self.mostrar_mensaje(f"Cliente '{resultado.nombre}' (ID: {resultado.id}) creado con éxito.", tipo="success")
                self.cliente_nombre_entry.delete(0, "end")
                self.email_user_entry.delete(0, "end")
                self.cargar_lista_clientes()
        finally:
            db.close()

    def actualizar_cliente_seleccionado(self):
        selected_item = self.tree_clientes.focus()
        if not selected_item:
            self.mostrar_mensaje("Primero selecciona un cliente de la lista para actualizar.", tipo="error")
            return
            
        values = self.tree_clientes.item(selected_item, 'values')
        cliente_id = int(values[0])
        
        nuevo_nombre = self.cliente_nombre_entry.get().strip()
        nuevo_email_user = self.email_user_entry.get().strip()
        nuevo_email_dominio = self.email_dominio_var.get()
        nuevo_email = nuevo_email_user + nuevo_email_dominio

        if not nuevo_nombre or not nuevo_email_user:
            self.mostrar_mensaje("El nombre y el email no pueden estar vacíos.", tipo="error")
            return

        db = self.get_db_session()
        if not db: return

        try:
            cliente_actualizado = ccrud.actualizar_cliente(db, cliente_id, nuevo_nombre, nuevo_email)
            
            if isinstance(cliente_actualizado, str) and "Error" in cliente_actualizado:
                 self.mostrar_mensaje(cliente_actualizado, tipo="error")
            elif cliente_actualizado:
                self.mostrar_mensaje(f"Cliente ID {cliente_id} actualizado con éxito.", tipo="success")
                self.cargar_lista_clientes()
            else:
                self.mostrar_mensaje(f"Fallo al actualizar cliente ID {cliente_id}. El email podría estar en uso.", tipo="error")
        finally:
            db.close()

    def eliminar_cliente_seleccionado(self):
        selected_item = self.tree_clientes.focus()
        if not selected_item:
            self.mostrar_mensaje("Primero selecciona un cliente de la lista para eliminar.", tipo="error")
            return

        values = self.tree_clientes.item(selected_item, 'values')
        cliente_id = int(values[0])
        cliente_nombre = values[1]
        
        if messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de eliminar a '{cliente_nombre}' (ID: {cliente_id})?"):
            db = self.get_db_session()
            if not db: return
            
            try:
                eliminado = ccrud.eliminar_cliente(db, cliente_id)
                if eliminado:
                    self.mostrar_mensaje(f"Cliente ID {cliente_id} eliminado con éxito.", tipo="success")
                    self.cargar_lista_clientes()
                else:
                    self.mostrar_mensaje(f"Fallo al eliminar cliente ID {cliente_id}. Tiene pedidos asociados.", tipo="error")
            finally:
                db.close()


    # ====================================================
    # PESTAÑA 2: INGREDIENTES (Selección Directa y Upsert)
    # ====================================================

    def setup_ingredientes_tab(self):
        tab = self.tabview.tab("Ingredientes")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(6, weight=1) 

        gestion_frame = ctk.CTkFrame(tab)
        gestion_frame.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="ew")
        gestion_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        ctk.CTkLabel(gestion_frame, text="Gestión de Ingredientes y Stock", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=4, padx=10, pady=(5, 5))
        
        ctk.CTkLabel(gestion_frame, text="Nombre:").grid(row=1, column=0, padx=10, pady=(5,0), sticky="w")
        self.ing_nombre_entry = ctk.CTkEntry(gestion_frame, placeholder_text="Nombre Ingrediente")
        self.ing_nombre_entry.grid(row=2, column=0, padx=10, pady=(0,5), sticky="ew")
        
        ctk.CTkLabel(gestion_frame, text="Stock a Añadir/Nuevo:").grid(row=1, column=1, padx=10, pady=(5,0), sticky="w")
        self.ing_stock_entry = ctk.CTkEntry(gestion_frame, placeholder_text="Cantidad (Ej: 1.0 o 0.5)")
        self.ing_stock_entry.grid(row=2, column=1, padx=10, pady=(0,5), sticky="ew")
        
        # Botones de Acción (LIMPIO)
        ctk.CTkButton(gestion_frame, text="Crear o Sumar Stock", command=self.crear_ingrediente_manual).grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(gestion_frame, text="Eliminar Seleccionado", command=self.eliminar_ingrediente_seleccionado).grid(row=3, column=2, padx=10, pady=10, sticky="ew")

        # Botón de Cargar CSV 
        ctk.CTkButton(tab, text="Cargar Stock desde Archivo CSV", command=self.cargar_stock_csv_gui).grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        # --- Área de Visualización (Treeview para selección) ---
        ctk.CTkLabel(tab, text="Stock de Ingredientes (Selecciona para fijar/eliminar)", font=ctk.CTkFont(size=14)).grid(row=5, column=0, padx=20, pady=(10, 5), sticky="w")
        
        list_frame = ctk.CTkFrame(tab) 
        list_frame.grid(row=6, column=0, padx=20, pady=(0, 20), sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)

        self.tree_ingredientes = ttk.Treeview(list_frame, columns=("ID", "Nombre", "Stock"), show="headings")
        self.tree_ingredientes.heading("ID", text="ID")
        self.tree_ingredientes.heading("Nombre", text="Nombre")
        self.tree_ingredientes.heading("Stock", text="Stock (Unidades)")
        self.tree_ingredientes.column("ID", width=50, stretch=tk.NO)
        self.tree_ingredientes.column("Nombre", width=250, stretch=tk.YES)
        self.tree_ingredientes.column("Stock", width=150, anchor=tk.E, stretch=tk.NO)
        self.tree_ingredientes.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree_ingredientes.yview)
        self.tree_ingredientes.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        self.tree_ingredientes.bind("<<TreeviewSelect>>", self.cargar_ingrediente_seleccionado)




    def cargar_ingrediente_seleccionado(self, event):
        selected_item = self.tree_ingredientes.focus()
        if not selected_item: return

        values = self.tree_ingredientes.item(selected_item, 'values')
        ing_id = values[0]
        nombre = values[1]
        
        self.ing_nombre_entry.delete(0, "end")
        self.ing_nombre_entry.insert(0, nombre)
        
        self.ing_stock_entry.delete(0, "end")

        self.mostrar_mensaje(f"Ingrediente ID {ing_id} ('{nombre}') cargado para edición.", tipo="info")


    def crear_ingrediente_manual(self):
        nombre = self.ing_nombre_entry.get().strip()
        stock_str = self.ing_stock_entry.get().strip()

        if not nombre or not stock_str:
            self.mostrar_mensaje("Debe ingresar Nombre y Cantidad (Stock a Añadir).", tipo="error")
            return
        
        try:
            stock_a_agregar = float(stock_str)
            if stock_a_agregar < 0:
                 self.mostrar_mensaje("La cantidad a añadir debe ser positiva o cero.", tipo="error")
                 return
        except ValueError:
            self.mostrar_mensaje("La Cantidad debe ser un número válido.", tipo="error")
            return

        db = self.get_db_session()
        if not db: return

        try:
            resultado = icrud.crear_ingrediente(db, nombre, stock_a_agregar) 

            if isinstance(resultado, str):
                self.mostrar_mensaje(resultado, tipo="error") 
            else:
                accion = "creado" if resultado.stock == stock_a_agregar else "stock sumado a"
                self.mostrar_mensaje(f"Ingrediente '{resultado.nombre}' {accion} con éxito. Stock: {resultado.stock:,.2f}.", tipo="success")
                self.ing_nombre_entry.delete(0, "end")
                self.ing_stock_entry.delete(0, "end")
                self.cargar_lista_ingredientes()
        finally:
            db.close()

    
    def actualizar_ingrediente_stock_seleccionado(self):
        """Fija el stock del ingrediente seleccionado al valor introducido en el campo de stock."""
        selected_item = self.tree_ingredientes.focus()
        if not selected_item:
            self.mostrar_mensaje("Primero selecciona un ingrediente de la lista para fijar stock.", tipo="error")
            return
            
        values = self.tree_ingredientes.item(selected_item, 'values')
        ing_id = int(values[0])
        ing_nombre = values[1]
        
        nuevo_stock_str = self.ing_stock_entry.get().strip()

        if not nuevo_stock_str:
            self.mostrar_mensaje("Debe ingresar el Nuevo Stock (Cantidad Total).", tipo="error")
            return

        try:
            nuevo_stock = float(nuevo_stock_str)
            if nuevo_stock < 0:
                raise ValueError("El stock debe ser positivo.")
        except ValueError:
            self.mostrar_mensaje("El stock debe ser un número válido y positivo.", tipo="error")
            return
        
        db = self.get_db_session()
        if not db: return
        
        try:
            ing_actualizado = icrud.actualizar_stock_ingrediente(db, ing_id, nuevo_stock)
            
            if ing_actualizado:
                self.mostrar_mensaje(f"Stock de '{ing_actualizado.nombre}' (ID {ing_id}) fijado a {ing_actualizado.stock:,.2f}.", tipo="success")
                self.ing_stock_entry.delete(0, "end")
                self.cargar_lista_ingredientes()
            else:
                self.mostrar_mensaje(f"Fallo al fijar stock ID {ing_id}.", tipo="error")
        finally:
            db.close()

    def eliminar_ingrediente_seleccionado(self):
        """Elimina el ingrediente seleccionado en el Treeview."""
        selected_item = self.tree_ingredientes.focus()
        if not selected_item:
            self.mostrar_mensaje("Primero selecciona un ingrediente de la lista para eliminar.", tipo="error")
            return

        values = self.tree_ingredientes.item(selected_item, 'values')
        ing_id = int(values[0])
        ing_nombre = values[1]
        
        if messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de eliminar el ingrediente '{ing_nombre}' (ID: {ing_id})?\nAdvertencia: Esto puede afectar a los menús que lo utilizan."):
            db = self.get_db_session()
            if not db: return
            
            try:
                eliminado = icrud.eliminar_ingrediente(db, ing_id)
                if eliminado:
                    self.mostrar_mensaje(f"Ingrediente ID {ing_id} eliminado con éxito.", tipo="success")
                    self.cargar_lista_ingredientes()
                else:
                    self.mostrar_mensaje(f"Fallo al eliminar ID {ing_id}.", tipo="error") 
            finally:
                db.close()
   # app.py (Dentro de la clase RestauranteApp)

    def cargar_stock_csv_gui(self):
        """Abre el diálogo para seleccionar CSV y llama a la función CRUD."""
        filepath = filedialog.askopenfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        
        if not filepath:
            self.mostrar_mensaje("Selección de archivo CSV cancelada.", tipo="info")
            return

        db = self.get_db_session()
        if not db: return

        try:
            # 1. ESTO GUARDA EN LA BD
            success = icrud.cargar_ingredientes_csv(db, filepath)
            
            if success:
                 self.mostrar_mensaje("Carga CSV de stock completada con éxito.", tipo="success")
            else:
                 self.mostrar_mensaje("Fallo la carga CSV. Revise la Consola.", tipo="error")
                 
        except Exception as e:
            self.mostrar_mensaje(f"Error inesperado en la carga CSV: {e}", tipo="error")
        finally:
            db.close()
            
            # 2. ESTA LÍNEA MUESTRA LOS DATOS EN PANTALLA
            self.cargar_lista_ingredientes() 


    def cargar_lista_ingredientes(self):
        """Refresca el Treeview con los datos actuales de la BD."""
        db = self.get_db_session()
        if not db: return

        try:
            ingredientes = icrud.listar_ingredientes(db)
            
            # Limpia la tabla antes de recargar
            for item in self.tree_ingredientes.get_children():
                self.tree_ingredientes.delete(item)
            
            if not ingredientes:
                self.mostrar_mensaje("No hay ingredientes registrados. Carga desde CSV o cree uno.", tipo="info")
                return

            # MUESTRA LOS DATOS EN LA TABLA
            for i in ingredientes:
                self.tree_ingredientes.insert("", tk.END, values=(i.id, i.nombre, f"{i.stock:,.2f}"))
            
            self.mostrar_mensaje(f"Inventario actualizado. Total de ítems: {len(ingredientes)}", tipo="info")
        finally:
            db.close()
            
    # ====================================================
    # PESTAÑA 3: MENÚS (Integración de Carga de Recetas)
    # ====================================================

    # app.py (Reemplazar estas funciones dentro de la clase RestauranteApp)

    # ====================================================
    # PESTAÑA 3: MENÚS (REFACTORIZADA CON TREEVIEW Y LÓGICA DE CARGA)
    # ====================================================

    def setup_menus_tab(self):
        tab = self.tabview.tab("Menús")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)
        
        gestion_frame = ctk.CTkFrame(tab)
        gestion_frame.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="ew")
        gestion_frame.grid_columnconfigure((0, 1, 2, 3), weight=1) 
        
        ctk.CTkLabel(gestion_frame, text="Gestión de Menús y Recetas", font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, columnspan=4, padx=10, pady=(5, 5))
        
        # BOTÓN CLAVE: Carga los menús y sus recetas (si los ingredientes del CSV existen)
        ctk.CTkButton(gestion_frame, text="Menus prefijos", command=self.crear_recetas_masivas).grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        
        ctk.CTkButton(gestion_frame, text="Eliminar Menú Seleccionado", command=self.eliminar_menu_seleccionado).grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(gestion_frame, text="Crear Menú ", command=lambda: self.mostrar_mensaje("Funcionalidad de creación individual omitida.", tipo="info")).grid(row=1, column=2, padx=10, pady=10, sticky="ew")


        ctk.CTkLabel(tab, text="Menús Registrados (Selecciona para eliminar)", font=ctk.CTkFont(size=14)).grid(row=1, column=0, padx=20, pady=(10, 5), sticky="w")
        
        # --- Área de Visualización (Treeview para selección) ---
        list_frame = ctk.CTkFrame(tab) 
        list_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)

        self.tree_menus = ttk.Treeview(list_frame, columns=("ID", "Nombre", "Precio", "Descripción"), show="headings")
        self.tree_menus.heading("ID", text="ID")
        self.tree_menus.heading("Nombre", text="Nombre")
        self.tree_menus.heading("Precio", text="Precio")
        self.tree_menus.heading("Descripción", text="Descripción")
        
        self.tree_menus.column("ID", width=50, stretch=tk.NO)
        self.tree_menus.column("Nombre", width=200, stretch=tk.YES)
        self.tree_menus.column("Precio", width=100, anchor=tk.E, stretch=tk.NO)
        self.tree_menus.column("Descripción", width=300, stretch=tk.YES)
        
        self.tree_menus.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree_menus.yview)
        self.tree_menus.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

    def load_menus(self):
        """Carga los menús existentes en el Treeview."""
        db = self.get_db_session()
        if not db: return

        try:
            menus = mcrud.leer_todos_los_menus(db)
            
            # Limpiar Treeview
            for item in self.tree_menus.get_children():
                self.tree_menus.delete(item)
            
            if not menus:
                self.mostrar_mensaje("No hay menús registrados. Carga el CSV de ingredientes y luego 'Crear Recetas Prefijadas'.", tipo="info")
                return

            for m in menus:
                self.tree_menus.insert("", tk.END, values=(m.id, m.nombre, f"${m.precio:,.0f}", m.descripcion))
            
            self.mostrar_mensaje(f"Lista de menús actualizada. Total: {len(menus)}", tipo="info")
        finally:
            db.close()
            self.load_pedidos_init_data() # Recarga el combobox de Panel de Compra

    def crear_recetas_masivas(self):
        """
        Intenta crear todos los menús y sus recetas predefinidas.
        SOLO funciona si los ingredientes (del CSV) ya están en la BD.
        """
        db = self.get_db_session()
        if not db: return

        # 1. Obtener la lista de recetas predefinidas
        recetas_predefinidas = self.obtener_recetas_predefinidas()
        exitos = 0
        fallos = 0
        
        try:
            # 2. Obtener TODOS los ingredientes que existen actualmente en la BD
            ingredientes_existentes = {ing.nombre: ing.id for ing in icrud.listar_ingredientes(db)}
            
            if not ingredientes_existentes:
                self.mostrar_mensaje("ERROR: El inventario de ingredientes está vacío. ¡Cargue el CSV primero!", tipo="error")
                db.close()
                return

            for nombre_menu, precio, receta_data in recetas_predefinidas:
                
                # 3. Verificar si el menú ya existe (para no duplicarlo)
                if mcrud.leer_menu_por_nombre(db, nombre_menu):
                    continue

                receta_orm = []
                ingredientes_faltantes = False
                
                # 4. Convertir nombres de ingredientes en IDs
                for ing_nombre, cantidad in receta_data:
                    ing_nombre_title = ing_nombre.strip().title()

                    if ing_nombre_title not in ingredientes_existentes:
                        ingredientes_faltantes = True
                        break # Falla la receta si falta un ingrediente
                    
                    ing_id = ingredientes_existentes[ing_nombre_title]
                    receta_orm.append({"ingrediente_id": ing_id, "cantidad": cantidad})

                if ingredientes_faltantes:
                    print(f"FALLO RECETA: {nombre_menu} - Faltan ingredientes en el inventario.")
                    fallos += 1
                    continue
                
                # 5. Si todo está bien, crear el menú y la receta
                if receta_orm:
                    # Llama a la función de CRUD que crea el Menú y la Receta juntos
                    resultado = mcrud.crear_menu(db, nombre_menu, f"Receta de {nombre_menu}", precio, receta_orm)
                    
                    if isinstance(resultado, str) and "Error" in resultado:
                        print(f"Error al crear menú {nombre_menu}: {resultado}")
                        fallos += 1
                    else:
                        exitos += 1

        except Exception as e:
            self.mostrar_mensaje(f"Error crítico en la carga masiva de recetas: {e}", tipo="error")
            fallos += 1
        finally:
            db.close()
            self.load_menus() # Recargar la lista de menús
            
        self.mostrar_mensaje(f"Carga de recetas: {exitos} creadas. {fallos} fallaron (ingrediente no cargado).", tipo="info")

    def eliminar_menu_seleccionado(self):
        """Elimina el menú seleccionado en el Treeview."""
        selected_item = self.tree_menus.focus()
        if not selected_item:
            self.mostrar_mensaje("Primero selecciona un menú de la lista para eliminar.", tipo="error")
            return

        values = self.tree_menus.item(selected_item, 'values')
        menu_id = int(values[0])
        menu_nombre = values[1]
        
        if messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de eliminar el menú '{menu_nombre}' (ID: {menu_id})?"):
            db = self.get_db_session()
            if not db: return
            
            try:
                eliminado = mcrud.eliminar_menu(db, menu_id)
                if eliminado:
                    self.mostrar_mensaje(f"Menú ID {menu_id} eliminado con éxito.", tipo="success")
                    self.load_menus()
                else:
                    self.mostrar_mensaje(f"Fallo al eliminar menú ID {menu_id}. ¿Está asociado a un pedido?", tipo="error")
            finally:
                db.close()

    # ====================================================
    # PESTAÑA 4: PANEL DE COMPRA (PEDIDOS) - LÓGICA COMPLETA
    # ====================================================

    def setup_compra_tab(self):
        tab = self.tabview.tab("Panel de Compra")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1) 
        
        control_frame = ctk.CTkFrame(tab)
        control_frame.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="ew")
        control_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(control_frame, text="Cliente:").grid(row=0, column=0, padx=10, pady=(5,0), sticky="w")
        self.cliente_var_compra = ctk.StringVar(control_frame)
        self.cliente_combo_compra = ctk.CTkComboBox(control_frame, variable=self.cliente_var_compra, values=[], state="readonly")
        self.cliente_combo_compra.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(control_frame, text="Menú:").grid(row=0, column=1, padx=10, pady=(5,0), sticky="w")
        self.menu_var_compra = ctk.StringVar(control_frame)
        self.menu_combo_compra = ctk.CTkComboBox(control_frame, variable=self.menu_var_compra, values=[], state="readonly")
        self.menu_combo_compra.grid(row=1, column=1, padx=10, pady=(0, 10), sticky="ew")
        
        ctk.CTkLabel(control_frame, text="Cantidad:").grid(row=0, column=2, padx=10, pady=(5,0), sticky="w")
        self.cantidad_entry_compra = ctk.CTkEntry(control_frame, width=50)
        self.cantidad_entry_compra.insert(0, "1")
        self.cantidad_entry_compra.grid(row=1, column=2, padx=10, pady=(0, 10), sticky="w")

        ctk.CTkButton(control_frame, text="Añadir al Pedido", command=self.add_menu_to_order).grid(row=1, column=3, padx=10, pady=10, sticky="ew")
        
        self.tree_order = ttk.Treeview(tab, columns=("ID", "Nombre", "Precio", "Cantidad", "Subtotal"), show="headings")
        self.tree_order.heading("ID", text="ID", anchor=tk.W)
        self.tree_order.heading("Nombre", text="Menú", anchor=tk.W)
        self.tree_order.heading("Precio", text="P. Unit.", anchor=tk.E)
        self.tree_order.heading("Cantidad", text="Cant.", anchor=tk.E)
        self.tree_order.heading("Subtotal", text="Subtotal", anchor=tk.E)
        
        self.tree_order.column("ID", width=40, stretch=tk.NO)
        self.tree_order.column("Nombre", width=250, stretch=tk.YES)
        self.tree_order.column("Precio", width=100, anchor=tk.E, stretch=tk.NO)
        self.tree_order.column("Cantidad", width=60, anchor=tk.E, stretch=tk.NO)
        self.tree_order.column("Subtotal", width=120, anchor=tk.E, stretch=tk.NO)
        
        self.tree_order.grid(row=1, column=0, padx=20, pady=(10, 5), sticky="nsew") 

        footer_frame = ctk.CTkFrame(tab)
        footer_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        footer_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.total_var = ctk.StringVar(footer_frame, value="Total: $0")
        ctk.CTkLabel(footer_frame, textvariable=self.total_var, font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        ctk.CTkButton(footer_frame, text="Eliminar Item", command=self.remove_menu_from_order).grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(footer_frame, text="Limpiar Pedido", command=self.clear_order).grid(row=0, column=2, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(footer_frame, text="Finalizar Compra", command=self.finalize_order, fg_color="green").grid(row=0, column=3, padx=10, pady=10, sticky="ew")

    def load_pedidos_init_data(self):
        """Carga los datos de Clientes y Menús para los comboboxes."""
        db = self.get_db_session()
        if not db: return

        try:
            clientes = ccrud.listar_clientes(db)
            self.cliente_map = {f"{c.nombre} (ID: {c.id})": c.id for c in clientes}
            cliente_keys = list(self.cliente_map.keys())
            self.cliente_combo_compra.configure(values=cliente_keys)
            if cliente_keys:
                self.cliente_var_compra.set(cliente_keys[0])

            menus = mcrud.leer_todos_los_menus(db)
            self.menu_map = {f"{m.nombre} (${m.precio:,.0f}) (ID: {m.id})": m for m in menus}
            menu_keys = list(self.menu_map.keys())
            self.menu_combo_compra.configure(values=menu_keys)
            if menu_keys:
                self.menu_var_compra.set(menu_keys[0])

        finally:
            db.close()
        self.update_order_display() 

    def update_order_display(self):
        """Actualiza el Treeview (lista de pedido) y el total."""
        
        for item in self.tree_order.get_children():
            self.tree_order.delete(item)
            
        total = 0
        for item in self.current_order_items:
            subtotal = item['precio'] * item['cantidad']
            total += subtotal
            
            self.tree_order.insert("", tk.END, values=(
                item['id'], 
                item['nombre'], 
                f"${item['precio']:,.0f}", 
                item['cantidad'], 
                f"${subtotal:,.0f}"
            ))
            
        self.total_var.set(f"Total: ${total:,.0f}")

    def add_menu_to_order(self):
        """Añade el menú seleccionado con la cantidad especificada al pedido."""
        selected_menu_str = self.menu_var_compra.get()
        cantidad_str = self.cantidad_entry_compra.get().strip()

        if not selected_menu_str:
            self.mostrar_mensaje("Selecciona un menú.", tipo="error")
            return
        
        try:
            cantidad = int(cantidad_str)
            if cantidad <= 0:
                raise ValueError("Cantidad debe ser positiva.")
        except ValueError:
            self.mostrar_mensaje("Ingresa una cantidad válida (número entero positivo).", tipo="error")
            return

        selected_menu_obj = self.menu_map.get(selected_menu_str)
        if not selected_menu_obj:
            self.mostrar_mensaje("Error: Menú no encontrado en el mapa.", tipo="error")
            return

        menu_id = selected_menu_obj.id
        menu_nombre = selected_menu_obj.nombre
        menu_precio = selected_menu_obj.precio

        found = False
        for item in self.current_order_items:
            if item['id'] == menu_id:
                item['cantidad'] += cantidad
                found = True
                break
        
        if not found:
            self.current_order_items.append({
                'id': menu_id,
                'nombre': menu_nombre,
                'precio': menu_precio,
                'cantidad': cantidad
            })

        self.update_order_display()
        self.mostrar_mensaje(f"Se añadieron {cantidad} x '{menu_nombre}' al pedido.", tipo="success")
        self.cantidad_entry_compra.delete(0, "end")
        self.cantidad_entry_compra.insert(0, "1")

    def remove_menu_from_order(self):
        """Elimina el menú seleccionado del Treeview y de la lista interna."""
        
        selected_item = self.tree_order.focus()
        if not selected_item:
            self.mostrar_mensaje("Selecciona un ítem para eliminar en la lista de abajo.", tipo="info")
            return

        values = self.tree_order.item(selected_item, 'values')
        menu_id_to_remove = int(values[0])

        self.current_order_items = [item for item in self.current_order_items if item['id'] != menu_id_to_remove]
        
        self.update_order_display()
        self.mostrar_mensaje("Ítem eliminado del pedido.", tipo="info")

    def clear_order(self):
        """Limpia el pedido actual."""
        self.current_order_items = []
        self.update_order_display()
        self.mostrar_mensaje("Pedido limpiado.", tipo="info")

    def finalize_order(self):
        """Procesa la compra y descuenta el stock (Llamada CRÍTICA al CRUD)."""
        if not self.current_order_items:
            self.mostrar_mensaje("El pedido está vacío.", tipo="error")
            return

        selected_cliente_str = self.cliente_var_compra.get()
        if not selected_cliente_str:
            self.mostrar_mensaje("Selecciona un cliente.", tipo="error")
            return

        cliente_id = self.cliente_map.get(selected_cliente_str)
        if not cliente_id:
            self.mostrar_mensaje("Error: No se pudo obtener el ID del cliente.", tipo="error")
            return

        menus_pedido_for_crud = [
            {"id": item['id'], "cantidad": item['cantidad']}
            for item in self.current_order_items
        ]

        db = self.get_db_session()
        if not db: return

        try:
            nuevo_pedido = pcrud.crear_pedido(db, cliente_id, menus_pedido_for_crud)
            
            if nuevo_pedido:
                self.mostrar_mensaje(f"Pedido #{nuevo_pedido.id} finalizado con éxito. Total: ${nuevo_pedido.total:,.0f}.", tipo="success")
                self.clear_order() 
                self.cargar_lista_ingredientes() 
            else:
                self.mostrar_mensaje("Fallo al finalizar el pedido. (Stock insuficiente o error de BD)", tipo="error")
        except Exception as e:
            self.mostrar_mensaje(f"Error inesperado al procesar el pedido: {e}", tipo="error")
        finally:
            db.close()

    # ====================================================
    # PESTAÑA 5: GRÁFICOS
    # ====================================================

    def setup_graficos_tab(self):
        tab = self.tabview.tab("Estadísticas")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(tab, text="📊 Gráficos Estadísticos", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, padx=20, pady=15)

        control_frame = ctk.CTkFrame(tab)
        control_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        control_frame.grid_columnconfigure(1, weight=1) # Damos peso a la columna del combobox

        # Elemento 1: Etiqueta
        ctk.CTkLabel(control_frame, text="Seleccionar Tipo de Reporte:").grid(row=0, column=0, padx=(10, 5), pady=5, sticky="w")
        self.grafico_var = ctk.StringVar(control_frame)
        opciones_graficos = ["Ventas Diarias", "Ventas Mensuales", "Ventas Anuales", "Menús Más Comprados", "Uso Total de Ingredientes"]
        self.grafico_var.set(opciones_graficos[0]) 
        
        # Elemento 2: ComboBox
        grafico_menu = ctk.CTkComboBox(control_frame, variable=self.grafico_var, values=opciones_graficos, state="readonly", width=250)
        grafico_menu.grid(row=0, column=1, padx=5, pady=5, sticky="ew") # Columna 1
        
        # Elemento 3: Botón
        ctk.CTkButton(control_frame, 
                      text="Generar Reporte", 
                      command=self.generate_report).grid(row=0, column=2, padx=(10, 10), pady=5, sticky="e") # Columna 2
        
        self.report_text = ctk.CTkTextbox(tab, height=200)
        self.report_text.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")

    def generate_report(self):
        """Genera el reporte estadístico basado en la selección."""
        self.mostrar_mensaje("La generación de reportes requiere la implementación final del módulo graficos.py.", tipo="info")
        # Lógica de generación de reportes (Llama a graficos.py)
        pass