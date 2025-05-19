from flask import Flask
from routes.single_device_routes import single_device_bp
from routes.multi_device_routes import multi_device_bp
from routes.continuous_routes import continuous_bp

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Register blueprints
    app.register_blueprint(single_device_bp)
    app.register_blueprint(multi_device_bp)
    app.register_blueprint(continuous_bp)
    
    @app.route('/')
    def index():
        """API root endpoint"""
        return {
            "status": "success",
            "message": "Modbus API Server is running",
            "api_version": "1.0.0",
            "endpoints": {
                "single_device": "/api/modbus/device",
                "multiple_devices": "/api/modbus/devices",
                "continuous_operations": [
                    "/api/modbus/device/continuous",
                    "/api/modbus/devices/continuous",
                    "/api/modbus/tasks"
                ]
            }
        }
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)