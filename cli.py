import argparse
from modbus_controller import ModbusController, ModbusError

def main():
    """Command-line interface for Modbus operations"""
    parser = argparse.ArgumentParser(description="Modbus TCP Client Tool")
    
    # Connection parameters
    parser.add_argument('--enabled', type=bool, default=True, help='Enable Modbus')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='Server IP')
    parser.add_argument('--port', type=int, default=502, help='Server Port')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout in seconds')
    parser.add_argument('--slave-id', type=int, default=1, help='Slave ID')
    
    # Operation parameters
    parser.add_argument('--mode-op', choices=['read', 'write'], default='read', help='Read or Write')
    parser.add_argument('--reg-type', choices=['input', 'holding'], default='holding', help='Register type')
    parser.add_argument('--address', type=int, default=0, help='Start register address')
    parser.add_argument('--count', type=int, default=1, help='Number of values to read/write')
    parser.add_argument('--data-type', type=str, default='int16', 
                        help='Data type (int16, uint16, int32, uint32, float32, float64, etc.)')
    parser.add_argument('--value', type=str, help='Value to write (required for write operations)')
    
    args = parser.parse_args()
    
    if not args.enabled:
        print("Modbus is disabled.")
        return
    
    try:
        # Create controller
        controller = ModbusController(args.host, args.port, args.timeout)
        print(f"Connected to Modbus server at {args.host}:{args.port}")
        
        try:
            # Perform operation
            if args.mode_op == 'read':
                result = controller.read_data(
                    args.reg_type, args.address, args.count, args.slave_id, args.data_type
                )
                print(f"Read successful. Value(s): {result}")
            
            elif args.mode_op == 'write':
                if args.value is None:
                    raise ModbusError("Value is required for write operations")
                
                # Convert value based on data type
                value = args.value
                if args.data_type in ('int16', 'int32', 'int64'):
                    value = int(value)
                elif args.data_type in ('uint16', 'uint32', 'uint64'):
                    value = int(value)
                elif args.data_type in ('float32', 'float64'):
                    value = float(value)
                elif args.data_type == 'bool':
                    value = value.lower() in ('true', 't', 'yes', 'y', '1')
                
                controller.write_data(args.address, value, args.slave_id, args.data_type)
                print("Write operation successful")
        
        finally:
            controller.close()
            print("Connection closed")
    
    except ModbusError as e:
        print(f"Modbus error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()