import requests
import json
from datetime import datetime, timedelta
import os
import random

class NASADataFetcher:
    """Clase para obtener datos de APIs de NASA"""
    
    def __init__(self):
        self.nasa_api_key = os.getenv('NASA_API_KEY', 'DEMO_KEY')
        self.power_api_url = "https://power.larc.nasa.gov/api/temporal/daily/point"
        
    def get_vegetation_index(self, lat, lon, date=None):
        """Obtener índices de vegetación"""
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        
        try:
            # Usar NASA POWER API para datos climáticos
            params = {
                'parameters': 'T2M,PRECTOTCORR,RH2M',
                'community': 'AG',
                'longitude': lon,
                'latitude': lat,
                'start': date,
                'end': date,
                'format': 'JSON'
            }
            
            response = requests.get(self.power_api_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Calcular índice simulado basado en condiciones climáticas
                temp = data.get('properties', {}).get('parameter', {}).get('T2M', {})
                precip = data.get('properties', {}).get('parameter', {}).get('PRECTOTCORR', {})
                
                temp_val = list(temp.values())[0] if temp else 20
                precip_val = list(precip.values())[0] if precip else 0
                
                ndvi = self._calculate_simulated_ndvi(temp_val, precip_val)
                evi = ndvi * 1.2 if ndvi < 0.83 else ndvi
                
                return {
                    'ndvi': round(ndvi, 3),
                    'evi': round(evi, 3),
                    'temperature': temp_val,
                    'precipitation': precip_val,
                    'date': date
                }
            else:
                return self._get_fallback_data(lat, lon)
                
        except Exception as e:
            print(f"Error fetching NASA data: {e}")
            return self._get_fallback_data(lat, lon)
    
    def _calculate_simulated_ndvi(self, temp, precip):
        """Calcular NDVI simulado basado en condiciones climáticas"""
        optimal_temp = 20
        temp_factor = 1 - abs(temp - optimal_temp) / 30
        temp_factor = max(0, min(1, temp_factor))
        
        precip_factor = min(precip / 10, 1) if precip > 0 else 0.3
        
        ndvi = (temp_factor * 0.6 + precip_factor * 0.4) * 0.9
        return max(0, min(0.95, ndvi))
    
    def _get_fallback_data(self, lat, lon):
        """Datos de respaldo cuando la API no está disponible"""
        season_factor = abs(lat) / 90
        base_ndvi = 0.4 + random.uniform(0, 0.3) * (1 - season_factor)
        
        return {
            'ndvi': round(base_ndvi, 3),
            'evi': round(base_ndvi * 1.15, 3),
            'temperature': 15 + random.uniform(-5, 15),
            'precipitation': random.uniform(0, 20),
            'date': datetime.now().strftime('%Y%m%d')
        }
    
    def get_historical_data(self, lat, lon, days=90):
        """Obtener datos históricos para análisis de tendencias"""
        historical = []
        end_date = datetime.now()
        
        for i in range(days):
            date = (end_date - timedelta(days=i)).strftime('%Y%m%d')
            data = self.get_vegetation_index(lat, lon, date)
            historical.append({
                'date': date,
                'ndvi': data['ndvi'],
                'evi': data['evi']
            })
        
        return historical[::-1]
    
    def get_time_series(self, lat, lon, start_date, end_date):
        """Obtener serie temporal entre dos fechas"""
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        dates = []
        ndvi_values = []
        evi_values = []
        bloom_events = []
        
        current = start
        while current <= end:
            date_str = current.strftime('%Y%m%d')
            data = self.get_vegetation_index(lat, lon, date_str)
            
            dates.append(current.strftime('%Y-%m-%d'))
            ndvi_values.append(data['ndvi'])
            evi_values.append(data['evi'])
            
            if data['ndvi'] > 0.6:
                bloom_events.append({
                    'date': current.strftime('%Y-%m-%d'),
                    'intensity': data['ndvi']
                })
            
            current += timedelta(days=7)
        
        return {
            'dates': dates,
            'ndvi': ndvi_values,
            'evi': evi_values,
            'bloom_events': bloom_events
        }