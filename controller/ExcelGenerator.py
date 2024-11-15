import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from openpyxl import Workbook
from openpyxl.drawing.image import Image
from model.Model import Model
from openpyxl.styles import Font
import pymannkendall as mk

class ExcelGenerator:
    model = Model()
    wb = Workbook()
    ws = wb.active
    missing_consecutives_months = 0

    def get_original_raw_data(self, station_name):
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
    
    def get_modified_data(self, station_name, n):
        select = f"SELECT ESTCLAVE FROM ESTACIONES WHERE ESTNOMBRE = '{station_name}'"
        self.model.cursor.execute(select)
        estclave = self.model.cursor.fetchone()[0]

        select = f"select * from get_precipitation_estimation({estclave}, {n});"
        self.model.cursor.execute(select)
        raw_data = self.model.cursor.fetchall()

        return raw_data, estclave
    
    def generate_trend_analysis(self, station, data_type, n=0):
        raw_data = None

        if data_type == 'original_data':
            raw_data = self.get_original_raw_data(station)
        else:
            raw_data = self.get_modified_data(station, n)

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
        self.missing_consecutives_months = 0    
        missing = 0
        generated_data = 0

        for i, r in enumerate(raw_data[0], start=8):
            self.ws[f'B{i}'] = r[0]
            self.ws[f'C{i}'] = r[1]
            if r[3] > 15:
                self.ws[f'D{i}'] = r[2]
            self.ws[f'E{i}'] = r[3]
                
            if(r[2] == None or r[3] < 15):
                if(data_type != 'original_data'):
                    #print(f"{r[0]} {r[1]}")
                    generated_data+=1

                missing += 1
                if (missing > 6):
                    self.missing_consecutives_months = max(self.missing_consecutives_months, missing)                    
                continue
            missing = 0

            data['month'].append(i-7)            
            data['value'].append(r[2])
            max_month = i-7
            max_sum = max(max_sum, r[2])

        self.generate_scatter_plot(data, raw_data[1], max_month, max_sum)

        self.generate_rolling_mean_plot(12, raw_data[0], max_month, max_sum, raw_data[1],'H')
        self.generate_rolling_mean_plot(18, raw_data[0], max_month, max_sum, raw_data[1],'I')

        scatter_plot_img = Image(f'./imgs/scatter_plot_{raw_data[1]}.png')
        rolling_mean_12 = Image(f'./imgs/rolling_mean_12_{raw_data[1]}.png')
        rolling_mean_18 = Image(f'./imgs/rolling_mean_18_{raw_data[1]}.png')

        self.ws.add_image(scatter_plot_img, 'P8')  
        self.ws.add_image(rolling_mean_12, 'P33')
        self.ws.add_image(rolling_mean_18, 'AA33')

        self.ws['K5'] = f'Datos generados: {generated_data}'
        self.ws['K5'].font = Font(name='Arial', size=12, bold=True, color="000000")

        if data_type == 'original_data':
            self.wb.save(f'./excels/analisis_tendencia_precipitacion_{station}.xlsx')     
        else:
            self.wb.save(f'./excels/analisis_tendencia_precipitacion_modificado_{station}.xlsx')     
             
    def generate_mannkendall_test(self, data):
        self.ws['K10'] = 'trend'
        self.ws['K11'] = 'H'
        self.ws['K12'] = 'P'
        self.ws['K13'] = 'Z'
        self.ws['K14'] = 'Tau'
        self.ws['K15'] = 'S'
        self.ws['K16'] = 'Var_S'
        self.ws['K17'] = 'Slope'
        self.ws['K18'] = 'Intercept'

        result = mk.original_test(data)
        self.ws['L10'] = result.trend
        self.ws['L11'] = result.h
        self.ws['L12'] = result.p
        self.ws['L13'] = result.z
        self.ws['L14'] = result.Tau
        self.ws['L15'] = result.s
        self.ws['L16'] = result.var_s
        self.ws['L17'] = result.slope
        self.ws['L18'] = result.intercept

        result = mk.seasonal_test(data)
        self.ws['M10'] = result.trend
        self.ws['M11'] = result.h
        self.ws['M12'] = result.p
        self.ws['M13'] = result.z
        self.ws['M14'] = result.Tau
        self.ws['M15'] = result.s
        self.ws['M16'] = result.var_s
        self.ws['M17'] = result.slope
        self.ws['M18'] = result.intercept

        result = mk.sens_slope(data)
        self.ws['N17'] = result.slope
        self.ws['N18'] = result.intercept

    def generate_scatter_plot(self, data, estclave, max_month, max_value):
        df = pd.DataFrame(data)

        plt.scatter(df['month'], df['value'], color='blue', alpha=0.5, label='Sum-Precipitacion')
        df['value'] = df['value'].astype(float)

        trend = np.polyfit(df['month'], df['value'], 1)
        trend_line = np.poly1d(trend)

        plt.plot(df['month'], trend_line(df['month']), color='red', linewidth=1, label='Trend Line')
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

    def generate_rolling_mean_plot(self, window, raw_data, max_month, max_value, estclave, letter):
        data = {
            'month' : [],
            'value' : []
        }
        sum = 0.0
        n = 0

        max_month = 0
        max_value = 0
        for i in range (0, window):
            if raw_data[i][2] != None:
                sum += float(raw_data[i][2])
                n += 1
        
        l = 0
        for i in range (window, len(raw_data) - window):
            if n <= 0:
                break
            
            average = sum / n
            max_value = max(average, max_value)
            max_month = i+1
            data['value'].append(average)
            data['month'].append(i+1)
            self.ws[f'{letter}{int(i-window+(8+window/2-1))}'] = average

            if(raw_data[l][2] != None):
                n -= 1
                sum -= float(raw_data[l][2])
            if(raw_data[i][2] != None):
                n+=1
                sum+=float(raw_data[i][2])
            l+=1

        if(window == 12):  
            self.generate_mannkendall_test(data['value'])

        # for i in range (int(max_month - (window/2))):
        #     self.ws[f'H{int(i+8+(window/2)-1)}'] = f'=AVERAGE(D{int(i+8)}:D{int(i+8+window-1)})'

        df = pd.DataFrame(data)
        df['rolling-window'] = df['value'].astype(float)

        trend = np.polyfit(df['month'], df['rolling-window'], 1)
        trend_line = np.poly1d(trend)

        plt.plot(df['month'], trend_line(df['month']), color='red', linewidth=1, label='Trend Line')
        
        plt.text(max_month*0.65, max_value*0.8,  ("y = %.6fx+(%.6f)"%(trend[0],trend[1])), fontsize = 8, color='red')

        plt.plot(df['month'], df['rolling-window'], label=f'Promedio móvil {window} meses', linestyle='solid')

        plt.xlabel('Mes')
        plt.ylabel('Precipitacion')
        plt.title(f'Promedio móvil {window} meses')
        plt.legend()

        plt.savefig(f'./imgs/rolling_mean_{window}_{estclave}.png')
        plt.close()         