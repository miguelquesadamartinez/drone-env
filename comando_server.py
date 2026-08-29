"""
Servidor de comandos para controlar el dron desde la app movil.

Mantiene UNA conexion persistente al vehiculo (Pixhawk) y expone
endpoints HTTP que la app llama para despegar, aterrizar, activar
RTL o disparar una parada de emergencia.

SEGURIDAD: mientras no tengas el mando RC como respaldo fisico, este
servidor ES tu unico control del dron. Incluye un watchdog: si la
app deja de mandar /ping durante mas de WATCHDOG_TIMEOUT segundos
mientras el dron esta armado, se dispara RTL automaticamente (igual
que haria un failsafe de radio si perdieras la señal del mando).

La configuracion (DRONE_CONN, DRONE_WATCHDOG_TIMEOUT) se lee del
archivo ".env" en este mismo directorio (copia ".env.example" y
ajustalo). Si no existe ".env", se usan los valores por defecto.

Para probar en tu PC contra SITL, sin hardware:
    pip install fastapi uvicorn dronekit pymavlink python-dotenv
    python comando_server.py

Para correr en la Raspberry con la Pixhawk real por el UART que
cableamos (TELEM2 <-> GPIO14/15), pon en ".env":
    DRONE_CONN=/dev/serial0:921600
"""

import collections
import collections.abc
import os
import threading
import time

# Parche: dronekit usa collections.MutableMapping, que Python quito de
# collections (ahora esta en collections.abc) desde la 3.10. Sin esto,
# el import de dronekit falla en Python 3.10+.
if not hasattr(collections, "MutableMapping"):
    collections.MutableMapping = collections.abc.MutableMapping

from dotenv import load_dotenv
from fastapi import FastAPI
from dronekit import connect, VehicleMode
from pymavlink import mavutil

load_dotenv()

# --- Configuracion ---
DRONE_CONN = os.environ.get("DRONE_CONN", "udp:127.0.0.1:14551")
WATCHDOG_TIMEOUT = float(os.environ.get("DRONE_WATCHDOG_TIMEOUT", "5"))
MAX_ESPERA_SEGUNDOS = 180  # tope de seguridad para no bloquear un hilo para siempre

# Prueba de motores en banco: sube muy poco a poco y nunca pasa de este tope.
NUM_MOTORES = 4
MOTOR_TEST_MAX_PORCENTAJE = 15
MOTOR_TEST_PASO = 1
MOTOR_TEST_INTERVALO_SEGUNDOS = 1.5
MOTOR_TEST_COMANDO_TIMEOUT = 3  # si no se refresca en este tiempo, el motor para solo

# Movimiento en GUIDED: velocidad de avance/retroceso y de giro por defecto.
MOVER_VELOCIDAD = 1.0       # m/s
MOVER_YAW_RATE = 0.5        # rad/s
MOVER_REFRESCO_SEGUNDOS = 0.3  # se reenvia el comando mientras se mantenga pulsado

# --- Estado compartido entre hilos ---
abort_event = threading.Event()
motor_test_stop = threading.Event()
motor_test_running = False
mover_lock = threading.Lock()
mover_id = 0
last_ping = time.time()

print(f"Conectando al vehiculo en {DRONE_CONN} ...")
if DRONE_CONN.startswith("/dev/") and ":" in DRONE_CONN:
    _path, _baud = DRONE_CONN.rsplit(":", 1)
    vehicle = connect(_path, baud=int(_baud), wait_ready=True, heartbeat_timeout=60)
else:
    vehicle = connect(DRONE_CONN, wait_ready=True, heartbeat_timeout=60)
print("Vehiculo conectado.")

app = FastAPI()


def _armar_y_despegar(target_altitude: float) -> None:
    abort_event.clear()
    inicio = time.time()

    while not vehicle.is_armable:
        if abort_event.is_set() or (time.time() - inicio) > MAX_ESPERA_SEGUNDOS:
            print("Despegue cancelado: no se pudo armar a tiempo.")
            return
        time.sleep(1)

    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True
    while not vehicle.armed:
        if abort_event.is_set() or (time.time() - inicio) > MAX_ESPERA_SEGUNDOS:
            print("Despegue cancelado: no se pudo armar a tiempo.")
            return
        time.sleep(1)

    vehicle.simple_takeoff(target_altitude)

    while True:
        if abort_event.is_set():
            print("Despegue interrumpido (parada de emergencia u otra orden).")
            return
        if (time.time() - inicio) > MAX_ESPERA_SEGUNDOS:
            print("Despegue cancelado: tardo demasiado en alcanzar altitud.")
            return
        alt = vehicle.location.global_relative_frame.alt
        if alt >= target_altitude * 0.95:
            print("Altitud objetivo alcanzada.")
            return
        time.sleep(1)


def _aterrizar() -> None:
    vehicle.mode = VehicleMode("LAND")
    inicio = time.time()
    while vehicle.location.global_relative_frame.alt > 0.5:
        if (time.time() - inicio) > MAX_ESPERA_SEGUNDOS:
            print("Aviso: LAND tarda mas de lo esperado, sigue en curso.")
            break
        time.sleep(1)
    vehicle.armed = False


def _rtl() -> None:
    vehicle.mode = VehicleMode("RTL")


