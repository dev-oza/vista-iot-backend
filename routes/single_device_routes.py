from flask import Blueprint, request, jsonify
from modbus_controller import ModbusController, ModbusError

# Create Blueprint for single device operations
single_device_bp = Blueprint('single_device', __name__, url_prefix='/api/modbus/device')

@single_device_bp.route('', methods=['POST'])
def single_device_operation():
    """Perform a single read or write operation on one device"""
    try:
        data = request.get_json()
        
        # Extract device connection parameters
        host = data.get('host', '127.0.0.1')
        port = data.get('port', 502)
        timeout = data.get('timeout', 30)
        slave_id = data.get('slave_id', 1)
        
        # Extract operation parameters
        operation = data.get('operation', 'read')  # 'read' or 'write'
        reg_type = data.get('reg_type', 'holding')  # 'holding' or 'input'
        address = data.get('address', 0)
        count = data.get('count', 1)
        data_type = data.get('data_type', 'int16')  # 'int16', 'uint16', 'float32', etc.
        
        # Value only needed for write operations
        value = data.get('value', None)
        
        controller = ModbusController(host, port, timeout)
        
        if operation == 'read':
            result = controller.read_data(reg_type, address, count, slave_id, data_type)
            controller.close()
            return jsonify({"status": "success", "data": result})
        elif operation == 'write':
            if value is None:
                return jsonify({"status": "error", "message": "Value is required for write operations"}), 400
            controller.write_data(address, value, slave_id, data_type)
            controller.close()
            return jsonify({"status": "success", "message": "Write operation completed"})
        else:
            controller.close()
            return jsonify({"status": "error", "message": "Invalid operation. Use 'read' or 'write'"}), 400
            
    except ModbusError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Unexpected error: {str(e)}"}), 500