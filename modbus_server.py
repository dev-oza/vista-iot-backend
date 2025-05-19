from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
import logging

# Configure logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

def setup_server(host="127.0.0.1", port=502):
    """Setup and start a Modbus TCP server for testing"""
    
    # Initialize data blocks with test values
    # Using address space 0-99 for each block type
    hr = ModbusSequentialDataBlock(0, [i for i in range(100)])  # Holding registers
    ir = ModbusSequentialDataBlock(0, [i * 10 for i in range(100)])  # Input registers
    co = ModbusSequentialDataBlock(0, [1] * 100)  # Coils
    di = ModbusSequentialDataBlock(0, [1] * 100)  # Discrete inputs
    
    # Create slave context with all block types
    store = ModbusSlaveContext(
        di=di,  # Discrete inputs
        co=co,  # Coils
        hr=hr,  # Holding registers
        ir=ir   # Input registers
    )
    
    # Create Modbus server context with single slave
    context = ModbusServerContext(slaves=store, single=True)
    
    # Start server
    log.info(f"Starting Modbus TCP server on {host}:{port}")
    StartTcpServer(context=context, address=(host, port))

if __name__ == "__main__":
    setup_server()
