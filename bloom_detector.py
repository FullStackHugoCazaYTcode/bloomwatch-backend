from datetime import datetime, timedelta

class BloomDetector:
    """Algoritmo para detectar y predecir floración"""
    
    def __init__(self):
        self.bloom_threshold_ndvi = 0.6
        self.bloom_threshold_evi = 0.65
        self.growth_rate_threshold = 0.05
        
    def analyze_bloom(self, satellite_data):
        """Analizar si hay floración activa"""
        ndvi = satellite_data.get('ndvi', 0)
        evi = satellite_data.get('evi', 0)
        temp = satellite_data.get('temperature', 20)
        precip = satellite_data.get('precipitation', 0)
        
        bloom_level = self._calculate_bloom_level(ndvi, evi, temp, precip)
        
        if bloom_level >= 70:
            status = 'peak_bloom'
            confidence = 0.85 + (bloom_level - 70) / 100
            color = '#00ff00'
        elif bloom_level >= 50:
            status = 'active_bloom'
            confidence = 0.70 + (bloom_level - 50) / 100
            color = '#90ee90'
        elif bloom_level >= 30:
            status = 'early_bloom'
            confidence = 0.55 + (bloom_level - 30) / 100
            color = '#ffff00'
        else:
            status = 'no_bloom'
            confidence = 0.40 + bloom_level / 100
            color = '#808080'
        
        return {
            'status': status,
            'level': bloom_level,
            'confidence': round(min(confidence, 0.95), 2),
            'color': color,
            'ndvi': ndvi,
            'evi': evi,
            'message': self._get_status_message(status, bloom_level)
        }
    
    def _calculate_bloom_level(self, ndvi, evi, temp, precip):
        """Calcular nivel de floración (0-100)"""
        veg_factor = ((ndvi + evi) / 2) * 40
        
        temp_optimal = 20
        temp_deviation = abs(temp - temp_optimal)
        temp_factor = max(0, (10 - temp_deviation) / 10) * 30
        
        precip_factor = min(precip / 15, 1) * 30 if precip > 0 else 5
        
        bloom_level = veg_factor + temp_factor + precip_factor
        return round(min(bloom_level, 100), 1)
    
    def _get_status_message(self, status, level):
        """Obtener mensaje descriptivo del estado"""
        messages = {
            'peak_bloom': f'🌸 Floración máxima detectada ({level}% intensidad)',
            'active_bloom': f'🌺 Floración activa ({level}% intensidad)',
            'early_bloom': f'🌱 Inicio de floración ({level}% intensidad)',
            'no_bloom': f'🍃 No hay floración activa ({level}% vegetación)'
        }
        return messages.get(status, 'Estado desconocido')
    
    def predict_bloom_date(self, historical_data):
        """Predecir fecha de próxima floración"""
        if len(historical_data) < 14:
            return {
                'date': 'Datos insuficientes',
                'probability': 0,
                'peak_period': 'N/A'
            }
        
        bloom_dates = []
        for i in range(len(historical_data) - 1):
            curr = historical_data[i]
            next_data = historical_data[i + 1]
            
            if (next_data['ndvi'] > self.bloom_threshold_ndvi and 
                next_data['ndvi'] - curr['ndvi'] > self.growth_rate_threshold):
                bloom_dates.append(curr['date'])
        
        if not bloom_dates:
            return {
                'date': 'No hay patrón histórico',
                'probability': 0.3,
                'peak_period': 'Variable'
            }
        
        avg_interval = self._calculate_average_interval(bloom_dates)
        last_bloom = bloom_dates[-1]
        
        last_bloom_date = datetime.strptime(last_bloom, '%Y%m%d')
        predicted_date = last_bloom_date + timedelta(days=avg_interval)
        
        probability = min(0.95, 0.6 + len(bloom_dates) * 0.05)
        
        return {
            'date': predicted_date.strftime('%Y-%m-%d'),
            'probability': round(probability, 2),
            'peak_period': f'{avg_interval} días desde última floración',
            'historical_blooms': len(bloom_dates)
        }
    
    def _calculate_average_interval(self, dates):
        """Calcular intervalo promedio entre floraciones"""
        if len(dates) < 2:
            return 90
        
        intervals = []
        for i in range(len(dates) - 1):
            date1 = datetime.strptime(dates[i], '%Y%m%d')
            date2 = datetime.strptime(dates[i + 1], '%Y%m%d')
            intervals.append((date2 - date1).days)
        
        return int(sum(intervals) / len(intervals))
    
    # NUEVO: Identificación de especies y tipo de vegetación
    def identify_species_type(self, satellite_data, location):
        """
        Identificar tipo de especies basado en patrones de floración y ubicación
        Proporciona inferencias ecológicas
        """
        ndvi = satellite_data.get('ndvi', 0)
        evi = satellite_data.get('evi', 0)
        temp = satellite_data.get('temperature', 20)
        precip = satellite_data.get('precipitation', 0)
        lat = location.get('lat', 0)
        
        species_hints = []
        ecosystem_type = ""
        ecological_notes = []
        
        # Clasificación por región climática
        if -23.5 <= lat <= 23.5:  # Zona tropical
            ecosystem_type = "Tropical"
            if ndvi > 0.7:
                species_hints.append("Selva tropical densa")
                ecological_notes.append("Alta biodiversidad esperada")
            if temp > 25 and precip > 10:
                species_hints.append("Flores tropicales: Orquídeas, Heliconias, Jengibre")
                ecological_notes.append("Período óptimo para polinizadores")
        
        elif 23.5 < abs(lat) <= 66.5:  # Zona templada
            ecosystem_type = "Templado"
            if 15 < temp < 25 and ndvi > 0.5:
                species_hints.append("Árboles frutales en floración")
                species_hints.append("Posibles especies: Cerezos, Manzanos, Duraznos")
                ecological_notes.append("Momento crítico para control de plagas")
            
            if ndvi > 0.6 and 10 < temp < 20:
                species_hints.append("Flores silvestres de primavera")
                ecological_notes.append("Importante para polinizadores nativos")
        
        else:  # Zona polar/subpolar
            ecosystem_type = "Boreal/Polar"
            if ndvi > 0.3:
                species_hints.append("Tundra floreciente o bosque boreal")
                ecological_notes.append("Ventana corta de floración - sensible a cambio climático")
        
        # Detección de patrones agrícolas
        if 0.4 < ndvi < 0.7 and 0.5 < evi < 0.8:
            species_hints.append("🌾 Patrón agrícola detectado")
            if temp > 20:
                species_hints.append("Cultivos posibles: Algodón, Girasoles, Canola")
                ecological_notes.append("Fase pre-floración crítica para aplicación de fertilizantes")
            else:
                species_hints.append("Cultivos de clima frío: Trigo, Cebada")
        
        # Detección de especies invasoras (anomalías)
        if ndvi > 0.75 and temp < 10:
            species_hints.append("⚠️ ALERTA: Posible especie invasora")
            ecological_notes.append("Floración anómala fuera de temporada normal")
            ecological_notes.append("Requiere inspección de campo urgente")
        
        # Evaluación de degradación
        if ndvi < 0.25:
            species_hints.append("Vegetación escasa o degradada")
            ecological_notes.append("⚠️ Posible desertificación o sobreexplotación")
            ecological_notes.append("Área prioritaria para restauración")
        
        # Potencial para biodiversidad
        biodiversity_score = self._calculate_biodiversity_potential(ndvi, evi, temp, precip)
        
        return {
            'ecosystem_type': ecosystem_type,
            'species_hints': species_hints if species_hints else ["Vegetación general"],
            'ecological_notes': ecological_notes if ecological_notes else ["Condiciones normales"],
            'biodiversity_potential': biodiversity_score,
            'confidence': 'Alta' if len(species_hints) > 2 else 'Media' if len(species_hints) > 0 else 'Baja',
            'conservation_priority': 'Alta' if ndvi > 0.6 or ndvi < 0.3 else 'Media'
        }
    
    def _calculate_biodiversity_potential(self, ndvi, evi, temp, precip):
        """Calcular potencial de biodiversidad"""
        # Valores más altos de NDVI y EVI generalmente indican mayor biodiversidad
        veg_score = (ndvi + evi) / 2 * 50
        
        # Temperatura y precipitación óptimas
        temp_score = 30 if 15 < temp < 28 else 15
        precip_score = 20 if precip > 5 else 10
        
        total_score = veg_score + temp_score + precip_score
        
        if total_score > 80:
            return "Muy Alto - Ecosistema rico"
        elif total_score > 60:
            return "Alto - Biodiversidad significativa"
        elif total_score > 40:
            return "Moderado - Biodiversidad estándar"
        else:
            return "Bajo - Ecosistema limitado"