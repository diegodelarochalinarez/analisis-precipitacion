import customtkinter as ctk
import tkinter as ttk
from tkinter import messagebox

class View:
    input_end_year = None
    input_start_year = None
    input_min_years = None
    input_max_years = None
    slider_missing_allowed = None
    check_save_preferences = None
    save_preferences = None
    station_selected = None

    def __init__(self, root, controller):
        self.root = root
        self.controller = controller
        self.filtros_window = None
        self.frame_estaciones = None
        
        self.frame_estaciones = ctk.CTkScrollableFrame(master=self.root, height=720, width=250)
        self.frame_estaciones.grid(row=0, column=0, columnspan=1, rowspan=2, sticky='NSEW')

        self.frame_contenido = ctk.CTkFrame(master=root, width=900, height=1200, fg_color='transparent')
        self.frame_contenido.grid(row=0, column=1, sticky='nsew')
        
        self.textbox_estacion_info = ctk.CTkTextbox(master=self.frame_contenido, width=900, height=500, state='normal')
        self.textbox_estacion_info.grid(row=0, column=0, columnspan=3, padx=50, pady=25, sticky='new')
        
        self.frame_buttons = ctk.CTkFrame(master=self.frame_contenido, fg_color='transparent') 
        self.frame_buttons.grid(row=1, column=0, columnspan=4, padx=15, pady=10, sticky='sew')  

        self.frame_buttons.grid_columnconfigure((0, 1, 2, 3), weight=1)  

        self.btn_open_filters = ctk.CTkButton(master=self.frame_buttons, text='Filtros', command=self.controller.open_filters)
        self.btn_open_filters.grid(row=0, column=0, padx=10, pady=10, sticky='ew')  

        self.btn_scan_trend = ctk.CTkButton(master=self.frame_buttons, text='Buscar tendencia', command = lambda: self.controller.search_trend_intervals(self.station_selected))
        self.btn_scan_trend.grid(row=0, column=1, padx=10, pady=10, sticky='ew')  

        self.btn_download_modified = ctk.CTkButton(
            master=self.frame_buttons, text='Descargar base de datos modificada',
            command=lambda: self.controller.generate_modified_excel(self.station_selected))
        self.btn_download_modified.grid(row=0, column=2, padx=10, pady=10, sticky='ew') 

        self.btn_download_original = ctk.CTkButton(
            master=self.frame_buttons, text='Descargar original',
            command=lambda: self.controller.generate_excel(self.station_selected))
        self.btn_download_original.grid(row=0, column=3, padx=10, pady=10, sticky='ew')
        
        self.frame_contenido.grid_rowconfigure(0, weight=1)
        self.frame_contenido.grid_rowconfigure(1, weight=0)
        self.frame_contenido.grid_columnconfigure(0, weight=1)
        self.frame_contenido.grid_columnconfigure(1, weight=1)
        self.frame_contenido.grid_columnconfigure(2, weight=1)

    def slider_info(self, value):
        self.lbl_slider_value.configure(text=f"{int(value)}%")

    def open_filtros(self):
        if self.filtros_window is None or not self.filtros_window.winfo_exists():
            self.create_filtros_window() 
        else:
            self.filtros_window.focus()  

    def create_filtros_window(self):
        self.filtros_window = ctk.CTkToplevel(self.root)

        self.filtros_window.title("Selección de filtros")
        self.filtros_window.geometry("325x400")
        self.filtros_window.resizable(width=False, height=False)
        self.filtros_window.grid_rowconfigure(7, weight=1)
        self.filtros_window.grid_columnconfigure(2, weight=1)
        
        lbl_filtros = ctk.CTkLabel(master=self.filtros_window, text="Filtros", font=ctk.CTkFont(weight="bold", size=16))
        lbl_filtros.grid(row=0, sticky="nw", padx="10", pady="10")

        lbl_periodo = ctk.CTkLabel(master=self.filtros_window, text="Periodo", font=ctk.CTkFont(size=14))
        lbl_periodo.grid(row=1, sticky="nw", padx="10", pady="10")

        self.input_start_year = ctk.CTkEntry(master=self.filtros_window, placeholder_text="Año inicial")
        self.input_end_year = ctk.CTkEntry(master=self.filtros_window, placeholder_text="Año final")
        self.input_start_year.grid(row=2, column=0, padx=2, pady="10")
        self.input_end_year.grid(row=2, column=1, padx=2, pady="10")
        
        lbl_data_years = ctk.CTkLabel(master=self.filtros_window, text="Años de datos",font=ctk.CTkFont(size=14))
        lbl_data_years.grid(row=3, sticky="nw", padx="10")

        self.input_min_years = ctk.CTkEntry(master=self.filtros_window, placeholder_text="Mínimo")
        self.input_min_years.grid(row=4, column=0, pady="10")
        self.input_max_years = ctk.CTkEntry(master=self.filtros_window, placeholder_text="Máximo")
        self.input_max_years.grid(row=4, column=1, pady="10")

        lbl_missing_allowed = ctk.CTkLabel(master=self.filtros_window, text="% Faltante permitido:",font=ctk.CTkFont(size=14))
        lbl_missing_allowed.grid(row=5, sticky ="nw", padx="10")

        
        self.lbl_slider_value = ctk.CTkLabel(master=self.filtros_window, text="20%", font=ctk.CTkFont(weight="bold", size=14))
        self.lbl_slider_value.grid(row = 5, column = 1)

        self.slider_missing_allowed = ctk.CTkSlider(master=self.filtros_window, width=300, from_=0, to=100,number_of_steps=100, command=self.slider_info)
        self.slider_missing_allowed.grid(row=6,  sticky="nw", columnspan=2, pady="10", padx="10")
        self.slider_missing_allowed.set(20)

        btn_aceptar = ctk.CTkButton(master=self.filtros_window, text="Aceptar", command=self.controller.confirm_filters, width=100)
        btn_aceptar.grid(row=7, column=1)
        
        self.check_save_preferences = ctk.CTkCheckBox(self.filtros_window, text="Guardar preferencias",
                                            variable=self.save_preferences, onvalue="on", offvalue="off")
        self.check_save_preferences.grid(row=7, column=0, padx=10)
        #CENTER WINDOW  
        w = 325 
        h = 400 
        ws = self.root.winfo_screenwidth()
        hs = self.root.winfo_screenheight() 
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)
        self.filtros_window.geometry('%dx%d+%d+%d' % (w, h, x, y))
    
    def display_message(self, message):
        messagebox.showinfo("Mensaje!", message)

    def display_warning(self, message):
        messagebox.showwarning("Mensaje", message)

    def display_interval_input(self):
        dialog = ctk.CTkInputDialog(text="Ingresa el intervalo de búsqueda de tendencia:", title="Búsqueda de tendencia")
        return (int) (dialog.get_input())
        
    def create_estaciones_frame(self, nombres):
        self.frame_estaciones = ctk.CTkScrollableFrame(master=self.root, height=720, width=250)
        self.frame_estaciones.grid(row=0, column=0, columnspan=1, rowspan=2, sticky='NSEW')

        self.frame_estaciones_label = ctk.CTkLabel(self.frame_estaciones, text="  Estaciones Sinaloa",
                                                   compound="left", font=ctk.CTkFont(size=15, weight="bold"))
        self.frame_estaciones_label.grid(row=0, column=0, sticky='nsew')

        self.btn_estaciones = []
        for i, nombre in enumerate(nombres):
            button = ctk.CTkButton(self.frame_estaciones, corner_radius=0, height=40, border_spacing=10, text=nombre,
                                    fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                    anchor="w", command=lambda t=nombre: self.controller.set_estacion(t))
            button.grid(row=i+1, column=0, sticky='ew')
            self.btn_estaciones.append(button)
    
    def show_preferences(self, min_years, max_years, start_year, end_year, faltante):
        self.input_end_year.delete(0, "end")
        self.input_min_years.delete(0, "end")
        self.input_max_years.delete(0, "end")
        self.input_start_year.delete(0, "end")
        self.input_end_year.insert(0, end_year)
        self.input_min_years.insert(0, min_years)
        self.input_max_years.insert(0, max_years)
        self.input_start_year.insert(0, start_year)
        self.lbl_slider_value.configure(text=f"{faltante}%")
        self.slider_missing_allowed.set(faltante)

    def set_estacion_info(self, info, nombre):
        self.textbox_estacion_info.delete("0.0", "end")
        self.textbox_estacion_info.insert("0.0", info)
        self.station_selected = nombre

    def create_table(self):
            style = ttk.Style()
        
            style.theme_use("default")

            style.configure("Treeview",
                            background="#2a2d2e",
                            foreground="white",
                            rowheight=25,
                            fieldbackground="#343638",
                            bordercolor="#343638",
                            borderwidth=0)
            style.map('Treeview', background=[('selected', '#22559b')])

            style.configure("Treeview.Heading",
                            background="#565b5e",
                            foreground="white",
                            relief="flat")
            style.map("Treeview.Heading",
                        background=[('active', '#3484F0')])
        