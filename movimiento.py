from dronekit import connect, VehicleMode, LocationGlobalRelative
from pymavlink import mavutil
import time

print("Conectando al vehiculo...")
vehicle = connect('udp:127.0.0.1:14551', wait_ready=True, heartbeat_timeout=60)

def arm_and_takeoff(target_altitude):
    print("Esperando que sea armable...")
    while not vehicle.is_armable:
        time.sleep(1)

    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True

    while not vehicle.armed:
        time.sleep(1)

    vehicle.simple_takeoff(target_altitude)

    while True:
        alt = vehicle.location.global_relative_frame.alt
        print(f" -> Altitud: {alt:.1f}m")
        if alt >= target_altitude * 0.95:
            print("Altitud alcanzada!")
            break
        time.sleep(1)

def mover(vx, vy, vz, duracion):
    """
    vx = velocidad adelante/atras (m/s) positivo=adelante
    vy = velocidad izquierda/derecha (m/s) positivo=derecha
    vz = velocidad arriba/abajo (m/s) positivo=abajo
    duracion = segundos
    """
    msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0, 0, 0,
        mavutil.mavlink.MAV_FRAME_LOCAL_NED,
        0b0000111111000111,
        0, 0, 0,
        vx, vy, vz,
        0, 0, 0,
        0, 0)

    for _ in range(duracion):
        vehicle.send_mavlink(msg)
        time.sleep(1)

# Despegar a 10 metros
arm_and_takeoff(10)
time.sleep(2)

print("Moviendo adelante...")
mover(2, 0, 0, 5)

print("Moviendo atras...")
mover(-2, 0, 0, 5)

print("Moviendo derecha...")
mover(0, 2, 0, 5)

print("Moviendo izquierda...")
mover(0, -2, 0, 5)

print("Subiendo...")
mover(0, 0, -2, 3)

print("Bajando...")
mover(0, 0, 2, 3)

print("Aterrizando...")
vehicle.mode = VehicleMode("LAND")

while vehicle.location.global_relative_frame.alt > 0.5:
    print(f" -> Altitud: {vehicle.location.global_relative_frame.alt:.1f}m")
    time.sleep(1)

print("Aterrizado!")
vehicle.armed = False
vehicle.close()