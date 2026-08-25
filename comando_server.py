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

Para probar en tu PC contra SITL, sin hardware:
    pip install fastapi uvicorn dronekit pymavlink
    python comando_server.py

Para correr en la Raspberry con la Pixhawk real por el UART que
cableamos (TELEM2 <-> GPIO14/15), exporta antes de arrancar:
    export DRONE_CONN=/dev/serial0:921600
    python comando_server.py
"""

import os
import threading
import time

from fastapi import FastAPI
from dronekit import connect, VehicleMode

# --- Configuracion ---
DRONE_CONN = os.environ.get("DRONE_CONN", "udp:127.0.0.1:14551")
WATCHDOG_TIMEOUT = float(os.environ.get("DRONE_WATCHDOG_TIMEOUT", "5"))
MAX_ESPERA_SEGUNDOS = 180  # tope de seguridad para no bloquear un hilo para siempre

# --- Estado compartido entre hilos ---
abort_event = threading.Event()
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
def despegar(altitud: float = 5.0):
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


@app.post("/parada_emergencia")
def parada_emergencia():
    """
    Entra en LAND inmediatamente e interrumpe cualquier despegue o
    maniobra en curso. NO desarma en el aire (eso seria una caida
    libre) - fuerza un aterrizaje controlado ya mismo.
    """
    abort_event.set()
    vehicle.mode = VehicleMode("LAND")
    return {"status": "parada_emergencia: aterrizando ya"}


@app.get("/telemetria")
def telemetria():
    return {
        "armado": vehicle.armed,
        "modo": vehicle.mode.name,
        "altitud": vehicle.location.global_relative_frame.alt,
        "bateria_voltaje": vehicle.battery.voltage if vehicle.battery else None,
        "gps_fix": vehicle.gps_0.fix_type if vehicle.gps_0 else None,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
