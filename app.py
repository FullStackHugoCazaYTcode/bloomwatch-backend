from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import json
import os
from datetime import datetime
from nasa_api import NASADataFetcher
from bloom_detector import BloomDetector

app = Flask(__name__, static_folder='../frontend')
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Inicializar módulos
nasa_fetcher = NASADataFetcher()
bloom_detector = BloomDetector()

@app.route('/')
def index():
    """Servir página principal"""
    return send_from_directory('../frontend', 'index.html')

@app.route('/api/bloom-data', methods=['POST'])
def get_bloom_data():
    """Obtener datos de floración para una región específica"""
    try:
        data = request.json
        lat = data.get('latitude')
        lon = data.get('longitude')
        date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # Obtener datos satelitales
        satellite_data = nasa_fetcher.get_vegetation_index(lat, lon, date)
        
        # Analizar floración
        bloom_status = bloom_detector.analyze_bloom(satellite_data)
        
        # NUEVO: Identificar tipo de especies
        species_info = bloom_detector.identify_species_type(satellite_data, {'lat': lat, 'lon': lon})
        
        response = {
            'success': True,
            'location': {'lat': lat, 'lon': lon},
            'date': date,
            'bloom_status': bloom_status,
            'ndvi': satellite_data.get('ndvi'),
            'evi': satellite_data.get('evi'),
            'confidence': bloom_status.get('confidence', 0),
            'species_info': species_info  # NUEVO
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/bloom-prediction', methods=['POST'])
def predict_bloom():
    """Predecir floración futura"""
    try:
        data = request.json
        lat = data.get('latitude')
        lon = data.get('longitude')
        
        # Obtener datos históricos
        historical_data = nasa_fetcher.get_historical_data(lat, lon)
        
        # Predecir floración
        prediction = bloom_detector.predict_bloom_date(historical_data)
        
        return jsonify({
            'success': True,
            'predicted_bloom_date': prediction.get('date'),
            'probability': prediction.get('probability'),
            'peak_period': prediction.get('peak_period')
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/global-bloom-map', methods=['GET'])
def global_bloom_map():
    """Obtener datos de floración global"""
    try:
        # Obtener datos de múltiples regiones
        regions = [
            {'name': 'Amazon', 'lat': -3.4653, 'lon': -62.2159},
            {'name': 'Sahel', 'lat': 15.0, 'lon': 0.0},
            {'name': 'Mediterranean', 'lat': 40.0, 'lon': 10.0},
            {'name': 'North America', 'lat': 40.0, 'lon': -100.0},
            {'name': 'Southeast Asia', 'lat': 10.0, 'lon': 105.0},
            {'name': 'Australia', 'lat': -25.0, 'lon': 135.0},
        ]
        
        global_data = []
        for region in regions:
            satellite_data = nasa_fetcher.get_vegetation_index(
                region['lat'], region['lon']
            )
            bloom_status = bloom_detector.analyze_bloom(satellite_data)
            
            global_data.append({
                'name': region['name'],
                'lat': region['lat'],
                'lon': region['lon'],
                'bloom_level': bloom_status.get('level', 0),
                'status': bloom_status.get('status', 'unknown')
            })
        
        return jsonify({'success': True, 'data': global_data})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/time-series', methods=['POST'])
def get_time_series():
    """Obtener serie temporal de floración"""
    try:
        data = request.json
        lat = data.get('latitude')
        lon = data.get('longitude')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        time_series = nasa_fetcher.get_time_series(lat, lon, start_date, end_date)
        
        return jsonify({
            'success': True,
            'dates': time_series.get('dates', []),
            'ndvi_values': time_series.get('ndvi', []),
            'evi_values': time_series.get('evi', []),
            'bloom_events': time_series.get('bloom_events', [])
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# NUEVO: Comparación multi-año
@app.route('/api/multi-year-comparison', methods=['POST'])
def multi_year_comparison():
    """Comparar floración entre múltiples años para detectar cambio climático"""
    try:
        data = request.json
        lat = data.get('latitude')
        lon = data.get('longitude')
        years = data.get('years', [2023, 2024, 2025])
        
        comparison_data = []
        
        for year in years:
            # Obtener datos de primavera de cada año (marzo-mayo para hemisferio norte)
            year_data = []
            months = [3, 4, 5] if lat >= 0 else [9, 10, 11]  # Ajustar por hemisferio
            
            for month in months:
                date = f"{year}{month:02d}15"
                satellite_data = nasa_fetcher.get_vegetation_index(lat, lon, date)
                year_data.append(satellite_data['ndvi'])
            
            avg_ndvi = sum(year_data) / len(year_data)
            comparison_data.append({
                'year': year,
                'avg_ndvi': round(avg_ndvi, 3),
                'months': ['Marzo', 'Abril', 'Mayo'] if lat >= 0 else ['Sep', 'Oct', 'Nov'],
                'values': year_data
            })
        
        # Calcular tendencia
        ndvi_trend = [d['avg_ndvi'] for d in comparison_data]
        trend = 'increasing' if ndvi_trend[-1] > ndvi_trend[0] else 'decreasing'
        change_pct = ((ndvi_trend[-1] - ndvi_trend[0]) / ndvi_trend[0]) * 100 if ndvi_trend[0] > 0 else 0
        
        # Determinar impacto climático
        if abs(change_pct) > 15:
            climate_impact = 'Crítico - Cambio significativo detectado'
        elif abs(change_pct) > 8:
            climate_impact = 'Moderado - Requiere monitoreo'
        else:
            climate_impact = 'Bajo - Variación normal'
        
        return jsonify({
            'success': True,
            'years_data': comparison_data,
            'trend': trend,
            'change_percentage': round(change_pct, 1),
            'climate_impact': climate_impact,
            'interpretation': f"La floración ha {'aumentado' if trend == 'increasing' else 'disminuido'} un {abs(round(change_pct, 1))}% en los últimos {len(years)} años"
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# NUEVO: Alertas de conservación
@app.route('/api/conservation-alerts', methods=['POST'])
def conservation_alerts():
    """Generar alertas para conservación basadas en análisis"""
    try:
        data = request.json
        lat = data.get('latitude')
        lon = data.get('longitude')
        
        # Obtener datos actuales
        satellite_data = nasa_fetcher.get_vegetation_index(lat, lon)
        bloom_status = bloom_detector.analyze_bloom(satellite_data)
        
        alerts = []
        recommendations = []
        
        # Generar alertas basadas en condiciones
        ndvi = satellite_data.get('ndvi', 0)
        
        if ndvi < 0.3:
            alerts.append({
                'level': 'critical',
                'type': 'Degradación',
                'message': '⚠️ Baja vegetación detectada. Posible degradación del ecosistema.'
            })
            recommendations.append('Investigar causas de pérdida de vegetación')
            recommendations.append('Implementar medidas de restauración urgentes')
        
        if ndvi > 0.8 and satellite_data.get('temperature', 20) < 15:
            alerts.append({
                'level': 'warning',
                'type': 'Especie Invasora',
                'message': '🚨 Patrón anómalo detectado. Posible especie invasora.'
            })
            recommendations.append('Realizar inspección de campo')
            recommendations.append('Verificar especies no nativas')
        
        if bloom_status.get('level', 0) > 70:
            alerts.append({
                'level': 'info',
                'type': 'Oportunidad',
                'message': '🌸 Floración máxima. Momento óptimo para polinización.'
            })
            recommendations.append('Ubicar colmenas en la zona')
            recommendations.append('Planificar actividades de turismo ecológico')
        
        # Áreas prioritarias para conservación
        priority_score = ndvi * 100
        
        return jsonify({
            'success': True,
            'alerts': alerts,
            'recommendations': recommendations,
            'priority_score': round(priority_score, 1),
            'priority_level': 'Alta' if priority_score > 60 else 'Media' if priority_score > 30 else 'Baja'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/<path:path>')
def serve_static(path):
    """Servir archivos estáticos"""
    return send_from_directory('../frontend', path)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    print("🌸 BloomWatch Server Starting...")
    print(f"📍 Access at: http://0.0.0.0:{port}")
    print("🚀 Enhanced with Conservation & Climate Analysis")

    app.run(host='0.0.0.0', port=port, debug=False)
