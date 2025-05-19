import os

# Create directory structure if it doesn't exist
os.makedirs('routes', exist_ok=True)

# Create __init__.py files to make directories proper Python packages
with open('routes/__init__.py', 'w') as f:
    f.write('# Routes package\n')

# Application setup
if __name__ == '__main__':
    print("Setting up the Modbus Flask API server...")
    
    try:
        from app import create_app
        
        app = create_app()
        print("Starting the server...")
        app.run(debug=True, host='0.0.0.0', port=5000)
    except ImportError as e:
        print(f"Error: {e}")
        print("Please install the required dependencies:")
        print("pip install flask pymodbus")