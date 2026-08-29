from dronekit import connect, VehicleMode
import time

print("Conectando al vehiculo...")
vehicle = connect('udp:127.0.0.1:14551', wait_ready=True, heartbeat_timeout=60)

def arm_and_takeoff(target_altitude):
    print("Esperando que sea armable...")
    while not vehicle.is_armable:
        print(f" -> No armable aun. GPS: {vehicle.gps_0.fix_type}")
        time.sleep(2)

    print("Armando motores...")
    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True

    while not vehicle.armed:
        print(" -> Esperando armado...")
        time.sleep(1)

    print(f"Despegando hacia {target_altitude}m...")
    vehicle.simple_takeoff(target_altitude)

    while True:
        alt = vehicle.location.global_relative_frame.alt
        print(f" -> Altitud actual: {alt:.1f}m")
        if alt >= target_altitude * 0.95:
            print("Altitud objetivo alcanzada!")
            break
        time.sleep(1)

arm_and_takeoff(1)

print("Manteniendo posicion 10 segundos...")
time.sleep(10)

print("Aterrizando...")
vehicle.mode = VehicleMode("LAND")

while vehicle.location.global_relative_frame.alt > 0.5:
    print(f" -> Altitud: {vehicle.location.global_relative_frame.alt:.1f}m")
    time.sleep(1)

print("Aterrizado!")
vehicle.armed = False
vehicle.close()
