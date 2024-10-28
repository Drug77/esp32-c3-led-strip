import bluetooth
from ble_advertising import advertising_payload
from micropython import const


IRQ_CENTRAL_CONNECT = const(1)
IRQ_CENTRAL_DISCONNECT = const(2)
IRQ_GATTS_WRITE = const(3)

FLAG_WRITE = const(0x0008)
FLAG_NOTIFY = const(0x0010)

UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
UART_TX = (
    bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"),
    FLAG_NOTIFY,
)
UART_RX = (
    bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"),
    FLAG_WRITE,
)
UART_SERVICE = (
    UART_UUID,
    (UART_TX, UART_RX),
)

# org.bluetooth.characteristic.gap.appearance.xml
ADV_APPEARANCE_GENERIC_COMPUTER = const(128)


class BLEUART:
    def __init__(self, name, queue, led, rxbuf=100):
        self.ble = bluetooth.BLE()
        self.ble.active(True)
        self.ble.irq(self.ble_irq)
        ((self.tx_handle, self.rx_handle),) = self.ble.gatts_register_services((UART_SERVICE,))
        # Increase the size of the rx buffer and enable append mode.
        self.ble.gatts_set_buffer(self.rx_handle, rxbuf, True)
        self.connections = set()
        self.rx_buffer = bytearray()
        self.queue = queue
        # Optionally add services=[UART_UUID], but this is likely to make the payload too large.
        self.payload = advertising_payload(name=name, appearance=ADV_APPEARANCE_GENERIC_COMPUTER)
        self.advertise()
        self.led = led

    def ble_irq(self, event, data):
        if event == IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self.connections.add(conn_handle)
            self.led.on()
        elif event == IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            if conn_handle in self.connections:
                self.connections.remove(conn_handle)
            self.led.off()
            self.advertise()
        elif event == IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            if conn_handle in self.connections and value_handle == self.rx_handle:
                self.rx_buffer += self.ble.gatts_read(self.rx_handle)
            
                ble_msg = self.read().decode("UTF-8").strip()
                try:
                    self.queue.put_sync(ble_msg)
                except IndexError:
                    self.write("Queue full, message discarded.")

    def any(self):
        return len(self.rx_buffer)

    def read(self, sz=None):
        if not sz:
            sz = len(self.rx_buffer)
        result = self.rx_buffer[0:sz]
        self.rx_buffer = self.rx_buffer[sz:]
        return result

    def write(self, data):
        if self.connections:
            for conn_handle in self.connections:
                self.ble.gatts_notify(conn_handle, self.tx_handle, data + "\n")
        else:
            print(data)

    def close(self):
        for conn_handle in self.connections:
            self.ble.gap_disconnect(conn_handle)
        self.connections.clear()
        
    def advertise(self, interval_us=500000):
        self.ble.gap_advertise(interval_us, adv_data=self.payload)
        