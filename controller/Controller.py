from model.Model import Model
from views.View import View
from controller.ExcelGenerator import ExcelGenerator
from controller.TrendFinder import TrendFinder

class Controller:
    view = None
    model = None
    reporter = None
    trend_finder = None

    def __init__(self, root):
        self.model = Model()
        self.view = View(root, self)
        self.reporter = ExcelGenerator()
        self.trend_finder = TrendFinder()
        #self.model.add_latitud_longitude()

        if not self.model.load_preferences():
            self.open_filters()
        else:
            self.model.estaciones = self.model.user_preferences["estaciones"]
            self.update_view()
    
    def set_estacion(self, nombre):
        info = self.model.get_estacion_info(nombre)
        self.view.set_estacion_info(info, nombre)

    def update_view(self):
        self.view.create_estaciones_frame(self.model.estaciones)

    def open_filters(self):
        self.view.open_filtros()
        min_years = self.model.user_preferences["min_years"]
        max_years = self.model.user_preferences["max_years"]
        start_year = self.model.user_preferences["start_year"]
        end_year = self.model.user_preferences["end_year"]
        faltante = self.model.user_preferences["missing"]

        if self.model.user_preferences["estaciones"]:
            self.view.show_preferences(min_years, max_years, start_year, end_year, faltante)  

    def confirm_filters(self):
        min_years = 0 if self.view.input_min_years.get() == "" else int(self.view.input_min_years.get())
        max_years = 2024 if self.view.input_max_years.get() == "" else int(self.view.input_max_years.get())
        start_year = 0 if self.view.input_start_year.get() == "" else int(self.view.input_start_year.get())
        end_year = -1 if self.view.input_end_year.get() == "" else int(self.view.input_end_year.get())
        faltante = int(self.view.slider_missing_allowed.get())

        save = self.view.check_save_preferences.get()
        print(f"is save checked? {save}")
        self.model.set_estaciones(save, min_years, max_years, start_year, end_year, faltante)
        self.update_view()

        self.view.filtros_window.destroy()

    def search_trend_intervals(self, station):
        interval = self.view.display_interval_input()
        trend_intervals = self.trend_finder.search_trend(interval, station)

        if trend_intervals == 0:
            self.view.display_warning("No se encontraron periodos con tendencia")
        else:
            self.view.display_message(f"Se encontrarón {trend_intervals} periodos con tendencia")
        
        self.reporter.reset_report()

    def generate_excel(self, station):
        self.reporter.generate_trend_analysis(station, 'original_data')
        if self.reporter.missing_consecutives_months > 6:
            self.view.display_warning("Esta estación tiene más de 6 meses consecutivos faltantes, por lo que el análisis de tendencia puede estar erróneo")
        else:
            self.view.display_message("Análisis de tendencia generado exitosamente!")
        self.reporter.reset_report()

    def generate_modified_excel(self, station):
        self.reporter.generate_trend_analysis(station, 'modified_data', 2)
        if self.reporter.missing_consecutives_months > 6:
            self.view.display_warning("Esta estación tiene más de 6 meses consecutivos faltantes, por lo que el análisis de tendencia puede estar erróneo")
        else:
            self.view.display_message("Análisis de tendencia con datos modificados generado exitosamente!")
        self.reporter.reset_report()