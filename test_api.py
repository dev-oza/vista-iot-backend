import requests
import json
import time
from threading import Thread
from modbus_server import setup_server

def test_single_device_read():
    """Test reading from a single device"""
    url = "http://localhost:5000/api/modbus/device"
    payload = {
        "operation": "read",
        "reg_type": "holding",
        "address": 0,
        "count": 5,
        "data_type": "int16",
        "port": 5020  # Use higher port number
    }
    response = requests.post(url, json=payload)
    print("\nRead Test:")
    print(json.dumps(response.json(), indent=2))

def test_single_device_write():
    """Test writing to a single device"""
    url = "http://localhost:5000/api/modbus/device"
    payload = {
        "operation": "write",
        "address": 0,
        "value": 42,
        "data_type": "int16",
        "port": 5020  # Use higher port number
    }
    response = requests.post(url, json=payload)
    print("\nWrite Test:")
    print(json.dumps(response.json(), indent=2))
    
    # Read back the written value
    payload["operation"] = "read"
    payload["count"] = 1
    response = requests.post(url, json=payload)
    print("\nRead Back Test:")
    print(json.dumps(response.json(), indent=2))

def test_multi_device():
    """Test operations on multiple devices"""
    url = "http://localhost:5000/api/modbus/devices"
    payload = {
        "operations": [
            {
                "operation": "read",
                "reg_type": "holding",
                "address": 0,
                "count": 2,
                "data_type": "int16",
                "port": 5020
            },
            {
                "operation": "write",
                "address": 10,
                "value": 100,
                "data_type": "int16",
                "port": 5020
            }
        ]
    }
    response = requests.post(url, json=payload)
    print("\nMulti-Device Test:")
    print(json.dumps(response.json(), indent=2))

def run_tests():
    """Run all API tests"""
    print("Starting API tests...")
    time.sleep(2)  # Wait for servers to start
    
    test_single_device_read()
    test_single_device_write()
    test_multi_device()

if __name__ == "__main__":
    # Start Modbus server in a separate thread with higher port
    modbus_thread = Thread(target=lambda: setup_server(port=5020))
    modbus_thread.daemon = True
    modbus_thread.start()
    
    # Start Flask server
    flask_thread = Thread(target=lambda: __import__('app').create_app().run(debug=False))
    flask_thread.daemon = True
    flask_thread.start()
    
    # Run tests
    run_tests()
