import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from openpyxl import Workbook
from openpyxl.drawing.image import Image
from model.Model import Model
from openpyxl.styles import Font

class ExcelGenerator:
    model = Model()
    wb = Workbook()
    ws = wb.active

    def get_raw_data(self, station_name):
        select = f"SELECT ESTCLAVE FROM ESTACIONES WHERE ESTNOMBRE = '{station_name}'"
        self.model.cursor.execute(select)
        estclave = self.model.cursor.fetchone()[0]

        select = f"""
                    SELECT EXTRACT(YEAR FROM fecha) AS year, 
                        EXTRACT(MONTH FROM fecha) AS month, 
                        SUM(precipitacion) AS total_precipitacion, 
                        COUNT(CASE WHEN precipitacion IS NOT NULL THEN 1 END) AS registros
                    FROM registrodiario
                    WHERE ESTCLAVE = {estclave}
                    GROUP BY EXTRACT(YEAR FROM fecha), EXTRACT(MONTH FROM fecha)
                    ORDER BY EXTRACT(YEAR FROM fecha), EXTRACT(MONTH FROM fecha);
        """
        self.model.cursor.execute(select)
        raw_data = self.model.cursor.fetchall()
        return raw_data, estclave

    def generate_trend_analysis(self, station):
        raw_data = self.get_raw_data(station)

        self.ws.title = "Analisis de Tendencia"

        self.ws['B3'] = 'Análisis de tendencia: ' + str(station) + ' (' + str(raw_data[1]) + ')'
        self.ws['B3'].font = Font(name='Arial', size=14, bold=True, color="000000")

        self.ws['B5'] = 'Datos crudos'
        self.ws['B5'].font = Font(name='Arial', size=12, bold=True, color="000000")

        self.ws['H5'] = 'Promedio móvil'
        self.ws['H5'].font = Font(name='Arial', size=12, bold=True, color="000000")

        self.ws['B7'] = 'Año'
        self.ws['C7'] = 'Mes'
        self.ws['D7'] = 'Sum-Precipitacion'
        self.ws['E7'] = 'N'

        data = {
            'month': [],
            'value': []
        }
        
        max_month = 0
        max_sum = 0
        for i, r in enumerate(raw_data[0], start=8):
            self.ws[f'B{i}'] = r[0]
            self.ws[f'C{i}'] = r[1]
            self.ws[f'D{i}'] = r[2]
            self.ws[f'E{i}'] = r[3]
            if(r[2] == None):
                continue
            data['month'].append(i-7)            
            data['value'].append(r[2])
            max_month = i-7
            max_sum = max(max_sum, r[2])

        self.generate_scatter_plot(data, raw_data[1], max_month, max_sum)

        self.generate_rolling_mean_plot(12, raw_data[0], max_month, max_sum, raw_data[1])

        scatter_plot_img = Image(f'./imgs/scatter_plot_{raw_data[1]}.png')
        rolling_mean_12 = Image(f'./imgs/rolling_mean_12_{raw_data[1]}.png')

        self.ws.add_image(scatter_plot_img, 'P8')  
        self.ws.add_image(rolling_mean_12, 'P33')

        
        self.wb.save(f'./excels/analisis_tendencia_precipitacion_{raw_data[1]}.xlsx')     

    def generate_scatter_plot(self, data, estclave, max_month, max_value):
        df = pd.DataFrame(data)
        plt.scatter(df['month'], df['value'], color='blue', alpha=0.5, label='Sum-Precipitacion')
        df['value'] = df['value'].astype(float)

        trend = np.polyfit(df['month'], df['value'], 1)
        trend_line = np.poly1d(trend)

        plt.plot(df['month'], trend_line(df['month']), color='red', linewidth=1, label='Trend Line')
        print(("y = %.6fx+(%.6f)"%(trend[0],trend[1])))
        plt.text(float(max_month)*0.65, float(max_value)*0.80,  ("y = %.6fx+(%.6f)"%(trend[0],trend[1])), fontsize = 8, color='red')

        for i in range(len(df) - 1):
                        plt.plot([df['month'].iloc[i], df['month'].iloc[i + 1]], 
                        [df['value'].iloc[i], df['value'].iloc[i + 1]], 
                        color='blue', linestyle='dashed', linewidth=1)

        plt.xlabel("Meses")
        plt.ylabel("Suma precipitacion")
        plt.title("Serie de tiempo")
        plt.legend()

        plt.savefig(f'./imgs/scatter_plot_{estclave}.png')
        plt.close()

        print('scatter plot for ' + str(estclave) + ' was generated')

    def generate_rolling_mean_plot(self, window, raw_data, max_month, max_value, estclave):
        data = {
            'month' : [],
            'value' : []
        }

        for i in range (int(max_month - (window/2))):
            self.ws[f'H{int(i+8+(window/2)-1)}'] = f'=AVERAGE(D{int(i+8)}:D{int(i+8+window-1)})'
            data['month'].append(i+1)
            print(self.ws[f'D{i+1}'].value)            

        data = {
            'month' : [],
            'value' : []
        }

        for i, r in enumerate(raw_data, start=8):
            data['month'].append(i-7)            
            data['value'].append(r[2])

        df = pd.DataFrame(data)
        df['rolling-window'] = df['value'].astype(float)

        for i, value in enumerate(df['rolling-window'], start=13):
            self.ws[f'I{i}'] = value

        trend = np.polyfit(df['month'], df['rolling-window'], 1)
        trend_line = np.poly1d(trend)

        plt.plot(df['rolling-window'], trend_line(df['month']), color='red', linewidth=1, label='Trend Line')
        print(("y = %.6fx+(%.6f)"%(trend[0],trend[1])))
        plt.text(float(max_month)*0.65, float(max_value)*0.80,  ("y = %.6fx+(%.6f)"%(trend[0],trend[1])), fontsize = 8, color='red')

        plt.plot(df.index, df['rolling-window'], label=f'Promedio móvil {window} meses', linestyle='solid')
        plt.xlabel('Mes')
        plt.ylabel('Precipitacion')
        plt.title(f'Promedio móvil {window} meses')
        plt.legend()

        plt.savefig(f'./imgs/rolling_mean_{window}_{estclave}.png')
        plt.close()

        print(f'rolling mean plot with a window of {window} for {estclave} was generated')
         

        
