from dronekit import connect, VehicleMode
import time

print("Conectando al vehiculo...")

# Cuando tengas el Pixhawk conectado por UART usa:
# vehicle = connect('/dev/ttyAMA0', baud=57600, wait_ready=True)

# Por ahora para simular sin Pixhawk usa:
vehicle = connect('udp:127.0.0.1:14551', wait_ready=True)

print("Vehiculo conectado!")
print(f"Firmware:       {vehicle.version}")
print(f"Modo de vuelo:  {vehicle.mode.name}")
print(f"Armado:         {vehicle.armed}")
print(f"GPS:            {vehicle.gps_0}")
print(f"Altitud:        {vehicle.location.global_relative_frame.alt}m")
print(f"Bateria:        {vehicle.battery}")
print(f"Es armable:     {vehicle.is_armable}")

# Listener - se ejecuta cada vez que cambia la actitud del dron
@vehicle.on_attribute('attitude')
def attitude_callback(self, attr_name, value):
    print(f"Roll: {value.roll:.2f} | Pitch: {value.pitch:.2f} | Yaw: {value.yaw:.2f}")

print("Escuchando datos... Ctrl+C para salir")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Cerrando conexion...")
    vehicle.close()
