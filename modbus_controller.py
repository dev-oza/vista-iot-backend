from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException
from pymodbus.payload import BinaryPayloadBuilder, BinaryPayloadDecoder
from pymodbus.constants import Endian
import struct

class ModbusError(Exception):
    """Custom exception for Modbus errors"""
    pass

class ModbusController:
    """Controller class for Modbus operations with support for different data types"""
    
    def __init__(self, host, port=502, timeout=30):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.client = ModbusTcpClient(host=host, port=port, timeout=timeout)
        self.connected = False
        self.connect()
    
    def connect(self):
        """Connect to the Modbus server"""
        if not self.connected:
            self.connected = self.client.connect()
            if not self.connected:
                raise ModbusError(f"Failed to connect to Modbus server at {self.host}:{self.port}")
        return self.connected
    
    def close(self):
        """Close the connection to the Modbus server"""
        if self.connected:
            self.client.close()
            self.connected = False
    
    def read_data(self, reg_type, address, count, slave_id=1, data_type='int16'):
        """
        Read data from Modbus registers
        
        Args:
            reg_type (str): 'holding' or 'input'
            address (int): Register start address
            count (int): Number of registers to read
            slave_id (int): Slave ID
            data_type (str): Data type to interpret the result
                             Supported types: 
                             - int16, uint16, int32, uint32, int64, uint64
                             - float32, float64
                             - string[N] (N bytes)
                             - bool
        
        Returns:
            Data read from registers in the specified format
        """
        # Ensure connected
        if not self.connected:
            self.connect()
        
        # Determine how many registers to read based on data type
        registers_to_read = self._get_register_count_for_type(data_type, count)
        
        # Read registers
        if reg_type == 'holding':
            result = self.client.read_holding_registers(address=address, count=registers_to_read, slave=slave_id)
        elif reg_type == 'input':
            result = self.client.read_input_registers(address=address, count=registers_to_read, slave=slave_id)
        else:
            raise ModbusError(f"Invalid register type: {reg_type}. Use 'holding' or 'input'")
        
        # Check for errors
        if result.isError():
            raise ModbusError(f"Error reading registers: {result}")
        
        # Decode the result based on data type
        return self._decode_registers(result.registers, data_type, count)
    
    def write_data(self, address, value, slave_id=1, data_type='int16'):
        """
        Write data to Modbus holding registers
        
        Args:
            address (int): Register start address
            value: Value to write (type depends on data_type)
            slave_id (int): Slave ID
            data_type (str): Data type of value
                             Supported types: 
                             - int16, uint16, int32, uint32, int64, uint64
                             - float32, float64
                             - string[N] (N bytes)
                             - bool
        """
        # Ensure connected
        if not self.connected:
            self.connect()
        
        # Encode value to registers
        registers = self._encode_value(value, data_type)
        
        # Use appropriate write function based on number of registers
        if len(registers) == 1:
            result = self.client.write_register(address=address, value=registers[0], slave=slave_id)
        else:
            result = self.client.write_registers(address=address, values=registers, slave=slave_id)
        
        # Check for errors
        if result.isError():
            raise ModbusError(f"Error writing registers: {result}")
        
        return True
    
    def _get_register_count_for_type(self, data_type, count=1):
        """Calculate how many registers to read based on data type"""
        # Each register is 16 bits (2 bytes)
        if data_type.startswith('string['):
            # For strings, extract the byte count from the format string[N]
            try:
                string_length = int(data_type.split('[')[1].split(']')[0])
                # Calculate registers needed (2 bytes per register, rounded up)
                return (string_length + 1) // 2 * count
            except (IndexError, ValueError):
                raise ModbusError(f"Invalid string data type format: {data_type}. Use 'string[N]'")
        
        # Standard data types
        registers_per_type = {
            'bool': 1,
            'int16': 1,
            'uint16': 1,
            'int32': 2,
            'uint32': 2,
            'float32': 2,
            'int64': 4,
            'uint64': 4,
            'float64': 4,
        }
        
        if data_type not in registers_per_type:
            raise ModbusError(f"Unsupported data type: {data_type}")
        
        return registers_per_type[data_type] * count
    
    def _decode_registers(self, registers, data_type, count=1):
        """Decode register values based on data type"""
        # Create a decoder with the register values
        decoder = BinaryPayloadDecoder.fromRegisters(
            registers,
            byteorder=Endian.BIG,
            wordorder=Endian.LITTLE  # Most Modbus devices use this order
        )
        
        # Special case for strings
        if data_type.startswith('string['):
            try:
                string_length = int(data_type.split('[')[1].split(']')[0])
                result = decoder.decode_string(string_length).decode('utf-8')
                return result
            except (IndexError, ValueError):
                raise ModbusError(f"Invalid string data type format: {data_type}")
        
        # Handle multiple values
        if count > 1:
            results = []
            for _ in range(count):
                results.append(self._decode_single_value(decoder, data_type))
            return results
        else:
            return self._decode_single_value(decoder, data_type)
    
    def _decode_single_value(self, decoder, data_type):
        """Decode a single value from the decoder based on data type"""
        if data_type == 'bool':
            return decoder.decode_bits()[0]
        elif data_type == 'int16':
            return decoder.decode_16bit_int()
        elif data_type == 'uint16':
            return decoder.decode_16bit_uint()
        elif data_type == 'int32':
            return decoder.decode_32bit_int()
        elif data_type == 'uint32':
            return decoder.decode_32bit_uint()
        elif data_type == 'int64':
            return decoder.decode_64bit_int()
        elif data_type == 'uint64':
            return decoder.decode_64bit_uint()
        elif data_type == 'float32':
            return decoder.decode_32bit_float()
        elif data_type == 'float64':
            return decoder.decode_64bit_float()
        else:
            raise ModbusError(f"Unsupported data type: {data_type}")
    
    def _encode_value(self, value, data_type):
        """Encode a value to register format based on data type"""
        builder = BinaryPayloadBuilder(
            byteorder=Endian.BIG,
            wordorder=Endian.LITTLE  # Most Modbus devices use this order
        )
        
        # Handle string data type
        if data_type.startswith('string['):
            try:
                string_length = int(data_type.split('[')[1].split(']')[0])
                # Truncate or pad the string to the specified length
                value_str = str(value)
                if len(value_str) > string_length:
                    value_str = value_str[:string_length]
                builder.add_string(value_str.encode('utf-8'))
            except (IndexError, ValueError):
                raise ModbusError(f"Invalid string data type format: {data_type}")
        
        # Handle other data types
        elif data_type == 'bool':
            builder.add_bits([bool(value)])
        elif data_type == 'int16':
            builder.add_16bit_int(int(value))
        elif data_type == 'uint16':
            builder.add_16bit_uint(int(value))
        elif data_type == 'int32':
            builder.add_32bit_int(int(value))
        elif data_type == 'uint32':
            builder.add_32bit_uint(int(value))
        elif data_type == 'int64':
            builder.add_64bit_int(int(value))
        elif data_type == 'uint64':
            builder.add_64bit_uint(int(value))
        elif data_type == 'float32':
            builder.add_32bit_float(float(value))
        elif data_type == 'float64':
            builder.add_64bit_float(float(value))
        else:
            raise ModbusError(f"Unsupported data type: {data_type}")
        
        # Build the registers
        return builder.to_registers()