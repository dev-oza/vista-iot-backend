from flask import Blueprint, request, jsonify
import threading
import time
from modbus_controller import ModbusController, ModbusError

# Dictionary to store active continuous tasks
continuous_tasks = {}
next_task_id = 0
task_lock = threading.Lock()

# Create Blueprint for continuous operations
continuous_bp = Blueprint('continuous', __name__, url_prefix='/api/modbus')

@continuous_bp.route('/device/continuous', methods=['POST'])
def start_continuous_operation():
    """Start continuous read or write operations on a single device"""
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
        data_type = data.get('data_type', 'int16')
        
        # Continuous operation specific parameters
        interval = data.get('interval', 1.0)  # seconds between operations
        callback_url = data.get('callback_url', None)  # Optional webhook URL to send results to
        
        # Value only needed for write operations
        value = data.get('value', None)
        
        if operation == 'write' and value is None:
            return jsonify({"status": "error", "message": "Value is required for write operations"}), 400
        
        # Create a new continuous task
        controller = ModbusController(host, port, timeout)
        stop_event = threading.Event()
        
        global next_task_id
        with task_lock:
            task_id = next_task_id
            next_task_id += 1
            
            # Store task info
            continuous_tasks[task_id] = {
                'stop_event': stop_event,
                'thread': None,
                'status': 'starting',
                'device': f"{host}:{port}",
                'operation': operation
            }
        
        # Define the worker function
        def continuous_worker(controller, stop_event, operation, reg_type, address, 
                              count, slave_id, data_type, value, interval, callback_url):
            try:
                while not stop_event.is_set():
                    try:
                        if operation == 'read':
                            result = controller.read_data(reg_type, address, count, slave_id, data_type)
                            # If webhook callback is provided, send the result (not implemented here)
                            if callback_url:
                                # This would be implemented with requests library
                                pass
                        else:  # write
                            controller.write_data(address, value, slave_id, data_type)
                    
                    except Exception as e:
                        print(f"Error in continuous operation: {str(e)}")
                    
                    # Wait for the next interval
                    time.sleep(interval)
            finally:
                controller.close()
        
        # Start the worker thread
        worker_thread = threading.Thread(
            target=continuous_worker,
            args=(controller, stop_event, operation, reg_type, address, count, 
                  slave_id, data_type, value, interval, callback_url)
        )
        worker_thread.daemon = True
        worker_thread.start()
        
        # Update task info
        with task_lock:
            continuous_tasks[task_id]['thread'] = worker_thread
            continuous_tasks[task_id]['status'] = 'running'
        
        return jsonify({
            "status": "success", 
            "message": "Continuous operation started", 
            "task_id": task_id
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error starting continuous operation: {str(e)}"}), 500


@continuous_bp.route('/device/continuous/<int:task_id>', methods=['DELETE'])
def stop_continuous_operation(task_id):
    """Stop a continuous operation task"""
    with task_lock:
        if task_id not in continuous_tasks:
            return jsonify({"status": "error", "message": "Task not found"}), 404
        
        task = continuous_tasks[task_id]
        if task['status'] != 'running':
            return jsonify({"status": "error", "message": f"Task is not running, current status: {task['status']}"}), 400
        
        # Signal the thread to stop
        task['stop_event'].set()
        task['status'] = 'stopping'
    
    # Wait for the thread to terminate (with timeout)
    task['thread'].join(timeout=5.0)
    
    with task_lock:
        if task['thread'].is_alive():
            task['status'] = 'stop_timeout'
            return jsonify({"status": "warning", "message": "Task stop signal sent, but thread is still running"})
        else:
            task['status'] = 'stopped'
            return jsonify({"status": "success", "message": "Task stopped successfully"})


@continuous_bp.route('/devices/continuous', methods=['POST'])
def start_continuous_multiple_devices():
    """Start continuous operations on multiple devices"""
    try:
        data = request.get_json()
        devices = data.get('devices', [])
        interval = data.get('interval', 1.0)
        callback_url = data.get('callback_url', None)
        
        if not devices:
            return jsonify({"status": "error", "message": "No devices specified"}), 400
        
        # Create controller for each device
        controllers = []
        for device in devices:
            host = device.get('host', '127.0.0.1')
            port = device.get('port', 502)
            timeout = device.get('timeout', 30)
            controllers.append(ModbusController(host, port, timeout))
        
        # Create stop event and task
        stop_event = threading.Event()
        
        global next_task_id
        with task_lock:
            task_id = next_task_id
            next_task_id += 1
            
            continuous_tasks[task_id] = {
                'stop_event': stop_event,
                'thread': None,
                'status': 'starting',
                'device': 'multiple',
                'operation': 'multiple'
            }
        
        # Worker function for multiple devices
        def multi_device_worker(controllers, devices, stop_event, interval, callback_url):
            try:
                while not stop_event.is_set():
                    results = []
                    
                    for i, device in enumerate(devices):
                        try:
                            controller = controllers[i]
                            operation = device.get('operation', 'read')
                            reg_type = device.get('reg_type', 'holding')
                            address = device.get('address', 0)
                            count = device.get('count', 1)
                            slave_id = device.get('slave_id', 1)
                            data_type = device.get('data_type', 'int16')
                            value = device.get('value', None)
                            
                            if operation == 'read':
                                result = controller.read_data(reg_type, address, count, slave_id, data_type)
                                results.append({
                                    "device": f"{device.get('host')}:{device.get('port')}",
                                    "status": "success",
                                    "data": result
                                })
                            elif operation == 'write':
                                if value is not None:
                                    controller.write_data(address, value, slave_id, data_type)
                                    results.append({
                                        "device": f"{device.get('host')}:{device.get('port')}",
                                        "status": "success",
                                        "message": "Write operation completed"
                                    })
                                else:
                                    results.append({
                                        "device": f"{device.get('host')}:{device.get('port')}",
                                        "status": "error",
                                        "message": "Value is required for write operations"
                                    })
                        
                        except Exception as e:
                            results.append({
                                "device": f"{device.get('host')}:{device.get('port')}",
                                "status": "error",
                                "message": str(e)
                            })
                    
                    # If webhook callback is provided, send the results
                    if callback_url:
                        # This would be implemented with requests library
                        pass
                        
                    time.sleep(interval)
            
            finally:
                for controller in controllers:
                    controller.close()
        
        # Start the worker thread
        worker_thread = threading.Thread(
            target=multi_device_worker,
            args=(controllers, devices, stop_event, interval, callback_url)
        )
        worker_thread.daemon = True
        worker_thread.start()
        
        # Update task info
        with task_lock:
            continuous_tasks[task_id]['thread'] = worker_thread
            continuous_tasks[task_id]['status'] = 'running'
        
        return jsonify({
            "status": "success", 
            "message": "Continuous multi-device operation started", 
            "task_id": task_id
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error starting continuous operation: {str(e)}"}), 500


@continuous_bp.route('/tasks', methods=['GET'])
def list_tasks():
    """List all active tasks"""
    with task_lock:
        task_list = [{
            "id": tid,
            "status": task["status"],
            "device": task["device"],
            "operation": task["operation"]
        } for tid, task in continuous_tasks.items()]
    
    return jsonify({
        "status": "success",
        "tasks": task_list
    })