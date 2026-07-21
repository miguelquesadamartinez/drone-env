from dronekit import connect, VehicleMode, LocationGlobalRelative
import time
import math

print("Conectando al vehiculo...")
vehicle = connect('udp:0.0.0.0:14551', wait_ready=True, heartbeat_timeout=60)

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

def distancia_metros(loc1, loc2):
    """Calcula distancia en metros entre dos coordenadas GPS"""
    dlat = loc2.lat - loc1.lat
    dlon = loc2.lon - loc1.lon
    return math.sqrt((dlat*dlat) + (dlon*dlon)) * 1.113195e5

def ir_a_waypoint(ubicacion, velocidad=5):
    vehicle.simple_goto(ubicacion, airspeed=velocidad)
    while True:
        distancia = distancia_metros(vehicle.location.global_frame, ubicacion)
        print(f" -> Distancia al waypoint: {distancia:.1f}m")
        if distancia < 2:
            print("Waypoint alcanzado!")
            break
        time.sleep(1)

# Obtener posicion actual como referencia
pos_actual = vehicle.location.global_frame

# Definir waypoints relativos a la posicion actual
waypoints = [
    LocationGlobalRelative(pos_actual.lat + 0.0001, pos_actual.lon,          10),
    LocationGlobalRelative(pos_actual.lat + 0.0001, pos_actual.lon + 0.0001, 10),
    LocationGlobalRelative(pos_actual.lat,           pos_actual.lon + 0.0001, 10),
    LocationGlobalRelative(pos_actual.lat,           pos_actual.lon,          10),
]

# Despegar
arm_and_takeoff(10)
time.sleep(2)

# Ejecutar mision
for i, wp in enumerate(waypoints):
    print(f"\nYendo al waypoint {i+1} de {len(waypoints)}...")
    ir_a_waypoint(wp)
    print("Esperando 3 segundos...")
    time.sleep(3)

# Aterrizar
print("\nMision completada! Aterrizando...")
vehicle.mode = VehicleMode("LAND")

while vehicle.location.global_relative_frame.alt > 0.5:
    print(f" -> Altitud: {vehicle.location.global_relative_frame.alt:.1f}m")
    time.sleep(1)

print("Aterrizado!")
vehicle.armed = False
vehicle.close()
