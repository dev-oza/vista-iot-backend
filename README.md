# Modbus TCP API Server

A Flask-based REST API server for interacting with Modbus TCP devices. This server provides endpoints for both single-device and multi-device operations, supporting various data types and register operations.

## Features

- Single device read/write operations
- Multi-device batch operations
- Support for various data types (int16, uint16, int32, uint32, int64, uint64, float32, float64, string, bool)
- Support for both holding and input registers
- Built-in Modbus TCP server for testing

## Installation

1. Create a virtual environment:
```bash
python3 -m venv venv
```

2. Activate the virtual environment:
```bash
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Server

Start the Flask server:
```bash
python3 app.py
```

The server will start on `http://localhost:5000`

## API Endpoints

### 1. Root Endpoint
- **URL**: `/`
- **Method**: `GET`
- **Description**: Returns API information and available endpoints
- **Response Example**:
```json
{
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
```

### 2. Single Device Operations
- **URL**: `/api/modbus/device`
- **Method**: `POST`
- **Description**: Perform read or write operations on a single Modbus device

#### Read Operation Example:
```json
{
    "operation": "read",
    "host": "127.0.0.1",
    "port": 502,
    "slave_id": 1,
    "reg_type": "holding",
    "address": 0,
    "count": 5,
    "data_type": "int16",
    "timeout": 30
}
```

#### Write Operation Example:
```json
{
    "operation": "write",
    "host": "127.0.0.1",
    "port": 502,
    "slave_id": 1,
    "address": 0,
    "value": 42,
    "data_type": "int16",
    "timeout": 30
}
```

#### Success Response Example:
```json
{
    "status": "success",
    "data": [1, 2, 3, 4, 5]  // For read operations
}
```
or
```json
{
    "status": "success",
    "message": "Write operation completed"  // For write operations
}
```

### 3. Multi-Device Operations
- **URL**: `/api/modbus/devices`
- **Method**: `POST`
- **Description**: Perform batch operations on multiple Modbus devices

#### Request Example:
```json
{
    "operations": [
        {
            "operation": "read",
            "host": "127.0.0.1",
            "port": 502,
            "slave_id": 1,
            "reg_type": "holding",
            "address": 0,
            "count": 2,
            "data_type": "int16"
        },
        {
            "operation": "write",
            "host": "192.168.1.100",
            "port": 502,
            "slave_id": 1,
            "address": 10,
            "value": 100,
            "data_type": "int16"
        }
    ]
}
```

#### Success Response Example:
```json
{
    "status": "success",
    "results": [
        {
            "status": "success",
            "host": "127.0.0.1",
            "port": 502,
            "data": [42, 2]
        },
        {
            "status": "success",
            "host": "192.168.1.100",
            "port": 502,
            "message": "Write operation completed"
        }
    ]
}
```

## Supported Data Types

- `bool`: Boolean value (1 bit)
- `int16`: 16-bit signed integer
- `uint16`: 16-bit unsigned integer
- `int32`: 32-bit signed integer
- `uint32`: 32-bit unsigned integer
- `int64`: 64-bit signed integer
- `uint64`: 64-bit unsigned integer
- `float32`: 32-bit floating point
- `float64`: 64-bit floating point
- `string[N]`: String with N bytes (e.g., "string[10]" for 10-byte string)

## Testing

1. Start the test Modbus server and run the test suite:
```bash
python3 test_api.py
```

This will:
- Start a Modbus TCP server on port 5020
- Start the Flask API server
- Run test cases for single and multi-device operations

## Error Handling

All endpoints return error responses in the following format:
```json
{
    "status": "error",
    "message": "Error description"
}
```

Common error scenarios:
- Connection failures
- Invalid data types
- Missing required parameters
- Invalid register addresses
- Timeout errors

## Development

### Project Structure
```
backend/
├── app.py              # Flask application setup
├── modbus_controller.py # Modbus TCP client implementation
├── modbus_server.py    # Test Modbus TCP server
├── test_api.py         # API test suite
├── requirements.txt    # Python dependencies
└── routes/
    ├── __init__.py
    ├── single_device_routes.py
    ├── multi_device_routes.py
    └── continuous_routes.py
```
