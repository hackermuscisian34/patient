#!/usr/bin/env python3
"""
Web Dashboard for Patient Tracking System
Provides real-time visualization of patient location and alerts
"""

from flask import Flask, render_template, jsonify, request
import sqlite3
import json
from datetime import datetime, timedelta
import math

app = Flask(__name__)

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('patient_tracking.db')
    conn.row_factory = sqlite3.Row
    return conn

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in meters"""
    R = 6371000  # Earth's radius in meters
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_lat/2)**2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * 
         math.sin(delta_lon/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/current_location')
def get_current_location():
    """Get current patient location"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM locations 
        ORDER BY timestamp DESC 
        LIMIT 1
    ''')
    
    location = cursor.fetchone()
    conn.close()
    
    if location:
        return jsonify({
            'latitude': location['latitude'],
            'longitude': location['longitude'],
            'altitude': location['altitude'],
            'speed': location['speed'],
            'timestamp': location['timestamp'],
            'accuracy': location['accuracy']
        })
    
    return jsonify({'error': 'No location data available'})

@app.route('/api/location_history')
def get_location_history():
    """Get location history for the last 24 hours"""
    hours = request.args.get('hours', 24, type=int)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    since_time = datetime.now() - timedelta(hours=hours)
    
    cursor.execute('''
        SELECT * FROM locations 
        WHERE timestamp > ?
        ORDER BY timestamp ASC
    ''', (since_time,))
    
    locations = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(locations)

@app.route('/api/alerts')
def get_alerts():
    """Get recent alerts"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM alerts 
        WHERE resolved = 0
        ORDER BY timestamp DESC
        LIMIT 50
    ''')
    
    alerts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(alerts)

@app.route('/api/mark_alert_resolved', methods=['POST'])
def mark_alert_resolved():
    """Mark alert as resolved"""
    alert_id = request.json.get('alert_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE alerts 
        SET resolved = 1 
        WHERE id = ?
    ''', (alert_id,))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/geofence_status')
def get_geofence_status():
    """Check geofence status"""
    # Load config
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    geofence = config.get('geofence', {})
    
    if not geofence.get('enabled', False):
        return jsonify({'enabled': False})
    
    # Get current location
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM locations 
        ORDER BY timestamp DESC 
        LIMIT 1
    ''')
    
    location = cursor.fetchone()
    conn.close()
    
    if not location:
        return jsonify({'enabled': True, 'status': 'unknown'})
    
    # Calculate distance from geofence center
    distance = calculate_distance(
        location['latitude'], location['longitude'],
        geofence['latitude'], geofence['longitude']
    )
    
    within_geofence = distance <= geofence['radius']
    
    return jsonify({
        'enabled': True,
        'status': 'within' if within_geofence else 'outside',
        'distance': distance,
        'radius': geofence['radius'],
        'center': {
            'latitude': geofence['latitude'],
            'longitude': geofence['longitude']
        }
    })

@app.route('/api/statistics')
def get_statistics():
    """Get tracking statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total locations recorded
    cursor.execute('SELECT COUNT(*) as count FROM locations')
    total_locations = cursor.fetchone()['count']
    
    # Locations in last 24 hours
    since_24h = datetime.now() - timedelta(hours=24)
    cursor.execute('SELECT COUNT(*) as count FROM locations WHERE timestamp > ?', (since_24h,))
    recent_locations = cursor.fetchone()['count']
    
    # Active alerts
    cursor.execute('SELECT COUNT(*) as count FROM alerts WHERE resolved = 0')
    active_alerts = cursor.fetchone()['count']
    
    # Last update time
    cursor.execute('SELECT MAX(timestamp) as last_update FROM locations')
    last_update = cursor.fetchone()['last_update']
    
    conn.close()
    
    return jsonify({
        'total_locations': total_locations,
        'recent_locations_24h': recent_locations,
        'active_alerts': active_alerts,
        'last_update': last_update
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