def _enviar_velocidad(vx: float, yaw_rate: float) -> None:
    msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0, 0, 0,
        mavutil.mavlink.MAV_FRAME_LOCAL_NED,
        0b0000011111000111,  # usa vx, vy, vz y yaw_rate; ignora posicion, aceleracion y yaw absoluto
        0, 0, 0,
        vx, 0, 0,
        0, 0, 0,
        0, yaw_rate)
    vehicle.send_mavlink(msg)


def _mover_continuo(vx: float, yaw_rate: float, my_id: int) -> None:
    """Reenvia el comando de velocidad mientras siga siendo el movimiento
    activo. En cuanto se pide otro movimiento o parar, se frena solo."""
    while True:
        with mover_lock:
            if mover_id != my_id:
                break
        _enviar_velocidad(vx, yaw_rate)
        time.sleep(MOVER_REFRESCO_SEGUNDOS)
    _enviar_velocidad(0, 0)


def _enviar_motor_test(motor_instance: int, porcentaje: float, duracion: float) -> None:
    msg = vehicle.message_factory.command_long_encode(
        0, 0,
        mavutil.mavlink.MAV_CMD_DO_MOTOR_TEST,
        0,
        motor_instance,
        mavutil.mavlink.MOTOR_TEST_THROTTLE_PERCENT,
        porcentaje,
        duracion,
        0, 0, 0)
    vehicle.send_mavlink(msg)


def _rampa_motores() -> None:
    """Sube el throttle de los NUM_MOTORES motores muy poco a poco hasta
    MOTOR_TEST_MAX_PORCENTAJE y se mantiene ahi hasta que se pida parar."""
    global motor_test_running
    motor_test_running = True
    motor_test_stop.clear()
    porcentaje = 0
    while not motor_test_stop.is_set():
        porcentaje = min(porcentaje + MOTOR_TEST_PASO, MOTOR_TEST_MAX_PORCENTAJE)
        for motor in range(1, NUM_MOTORES + 1):
            _enviar_motor_test(motor, porcentaje, MOTOR_TEST_COMANDO_TIMEOUT)
        print(f"Prueba de motores: {porcentaje}%")
        time.sleep(MOTOR_TEST_INTERVALO_SEGUNDOS)
    for motor in range(1, NUM_MOTORES + 1):
        _enviar_motor_test(motor, 0, 1)
    motor_test_running = False
    print("Prueba de motores: parada.")


def _watchdog() -> None:
    global last_ping
    while True:
        time.sleep(1)
        if vehicle.armed and (time.time() - last_ping) > WATCHDOG_TIMEOUT:
            print(f"WATCHDOG: sin señal de la app hace mas de {WATCHDOG_TIMEOUT}s, forzando RTL")
            _rtl()


threading.Thread(target=_watchdog, daemon=True).start()


@app.post("/ping")
def ping():
    global last_ping
    last_ping = time.time()
    return {"ok": True}


@app.post("/despegar")
def despegar(altitud: float = 1.0):
    threading.Thread(target=_armar_y_despegar, args=(altitud,), daemon=True).start()
    return {"status": "despegando", "altitud": altitud}


@app.post("/aterrizar")
def aterrizar():
    threading.Thread(target=_aterrizar, daemon=True).start()
    return {"status": "aterrizando"}


@app.post("/rtl")
def rtl():
    _rtl()
    return {"status": "rtl"}


@app.post("/mover")
def mover(vx: float = 0.0, yaw_rate: float = 0.0):
    global mover_id
    with mover_lock:
        mover_id += 1
        my_id = mover_id
    threading.Thread(target=_mover_continuo, args=(vx, yaw_rate, my_id), daemon=True).start()
    return {"status": "moviendo", "vx": vx, "yaw_rate": yaw_rate}


@app.post("/parar_movimiento")
def parar_movimiento():
    global mover_id
    with mover_lock:
        mover_id += 1
    return {"status": "movimiento_detenido"}


@app.post("/parada_emergencia")
def parada_emergencia():
    """
    Entra en LAND inmediatamente e interrumpe cualquier despegue o
    maniobra en curso. NO desarma en el aire (eso seria una caida
    libre) - fuerza un aterrizaje controlado ya mismo.
    """
    global mover_id
    abort_event.set()
    motor_test_stop.set()
    with mover_lock:
        mover_id += 1
    vehicle.mode = VehicleMode("LAND")
    return {"status": "parada_emergencia: aterrizando ya"}


@app.post("/motor_test/iniciar")
def motor_test_iniciar():
    if motor_test_running:
        return {"status": "ya_en_marcha"}
    threading.Thread(target=_rampa_motores, daemon=True).start()
    return {"status": "prueba_motores_iniciada"}


@app.post("/motor_test/detener")
def motor_test_detener():
    motor_test_stop.set()
    return {"status": "prueba_motores_detenida"}


@app.get("/telemetria")
def telemetria():
    return {
        "armado": vehicle.armed,
        "modo": vehicle.mode.name,
        "altitud": vehicle.location.global_relative_frame.alt,
        "bateria_voltaje": vehicle.battery.voltage if vehicle.battery else None,
        "gps_fix": vehicle.gps_0.fix_type if vehicle.gps_0 else None,
        "satelites": vehicle.gps_0.satellites_visible if vehicle.gps_0 else None,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
