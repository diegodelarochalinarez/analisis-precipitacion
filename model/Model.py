from bs4 import BeautifulSoup
import requests
import re
import psycopg2 as psql
from model.ETL import ETL  
from datetime import datetime
import json

class Model:
    conn = psql.connect(database="Precipitacion",
                        host="172.20.160.1",
                        user="diego",
                        password="root",
                        port="5432")
    
    cursor = conn.cursor()

    user_preferences = {
        "start_year" : 0,
        "end_year" : -1, 
        "min_years" : 0,
        "max_years" : -1,
        "missing" : 20,
        "estaciones" : []
    }

    def __init__(self):
        self.codigos = {}
        self.estaciones = []

    def get_estaciones(self):
        return self.estaciones

    def set_data(self, new_data):
        self.data = new_data

    def set_estaciones(self, save, min_years, max_years, start_year, end_year, faltante):
        if end_year == -1:
            end_year = datetime.now().year
        
        selectsql = f"""SELECT ESTNOMBRE
                        FROM ESTACIONES 
                        WHERE ESTCLAVE IN (
                            SELECT DISTINCT ESTCLAVE
                            FROM REGISTRODIARIO
                            WHERE date_part('year',  fecha) >= %s AND date_part('year', fecha) <= %s
                        ) AND fn_total_years(ESTCLAVE) >= %s AND fn_total_years(ESTCLAVE) <= %s
                        AND fn_missing_percentage(ESTCLAVE) < %s
                    """

        self.cursor.execute(selectsql, (start_year, end_year, min_years, max_years, faltante,))
        result = self.cursor.fetchall()
        print(len(result))

        self.estaciones = []
        for r in result:
            self.estaciones.append(r[0])

        if save == "on":
            self.user_preferences["start_year"] = start_year
            self.user_preferences["end_year"] = end_year
            self.user_preferences["min_years"] = min_years
            self.user_preferences["max_years"] = max_years
            self.user_preferences["missing"] = faltante
            self.user_preferences["estaciones"] = self.estaciones

            self.save_preferences()

    def get_estacion_info(self, nombre):
        estacion_info = ""

        estacion_info += f"Previsualización de los datos de la estación: {nombre}\n\n"
        estacion_info += "Fecha                | Precipitacion\n"

        select = f"SELECT ESTCLAVE FROM ESTACIONES WHERE ESTNOMBRE = '{nombre}';"
        self.cursor.execute(select)
        clave = self.cursor.fetchone()

        select = f"SELECT FECHA, PRECIPITACION FROM REGISTRODIARIO WHERE estclave = {clave[0]} ORDER BY FECHA;"
        self.cursor.execute(select)
        result = self.cursor.fetchall()
      
        for t in result:
            estacion_info += f"{t[0]}      |        {t[1]}\n"
        return estacion_info
    
    def save_preferences(self, filename='user_preferences.json'):
        with open(filename, 'w') as file:
            json.dump(self.user_preferences, file, indent=4)
        print("Preferences saved!")

    def load_preferences(self, filename='user_preferences.json'):
        try:
            with open(filename, 'r') as file:
                self.user_preferences = json.load(file)
            print("Preferences loaded!")
            return True
        except FileNotFoundError:
            print("Preferences file not found!")
            return False
        
    def bulk_estaciones(self):
        page = requests.get('https://smn.conagua.gob.mx/tools/RESOURCES/Normales_Climatologicas/catalogo/cat_sin.html').text
        soup = BeautifulSoup(page, 'lxml')

        estaciones_html = soup.find_all('tr')
        
        estaciones = []
        for index, estacion in enumerate(estaciones_html):
            if(index < 2):
                continue

            row = estacion.find_all('td')
            nombre_estacion = row[1].text.strip()
            codigo_estacion =row[0].text.strip()
            municipio = row[2].text.strip()
            situacion = row[3].text.strip()

            self.codigos[nombre_estacion] = codigo_estacion
            
            # insert = "INSERT INTO ESTACIONES (ESTCLAVE, ESTNOMBRE, MUNICIPIO, SITUACION) VALUES (%s, %s, %s, %s);"

            # try:
            #     self.cursor.execute(insert, (codigo_estacion, nombre_estacion, municipio, situacion,))
            # except:
            #     print("error")

            estaciones.append(str(nombre_estacion))  
        
        # self.conn.commit()
        # self.conn.close()
        return estaciones

    def add_latitud_longitude(self):
        select = "SELECT ESTCLAVE FROM ESTACIONES"
        self.cursor.execute(select)
        claves = self.cursor.fetchall()

        for c in claves:
            clave = c[0]

            page = requests.get(f'https://smn.conagua.gob.mx/tools/RESOURCES/Normales_Climatologicas/Diarios/sin/dia{clave}.txt')
            
            content = page.content.decode('utf-8')
            content = content.replace('\r\n', '\n').replace('\r', '\n')
            content = content.split('\n')

            latitud = None
            longitud = None

            for row in content:
                row = row.split()
                
                if len(row) > 0 and "LATITUD" == row[0]:
                    latitud = row[2]
                if len(row) > 0 and "LONGITUD" == row[0]:
                    longitud = row[2]
                
                if latitud != None and longitud != None:
                    break
            
            update = f"UPDATE ESTACIONES SET LONGITUD = %s, LATITUD = %s WHERE ESTCLAVE = %s"
            self.cursor.execute(update, (longitud, latitud, clave))
        
        self.conn.commit()


    def bulk_registro_diario(self, nombre):
        clave = self.codigos[nombre]
        page = requests.get(f'https://smn.conagua.gob.mx/tools/RESOURCES/Normales_Climatologicas/Diarios/sin/dia{clave}.txt')
        
        content = page.content.decode('utf-8')
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        date_pattern = r"(\d{4}-\d{2}-\d{2})"
        content = content.split('\n')

        matches = []
        for row in content:
            row = row.split()
            
            if len(row) > 0 and re.search(date_pattern, row[0]):
                matches.append(row)

        dates_only = [date[0] for date in matches]
        
        valid_dates, invalid_dates = ETL.parse_dates(dates_only)
        missing_dates = ETL.find_missing_dates(valid_dates)

        i = 0
        j = 0

        parsed_info = []
        content = f"Fecha / Precipitación de la estación: {nombre} \n\n"
        content+=(f"Fechas válidas: {len(valid_dates)}\n")
        content+=(f"Fechas no válidas: {len(invalid_dates)}\n")
        content+=(f"Dias faltantes: {len(missing_dates)}\n\n")

        insert = "INSERT INTO REGISTRODIARIO (ESTCLAVE, FECHA, PRECIPITACION, EVAPORACION, TEMPERATURA_MAX, TEMPERATURA_MIN) VALUES (%s, %s, %s, %s, %s, %s)"
        tuple = []
        null_precipitacion = 0

        while i < len(valid_dates) and j < len(missing_dates):
            if(valid_dates[i] < missing_dates[j] or j == len(missing_dates)):
                tuple = [valid_dates[i], None, None, None, None]

                if(matches[i][1] != "NULO"):
                    tuple[1] = matches[i][1]
                else:
                    null_precipitacion+=1

                if(matches[i][2] != "NULO"):
                    tuple[2] = matches[i][2]

                if(matches[i][3] != "NULO"):
                    tuple[3] = matches[i][3]

                if(matches[i][4] != "NULO"):
                    tuple[4] = matches[i][4]
                
                self.cursor.execute(insert, (clave, tuple[0], tuple[1],tuple[2], tuple[3],tuple[4],))    
 
                content += (f"{tuple}\n")
                i+=1
            else:
                tuple = [missing_dates[j], None, None, None, None]
                null_precipitacion+=1

                self.cursor.execute(insert, (clave, tuple[0], tuple[1],tuple[2], tuple[3],tuple[4],))

                content += (f"{tuple}\n")
                j+=1

        while i < len(valid_dates):
            tuple = [valid_dates[i], None, None, None, None]

            if(matches[i][1] != "NULO"):
                tuple[1] = matches[i][1]
            else:
                null_precipitacion+=1

            if(matches[i][2] != "NULO"):
                tuple[2] = matches[i][2]

            if(matches[i][3] != "NULO"):
                tuple[3] = matches[i][3]

            if(matches[i][4] != "NULO"):
                tuple[4] = matches[i][4]
            self.cursor.execute(insert, (clave, tuple[0], tuple[1],tuple[2], tuple[3],tuple[4],))    

            content += (f"{tuple}\n")
            i+=1

        while j < len(missing_dates):
            tuple = [missing_dates[j], None, None, None, None]
            null_precipitacion+=1
            self.cursor.execute(insert, (clave, tuple[0], tuple[1],tuple[2], tuple[3],tuple[4],))
            content += (f"{tuple}\n")
            j+=1

        print(null_precipitacion)
        sql_missing = f"UPDATE ESTACIONES SET FALTANTES = {null_precipitacion} WHERE ESTCLAVE = {clave};"
        try:
            self.cursor.execute(sql_missing)
            self.conn.commit()
        except:
            print("Error while commiting changes")

        return content
    
    def initial_bulk(self):
        try:
            for i in self.estaciones:
                self.bulk_registro_diario(i)
        except:
            print("Something went wrong while bulking")
            return
        
        print("Bulked succesfully !!")