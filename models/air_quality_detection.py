import cv2
import numpy as np
import random

class air_quality_detection:
    """
    Air quality monitoring using visual cues and simulated sensor data.
    Detects smoke, dust, and other airborne particles.
    """
    
    def __init__(self, conf=0.60):
        self.confidence = conf
        self.air_quality_levels = {
            'good': (0, 50),
            'moderate': (51, 100),
            'unhealthy_sensitive': (101, 150),
            'unhealthy': (151, 200),
            'very_unhealthy': (201, 300),
            'hazardous': (301, 500)
        }
        
    def analyze_visibility(self, frame):
        """Analyze frame visibility to detect air quality issues"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Calculate image contrast and brightness
        contrast = np.std(gray)
        brightness = np.mean(gray)
        
        # Calculate visibility score (0-100)
        visibility_score = min(100, (contrast / 50) * 100)
        
        return visibility_score
    
    def detect_particles(self, frame):
        """Detect airborne particles using image processing"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Detect particles using background subtraction simulation
        # In real implementation, this would use background subtraction
        diff = cv2.absdiff(gray, blurred)
        
        # Threshold to find particles
        _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
        
        # Count particles
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        particle_count = len([c for c in contours if cv2.contourArea(c) > 5])
        
        return particle_count
    
    def simulate_sensor_data(self):
        """Simulate air quality sensor data (PM2.5, CO2, etc.)"""
        # In real implementation, this would read from actual sensors
        pm25 = random.randint(10, 200)  # PM2.5 levels
        co2 = random.randint(400, 1000)  # CO2 levels in ppm
        humidity = random.randint(30, 80)  # Humidity percentage
        temperature = random.randint(18, 35)  # Temperature in Celsius
        
        return {
            'pm25': pm25,
            'co2': co2,
            'humidity': humidity,
            'temperature': temperature
        }
    
    def calculate_aqi(self, pm25):
        """Calculate Air Quality Index from PM2.5 levels"""
        if pm25 <= 12:
            return int(((50 - 0) / (12 - 0)) * (pm25 - 0) + 0)
        elif pm25 <= 35.4:
            return int(((100 - 51) / (35.4 - 12.1)) * (pm25 - 12.1) + 51)
        elif pm25 <= 55.4:
            return int(((150 - 101) / (55.4 - 35.5)) * (pm25 - 35.5) + 101)
        elif pm25 <= 150.4:
            return int(((200 - 151) / (150.4 - 55.5)) * (pm25 - 55.5) + 151)
        elif pm25 <= 250.4:
            return int(((300 - 201) / (250.4 - 150.5)) * (pm25 - 150.5) + 201)
        else:
            return int(((500 - 301) / (500.4 - 250.5)) * (pm25 - 250.5) + 301)
    
    def get_air_quality_level(self, aqi):
        """Get air quality level from AQI"""
        for level, (min_val, max_val) in self.air_quality_levels.items():
            if min_val <= aqi <= max_val:
                return level
        return 'hazardous'
    
    def process(self, img, flag=True):
        """
        Process frame for air quality monitoring
        Returns: (air_quality_alert, sensor_data, quality_level)
        """
        if not flag:
            return (False, {}, 'good')
        
        # Analyze visual indicators
        visibility = self.analyze_visibility(img)
        particle_count = self.detect_particles(img)
        
        # Get simulated sensor data
        sensor_data = self.simulate_sensor_data()
        
        # Calculate AQI
        aqi = self.calculate_aqi(sensor_data['pm25'])
        quality_level = self.get_air_quality_level(aqi)
        
        # Combine visual and sensor data for alert
        visual_score = max(0, 100 - visibility) + (particle_count / 10)
        air_quality_alert = aqi > 100 or visual_score > 50
        
        # Draw air quality information on frame
        color = self.get_quality_color(quality_level)
        
        # Display AQI and level
        cv2.putText(img, f"AQI: {aqi}", (10, 120), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.putText(img, f"Air Quality: {quality_level.replace('_', ' ').title()}", (10, 150), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Display sensor readings
        cv2.putText(img, f"PM2.5: {sensor_data['pm25']} μg/m³", (10, 180), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(img, f"CO2: {sensor_data['co2']} ppm", (10, 200), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Add warning if air quality is poor
        if air_quality_alert:
            cv2.putText(img, "AIR QUALITY ALERT!", (10, 250), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
        enhanced_sensor_data = {
            **sensor_data,
            'aqi': aqi,
            'visibility': visibility,
            'particle_count': particle_count
        }
        
        return (air_quality_alert, enhanced_sensor_data, quality_level)
    
    def get_quality_color(self, quality_level):
        """Get color for different air quality levels"""
        colors = {
            'good': (0, 255, 0),                    # Green
            'moderate': (0, 255, 255),              # Yellow
            'unhealthy_sensitive': (0, 165, 255),   # Orange
            'unhealthy': (0, 0, 255),               # Red
            'very_unhealthy': (128, 0, 128),        # Purple
            'hazardous': (128, 0, 0)                # Maroon
        }
        return colors.get(quality_level, (255, 255, 255))