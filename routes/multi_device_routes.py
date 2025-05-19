from flask import Blueprint, request, jsonify
from modbus_controller import ModbusController, ModbusError

# Create Blueprint for multi-device operations
multi_device_bp = Blueprint('multi_device', __name__, url_prefix='/api/modbus/devices')

@multi_device_bp.route('', methods=['POST'])
def multi_device_operation():
    """Perform operations on multiple devices"""
    try:
        data = request.get_json()
        operations = data.get('operations', [])
        results = []
        
        for op in operations:
            # Extract device connection parameters
            host = op.get('host', '127.0.0.1')
            port = op.get('port', 502)
            timeout = op.get('timeout', 30)
            slave_id = op.get('slave_id', 1)
            
            # Extract operation parameters
            operation = op.get('operation', 'read')
            reg_type = op.get('reg_type', 'holding')
            address = op.get('address', 0)
            count = op.get('count', 1)
            data_type = op.get('data_type', 'int16')
            value = op.get('value', None)
            
            try:
                controller = ModbusController(host, port, timeout)
                
                if operation == 'read':
                    result = controller.read_data(reg_type, address, count, slave_id, data_type)
                    results.append({
                        "status": "success",
                        "host": host,
                        "port": port,
                        "data": result
                    })
                elif operation == 'write':
                    if value is None:
                        results.append({
                            "status": "error",
                            "host": host,
                            "port": port,
                            "message": "Value is required for write operations"
                        })
                        continue
                    controller.write_data(address, value, slave_id, data_type)
                    results.append({
                        "status": "success",
                        "host": host,
                        "port": port,
                        "message": "Write operation completed"
                    })
                else:
                    results.append({
                        "status": "error",
                        "host": host,
                        "port": port,
                        "message": "Invalid operation. Use 'read' or 'write'"
                    })
                
                controller.close()
                
            except ModbusError as e:
                results.append({
                    "status": "error",
                    "host": host,
                    "port": port,
                    "message": str(e)
                })
            except Exception as e:
                results.append({
                    "status": "error",
                    "host": host,
                    "port": port,
                    "message": f"Unexpected error: {str(e)}"
                })
        
        return jsonify({"status": "success", "results": results})
            
    except Exception as e:
        return jsonify({"status": "error", "message": f"Unexpected error: {str(e)}"}), 500