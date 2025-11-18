import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from sqlalchemy.orm import Session
from datetime import datetime
import os
from functools import reduce
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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
        self.tabview.add("Pedidos")
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
        self.setup_pedidos_tab()
        self.setup_graficos_tab()

        # Cargar datos iniciales al iniciar
        self.cargar_lista_clientes()
        self.cargar_lista_ingredientes()
        self.load_menus()
        self.load_pedidos_init_data()

    # ===================================================================
    # LÓGICA ESPECÍFICA PARA MODIFICAR MENÚ (CON TABLA Y ELIMINAR)
    # ===================================================================

    def abrir_ventana_modificar_menu(self):
        """Abre ventana para modificar menú usando una Tabla para los ingredientes."""
        selected_item = self.tree_menus.focus()
        if not selected_item:
            self.mostrar_mensaje("Selecciona un menú para modificar.", tipo="error")
            return

        values = self.tree_menus.item(selected_item, 'values')
        menu_id = int(values[0])

        db = self.get_db_session()
        if not db: return
        
        try:
            menu_actual = mcrud.leer_menu_por_id(db, menu_id)
            if not menu_actual:
                return

            # 1. Configurar Ventana
            self.ventana_mod = ctk.CTkToplevel(self)
            self.ventana_mod.title(f"Modificar: {menu_actual.nombre}")
            self.ventana_mod.geometry("600x700")
            self.ventana_mod.grab_set()

            self.menu_id_en_edicion = menu_id
            self.temp_receta_mod = []      # Lista temporal para la receta
            self.mapa_ingredientes_mod = {} # Mapa para el combobox

            # 2. Campos de Texto (Nombre, Desc, Precio)
            ctk.CTkLabel(self.ventana_mod, text="Nombre:").pack(pady=(10, 0))
            self.entry_mod_nombre = ctk.CTkEntry(self.ventana_mod)
            self.entry_mod_nombre.insert(0, menu_actual.nombre)
            self.entry_mod_nombre.pack(pady=5)

            ctk.CTkLabel(self.ventana_mod, text="Descripción:").pack(pady=(5, 0))
            self.entry_mod_desc = ctk.CTkEntry(self.ventana_mod)
            self.entry_mod_desc.insert(0, menu_actual.descripcion or "")
            self.entry_mod_desc.pack(pady=5)

            ctk.CTkLabel(self.ventana_mod, text="Precio:").pack(pady=(5, 0))
            self.entry_mod_precio = ctk.CTkEntry(self.ventana_mod)
            self.entry_mod_precio.insert(0, str(menu_actual.precio))
            self.entry_mod_precio.pack(pady=5)

            # 3. Sección de Agregar Ingrediente
            ctk.CTkLabel(self.ventana_mod, text="--- Editar Receta ---", font=("Arial", 12, "bold")).pack(pady=10)
            
            frame_add = ctk.CTkFrame(self.ventana_mod)
            frame_add.pack(pady=5, padx=10, fill="x")

            self.combo_ing_mod = ctk.CTkComboBox(frame_add, state="readonly")
            self.combo_ing_mod.pack(side="left", padx=5, expand=True, fill="x")
            
            # Cargar ingredientes al combo (Manteniendo la sesión abierta)
            ingredientes = icrud.listar_ingredientes(db)
            self.mapa_ingredientes_mod = {i.nombre: i.id for i in ingredientes}
            self.combo_ing_mod.configure(values=list(self.mapa_ingredientes_mod.keys()))
            if ingredientes: self.combo_ing_mod.set(ingredientes[0].nombre)

            self.entry_cant_mod = ctk.CTkEntry(frame_add, placeholder_text="Cant.", width=60)
            self.entry_cant_mod.pack(side="left", padx=5)

            ctk.CTkButton(frame_add, text="Añadir", width=60, command=self.agregar_ingrediente_mod).pack(side="left", padx=5)

            # 4. TABLA DE RECETA
            frame_tabla = ctk.CTkFrame(self.ventana_mod)
            frame_tabla.pack(pady=10, padx=10, fill="both", expand=True)

            self.tree_receta_mod = ttk.Treeview(frame_tabla, columns=("ID", "Nombre", "Cantidad"), show="headings", height=8)
            self.tree_receta_mod.heading("ID", text="ID")
            self.tree_receta_mod.heading("Nombre", text="Ingrediente")
            self.tree_receta_mod.heading("Cantidad", text="Cantidad")
            self.tree_receta_mod.column("ID", width=40)
            self.tree_receta_mod.column("Nombre", width=250)
            self.tree_receta_mod.column("Cantidad", width=80)
            self.tree_receta_mod.pack(side="left", fill="both", expand=True)

            # 5. Botón ELIMINAR
            ctk.CTkButton(self.ventana_mod, text="Eliminar Ingrediente Seleccionado", fg_color="red", command=self.eliminar_ingrediente_mod).pack(pady=5)

            # 6. Cargar la receta actual en la lista temporal (AHORA SÍ FUNCIONARÁ)
            for item in menu_actual.items_receta:
                self.temp_receta_mod.append({
                    "ingrediente_id": item.ingrediente.id,
                    "nombre": item.ingrediente.nombre,
                    "cantidad": item.cantidad
                })
            
            self.refrescar_tabla_mod() # Mostrar en la tabla

            # 7. Botón Guardar Final
            ctk.CTkButton(self.ventana_mod, text="Guardar Cambios", fg_color="orange", height=40, font=("Arial", 14, "bold"), command=self.guardar_cambios_mod).pack(pady=20, padx=20, fill="x")

        finally:
            # Cerramos la conexión AL FINAL de todo
            db.close()

    def refrescar_tabla_mod(self):
        """Actualiza la tabla visual basada en la lista temporal."""
        for item in self.tree_receta_mod.get_children():
            self.tree_receta_mod.delete(item)
        
        for item in self.temp_receta_mod:
            self.tree_receta_mod.insert("", "end", values=(item['ingrediente_id'], item['nombre'], item['cantidad']))

    def agregar_ingrediente_mod(self):
        """Agrega o suma cantidad a la lista temporal."""
        nombre = self.combo_ing_mod.get()
        cant_str = self.entry_cant_mod.get()
        
        if not nombre or not cant_str: return
        try:
            cant = float(cant_str)
            if cant <= 0: raise ValueError
        except:
            tk.messagebox.showerror("Error", "Cantidad inválida")
            return

        ing_id = self.mapa_ingredientes_mod.get(nombre)

        # Verificar si ya existe para sumar
        for item in self.temp_receta_mod:
            if item['ingrediente_id'] == ing_id:
                item['cantidad'] += cant
                self.refrescar_tabla_mod()
                return

        # Si no existe, agregar
        self.temp_receta_mod.append({"ingrediente_id": ing_id, "nombre": nombre, "cantidad": cant})
        self.refrescar_tabla_mod()

    def eliminar_ingrediente_mod(self):
        """Elimina el ingrediente seleccionado de la tabla."""
        selected = self.tree_receta_mod.focus()
        if not selected:
            tk.messagebox.showerror("Error", "Selecciona un ingrediente de la tabla para eliminarlo.")
            return
        
        values = self.tree_receta_mod.item(selected, 'values')
        id_borrar = int(values[0])
        
        # Reconstruir la lista excluyendo el ID borrado
        self.temp_receta_mod = [i for i in self.temp_receta_mod if i['ingrediente_id'] != id_borrar]
        self.refrescar_tabla_mod()

    def guardar_cambios_mod(self):
        """Guarda el menú actualizado en la BD."""
        nombre = self.entry_mod_nombre.get().strip()
        desc = self.entry_mod_desc.get().strip()
        try:
            precio = float(self.entry_mod_precio.get().strip())
        except:
            tk.messagebox.showerror("Error", "Precio inválido")
            return

        if not nombre or not self.temp_receta_mod:
            tk.messagebox.showerror("Error", "Falta nombre o ingredientes.")
            return

        db = self.get_db_session()
        if not db: return

        try:
            # Llamamos a la función de CRUD (asegurate de tener menu_crud actualizado)
            res = mcrud.actualizar_menu_completo(
                db, self.menu_id_en_edicion, nombre, desc, precio, self.temp_receta_mod
            )
            
            if isinstance(res, str) and "Error" in res:
                tk.messagebox.showerror("Error BD", res)
            elif res:
                tk.messagebox.showinfo("Éxito", "Menú modificado correctamente.")
                self.ventana_mod.destroy()
                self.load_menus()
            else:
                tk.messagebox.showerror("Error", "No se pudo actualizar.")
        except Exception as e:
            tk.messagebox.showerror("Error", str(e))
        finally:
            db.close()

    def limpiar_receta_temporal(self):
        """Borra la receta actual en la ventana de edición."""
        self.temp_receta = []
        self.lista_ingredientes_label.configure(state="normal")
        self.lista_ingredientes_label.delete("0.0", "end")
        self.lista_ingredientes_label.insert("0.0", "Receta vaciada.\n")
        self.lista_ingredientes_label.configure(state="disabled")

    def guardar_edicion_menu_bd(self):
        """Llama al CRUD para actualizar el menú."""
        nombre = self.entry_nuevo_menu_nombre.get().strip()
        desc = self.entry_nuevo_menu_desc.get().strip()
        precio_str = self.entry_nuevo_menu_precio.get().strip()

        if not nombre or not precio_str:
            tk.messagebox.showerror("Error", "Falta nombre o precio")
            return
        
        if not self.temp_receta:
            tk.messagebox.showerror("Error", "El menú debe tener al menos un ingrediente.")
            return

        try:
            precio = float(precio_str)
        except ValueError:
            tk.messagebox.showerror("Error", "Precio inválido")
            return

        db = self.get_db_session()
        if not db: return

        try:
            # Llamamos a la función NUEVA de menu_crud
            resultado = mcrud.actualizar_menu_completo(
                db, 
                self.menu_id_en_edicion, 
                nombre, 
                desc, 
                precio, 
                self.temp_receta
            )
            
            if isinstance(resultado, str) and "Error" in resultado:
                tk.messagebox.showerror("Error BD", resultado)
            elif resultado:
                tk.messagebox.showinfo("Éxito", "Menú actualizado correctamente.")
                self.ventana_menu.destroy()
                self.load_menus()
            else:
                tk.messagebox.showerror("Error", "No se pudo actualizar.")
        except Exception as e:
             tk.messagebox.showerror("Error Crítico", str(e))
        finally:
            db.close()


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
        
        # Botón Carga Masiva
        ctk.CTkButton(gestion_frame, text="Cargar Menús Prefijos", command=self.crear_recetas_masivas).grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        
        # Botón Eliminar
        ctk.CTkButton(gestion_frame, text="Eliminar Menú Seleccionado", command=self.eliminar_menu_seleccionado).grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        
        # boton ventana emergente de crear menu
        ctk.CTkButton(gestion_frame, text="Crear Nuevo Menú", command=self.abrir_ventana_crear_menu).grid(row=1, column=2, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(tab, text="Menús Registrados (Selecciona para eliminar)", font=ctk.CTkFont(size=14)).grid(row=1, column=0, padx=20, pady=(10, 5), sticky="w")
        # boton modificar menu
        ctk.CTkButton(gestion_frame, text="Modificar Menú Seleccionado", command=self.abrir_ventana_modificar_menu).grid(row=1, column=3, padx=10, pady=10, sticky="ew")
        
        # --- Área de Visualización ---
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
 

    # --- LÓGICA PARA CREAR MENÚ MANUALMENTE (VENTANA EMERGENTE) ---

    def abrir_ventana_crear_menu(self):
        """Abre una ventana emergente (Toplevel) para crear un menú complejo."""
        
        # Crear ventana
        self.ventana_menu = ctk.CTkToplevel(self)
        self.ventana_menu.title("Crear Nuevo Menú")
        self.ventana_menu.geometry("500x600")
        self.ventana_menu.grab_set() # Hace que la ventana sea modal (bloquea la de atrás)

        # Variables temporales para esta ventana
        self.temp_receta = [] 
        self.mapa_ingredientes_temp = {}

        # --- Campos Básicos ---
        ctk.CTkLabel(self.ventana_menu, text="Nombre del Menú:").pack(pady=(10, 0))
        self.entry_nuevo_menu_nombre = ctk.CTkEntry(self.ventana_menu)
        self.entry_nuevo_menu_nombre.pack(pady=5)

        ctk.CTkLabel(self.ventana_menu, text="Descripción:").pack(pady=(5, 0))
        self.entry_nuevo_menu_desc = ctk.CTkEntry(self.ventana_menu)
        self.entry_nuevo_menu_desc.pack(pady=5)

        ctk.CTkLabel(self.ventana_menu, text="Precio ($):").pack(pady=(5, 0))
        self.entry_nuevo_menu_precio = ctk.CTkEntry(self.ventana_menu)
        self.entry_nuevo_menu_precio.pack(pady=5)

        # --- Sección de Ingredientes ---
        ctk.CTkLabel(self.ventana_menu, text="--- Agregar Ingredientes a la Receta ---", font=("Arial", 12, "bold")).pack(pady=10)

        frame_add_ing = ctk.CTkFrame(self.ventana_menu)
        frame_add_ing.pack(pady=5, padx=10, fill="x")

        # Cargar ingredientes disponibles
        self.combo_ingredientes_menu = ctk.CTkComboBox(frame_add_ing, state="readonly")
        self.combo_ingredientes_menu.pack(side="left", padx=5, expand=True, fill="x")
        self.cargar_combo_ingredientes_ventana() # Función auxiliar

        self.entry_cant_ing_menu = ctk.CTkEntry(frame_add_ing, placeholder_text="Cant.", width=60)
        self.entry_cant_ing_menu.pack(side="left", padx=5)

        ctk.CTkButton(frame_add_ing, text="+", width=40, command=self.agregar_ingrediente_a_lista_temporal).pack(side="left", padx=5)

        # Lista visual de ingredientes agregados
        self.lista_ingredientes_label = ctk.CTkTextbox(self.ventana_menu, height=100)
        self.lista_ingredientes_label.pack(pady=10, padx=20, fill="both", expand=True)
        self.lista_ingredientes_label.insert("0.0", "Ingredientes añadidos:\n")
        self.lista_ingredientes_label.configure(state="disabled")

        # Botón Guardar Final
        ctk.CTkButton(self.ventana_menu, text="Guardar Menú", fg_color="green", command=self.guardar_nuevo_menu_bd).pack(pady=20)

    def cargar_combo_ingredientes_ventana(self):
        """Carga los ingredientes en el combobox de la ventana emergente."""
        db = self.get_db_session()
        if not db: return
        try:
            ingredientes = icrud.listar_ingredientes(db)
            self.mapa_ingredientes_temp = {i.nombre: i.id for i in ingredientes}
            self.combo_ingredientes_menu.configure(values=list(self.mapa_ingredientes_temp.keys()))
            if ingredientes:
                self.combo_ingredientes_menu.set(ingredientes[0].nombre)
        finally:
            db.close()

    def agregar_ingrediente_a_lista_temporal(self):
        """Añade un ingrediente a la lista temporal de la receta."""
        nombre_ing = self.combo_ingredientes_menu.get()
        cant_str = self.entry_cant_ing_menu.get()

        if not nombre_ing or not cant_str:
            return # Ignorar si falta dato
        
        try:
            cantidad = float(cant_str)
            if cantidad <= 0: raise ValueError
        except ValueError:
            tk.messagebox.showerror("Error", "Cantidad inválida")
            return

        ing_id = self.mapa_ingredientes_temp.get(nombre_ing)
        
        # Agregar a la lista lógica
        self.temp_receta.append({"ingrediente_id": ing_id, "cantidad": cantidad})

        # Actualizar visualización
        self.lista_ingredientes_label.configure(state="normal")
        self.lista_ingredientes_label.insert("end", f"- {nombre_ing}: {cantidad}\n")
        self.lista_ingredientes_label.configure(state="disabled")
        
        # Limpiar entrada
        self.entry_cant_ing_menu.delete(0, "end")

    def guardar_nuevo_menu_bd(self):
        """Llama al CRUD para guardar el menú completo."""
        nombre = self.entry_nuevo_menu_nombre.get().strip()
        desc = self.entry_nuevo_menu_desc.get().strip()
        precio_str = self.entry_nuevo_menu_precio.get().strip()

        if not nombre or not precio_str:
            tk.messagebox.showerror("Error", "Falta nombre o precio")
            return

        if not self.temp_receta:
            tk.messagebox.showerror("Error", "El menú debe tener al menos un ingrediente.")
            return

        try:
            precio = float(precio_str)
        except ValueError:
            tk.messagebox.showerror("Error", "El precio debe ser un número.")
            return

        db = self.get_db_session()
        if not db: return

        try:
            resultado = mcrud.crear_menu(db, nombre, desc, precio, self.temp_receta)
            
            if isinstance(resultado, str) and "Error" in resultado:
                tk.messagebox.showerror("Error BD", resultado)
            elif resultado:
                tk.messagebox.showinfo("Éxito", f"Menú '{nombre}' creado correctamente.")
                self.ventana_menu.destroy() # Cerrar ventana
                self.load_menus() # Recargar lista principal
            else:
                tk.messagebox.showerror("Error", "No se pudo crear el menú.")
        except Exception as e:
             tk.messagebox.showerror("Error Crítico", str(e))
        finally:
            db.close()




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
    # PESTAÑA 5: GRÁFICOS ESTADÍSTICOS (CORREGIDO)
    # ====================================================

    def setup_graficos_tab(self):
        tab = self.tabview.tab("Estadísticas")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1) # Fila 2 se expande para el gráfico

        # Título
        ctk.CTkLabel(tab, text="📊 Gráficos Estadísticos", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, padx=20, pady=15)

        # Frame de Controles
        control_frame = ctk.CTkFrame(tab)
        control_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        ctk.CTkLabel(control_frame, text="Tipo de Reporte:").pack(side="left", padx=10, pady=10)
        
        self.grafico_var = ctk.StringVar(control_frame)
        opciones_graficos = ["Ventas Diarias", "Ventas Mensuales", "Ventas Anuales", "Menús Más Comprados", "Uso Total de Ingredientes"]
        self.grafico_var.set(opciones_graficos[0]) 
        
        grafico_menu = ctk.CTkComboBox(control_frame, variable=self.grafico_var, values=opciones_graficos, state="readonly", width=200)
        grafico_menu.pack(side="left", padx=10, pady=10)
        
        ctk.CTkButton(control_frame, text="Generar Reporte", command=self.generate_report).pack(side="left", padx=10, pady=10)
        
        # --- CORRECCIÓN CLAVE ---
        # Definimos self.chart_frame aquí mismo para que exista cuando presionas el botón
        self.chart_frame = ctk.CTkFrame(tab)
        self.chart_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")
    
    def generate_report(self):
        """Genera el reporte llamando a graficos.py y lo incrusta en la GUI."""
        seleccion = self.grafico_var.get()
        
        db = self.get_db_session()
        if not db: return

        fig = None
        try:
            # 1. Limpiar gráfico anterior si existe (para que no se monten uno encima de otro)
            for widget in self.chart_frame.winfo_children():
                widget.destroy()

            # 2. Llamar a la función correspondiente en graficos.py según lo que elegiste en el menú
            if seleccion == "Ventas Diarias":
                fig = gcrud.generar_grafico_ventas(db, "day")
            elif seleccion == "Ventas Mensuales":
                fig = gcrud.generar_grafico_ventas(db, "month")
            elif seleccion == "Ventas Anuales":
                fig = gcrud.generar_grafico_ventas(db, "year")
            elif seleccion == "Menús Más Comprados":
                fig = gcrud.generar_grafico_menus(db)
            elif seleccion == "Uso Total de Ingredientes":
                fig = gcrud.generar_grafico_ingredientes(db)

            # 3. Dibujar el gráfico en la ventana
            if fig:
                # Esto es lo que "pega" el gráfico de Matplotlib dentro de la ventana de Tkinter
                canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
            else:
                # Si no hay ventas aun, mostramos este mensaje
                label = ctk.CTkLabel(self.chart_frame, text="No hay datos suficientes para generar este gráfico.\n(Realiza algunos pedidos primero)", font=("Arial", 16))
                label.pack(pady=50)

        except Exception as e:
            self.mostrar_mensaje(f"Error al generar gráfico: {e}", tipo="error")
        finally:
            db.close()


    #====================================================
    # PESTAÑA 6: GESTIÓN DE PEDIDOS (HISTORIAL Y DETALLE)
    # ====================================================

    def setup_pedidos_tab(self):
        tab = self.tabview.tab("Pedidos")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1) # Lista pedidos
        tab.grid_rowconfigure(3, weight=1) # Detalle pedidos

        # --- 1. Filtros y Controles ---
        filter_frame = ctk.CTkFrame(tab)
        filter_frame.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="ew")
        
        ctk.CTkLabel(filter_frame, text="Filtrar por Cliente:").pack(side="left", padx=10)
        
        # Reusamos la lógica de clientes para llenar este combo
        self.filtro_cliente_var = ctk.StringVar(value="Todos")
        self.combo_filtro_cliente = ctk.CTkComboBox(filter_frame, variable=self.filtro_cliente_var, state="readonly", width=250)
        self.combo_filtro_cliente.pack(side="left", padx=10)
        
        ctk.CTkButton(filter_frame, text="Filtrar / Actualizar", command=self.cargar_historial_pedidos).pack(side="left", padx=10)
        ctk.CTkButton(filter_frame, text="Eliminar Pedido Seleccionado", fg_color="red", command=self.eliminar_pedido_gui).pack(side="right", padx=10)

        # --- 2. Tabla Principal: LISTA DE PEDIDOS ---
        
        frame_lista = ctk.CTkFrame(tab)
        frame_lista.grid(row=1, column=0, padx=20, pady=5, sticky="nsew")
        
        self.tree_pedidos = ttk.Treeview(frame_lista, columns=("ID", "Fecha", "Cliente", "Total"), show="headings", height=8)
        self.tree_pedidos.heading("ID", text="ID")
        self.tree_pedidos.heading("Fecha", text="Fecha")
        self.tree_pedidos.heading("Cliente", text="Cliente")
        self.tree_pedidos.heading("Total", text="Total ($)")
        
        self.tree_pedidos.column("ID", width=50, anchor="center")
        self.tree_pedidos.column("Fecha", width=150, anchor="center")
        self.tree_pedidos.column("Cliente", width=200)
        self.tree_pedidos.column("Total", width=100, anchor="e")        
        
        self.tree_pedidos.pack(side="left", fill="both", expand=True)
        
        # Scrollbar para pedidos
        sb_ped = ttk.Scrollbar(frame_lista, orient="vertical", command=self.tree_pedidos.yview)
        sb_ped.pack(side="right", fill="y")
        self.tree_pedidos.configure(yscrollcommand=sb_ped.set)

        # Evento: Al hacer click en un pedido, mostrar detalle
        self.tree_pedidos.bind("<<TreeviewSelect>>", self.mostrar_detalle_pedido)

        # --- 3. Tabla Secundaria: DETALLE DEL PEDIDO ---
        ctk.CTkLabel(tab, text="Detalle del Pedido Seleccionado (Contenido)", font=("Arial", 12, "bold")).grid(row=2, column=0, sticky="w", padx=20, pady=(10,0))

        frame_detalle = ctk.CTkFrame(tab)
        frame_detalle.grid(row=3, column=0, padx=20, pady=(5, 20), sticky="nsew")

        self.tree_detalle = ttk.Treeview(frame_detalle, columns=("Menu", "Cantidad", "Precio Unit.", "Subtotal"), show="headings", height=5)
        self.tree_detalle.heading("Menu", text="Menú")
        self.tree_detalle.heading("Cantidad", text="Cantidad")
        self.tree_detalle.heading("Precio Unit.", text="Precio Unit.")
        self.tree_detalle.heading("Subtotal", text="Subtotal")
        
        self.tree_detalle.column("Menu", width=250)
        self.tree_detalle.column("Cantidad", width=80, anchor="center")
        self.tree_detalle.column("Precio Unit.", width=100, anchor="e")
        self.tree_detalle.column("Subtotal", width=100, anchor="e")
        
        self.tree_detalle.pack(side="left", fill="both", expand=True)

    def cargar_historial_pedidos(self):
        """Carga los pedidos en la tabla superior, aplicando filtro si es necesario."""
        # 1. Actualizar Combo de Clientes (por si hay nuevos)
        db = self.get_db_session()
        if not db: return
        
        try:
            # Llenar combo
            clientes = ccrud.listar_clientes(db)
            opciones = ["Todos"] + [f"{c.nombre} (ID: {c.id})" for c in clientes]
            self.combo_filtro_cliente.configure(values=opciones)
            
            # Determinar filtro
            seleccion = self.filtro_cliente_var.get()
            pedidos = []
            
            if seleccion == "Todos":
                pedidos = pcrud.leer_todos_los_pedidos(db)
            else:
                # Extraer ID del string "Nombre (ID: 5)"
                try:
                    cliente_id = int(seleccion.split("ID: ")[1].replace(")", ""))
                    pedidos = pcrud.leer_pedidos_por_cliente(db, cliente_id)
                except:
                    self.mostrar_mensaje("Error al interpretar filtro de cliente.", tipo="error")
                    pedidos = []

            # Limpiar tabla
            for item in self.tree_pedidos.get_children():
                self.tree_pedidos.delete(item)
            
            # Llenar tabla
            for p in pedidos:
                # Formato fecha seguro
                fecha_str = p.fecha.strftime("%Y-%m-%d %H:%M") if p.fecha else "---"
                nombre_cliente = p.cliente.nombre if p.cliente else "Cliente Eliminado"
                
                self.tree_pedidos.insert("", "end", values=(p.id, fecha_str, nombre_cliente, f"${p.total:,.0f}"))
                
            # Limpiar detalle
            for item in self.tree_detalle.get_children():
                self.tree_detalle.delete(item)
                
        finally:
            db.close()

    def mostrar_detalle_pedido(self, event):
        """Muestra los ítems del pedido seleccionado en la tabla inferior."""
        selected = self.tree_pedidos.focus()
        if not selected: return
        
        values = self.tree_pedidos.item(selected, "values")
        pedido_id = int(values[0])
        
        db = self.get_db_session()
        if not db: return
        
        try:
            pedido = pcrud.leer_pedido_por_id(db, pedido_id)
            
            # Limpiar tabla detalle
            for item in self.tree_detalle.get_children():
                self.tree_detalle.delete(item)
                
            if not pedido: return
            
            # Llenar con los items (relación items_comprados)
            for item in pedido.items_comprados:
                menu_nombre = item.menu.nombre if item.menu else "Menú borrado"
                precio_unit = item.menu.precio if item.menu else 0
                subtotal = precio_unit * item.cantidad
                
                self.tree_detalle.insert("", "end", values=(
                    menu_nombre, 
                    item.cantidad, 
                    f"${precio_unit:,.0f}", 
                    f"${subtotal:,.0f}"
                ))
        finally:
            db.close()

    def eliminar_pedido_gui(self):
        """Llama al CRUD para eliminar el pedido."""
        selected = self.tree_pedidos.focus()
        if not selected:
            self.mostrar_mensaje("Selecciona un pedido arriba para eliminar.", tipo="error")
            return
            
        values = self.tree_pedidos.item(selected, "values")
        pedido_id = int(values[0])
        
        if messagebox.askyesno("Confirmar", f"¿Eliminar el Pedido #{pedido_id}? Esta acción es irreversible."):
            db = self.get_db_session()
            if not db: return
            
            try:
                if pcrud.eliminar_pedido(db, pedido_id):
                    self.mostrar_mensaje(f"Pedido #{pedido_id} eliminado.", tipo="success")
                    self.cargar_historial_pedidos() # Recargar tabla
                else:
                    self.mostrar_mensaje("Error al eliminar el pedido.", tipo="error")
            finally:
                db.close()