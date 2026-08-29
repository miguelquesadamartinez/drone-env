# 🚁 Dron con Raspberry Pi 4 + Pixhawk + IA
Guía completa de construcción, configuración y programación.

---

## � Instalación y Ejecución

### Instalación inicial del proyecto

#### 1. Clonar o descargar el proyecto
```bash
# Si tienes en un repositorio git:
git clone <URL-del-repo> ~/drone-env
cd ~/drone-env
```

#### 2. Crear entorno virtual (si no existe)
```bash
python3 -m venv ~/drone-env
source ~/drone-env/bin/activate
```

#### 3. Instalar dependencias
```bash
pip install --upgrade pip
pip install dronekit pymavlink MAVProxy opencv-python
pip install picamera2              # Para Raspberry Pi 4 con cámara
pip install tensorflow             # Para detección con IA
pip install numpy scipy scikit-image
```

#### 4. Configurar permisos (Raspberry Pi)
```bash
# Para acceder a la cámara y puerto serie
sudo usermod -a -G video,dialout $USER
sudo reboot
```

---

### Cómo ejecutar cada programa

#### **Paso previo: Activar el entorno virtual**
Siempre, antes de ejecutar cualquier script, activa el entorno:
```bash
source ~/drone-env/bin/activate
```

---

#### 📡 **telemetria.py** — Recibir datos del dron en tiempo real
Muestra voltaje de batería, altitud, modo de vuelo y estado de armado.

```bash
python3 telemetria.py
```
**Requisitos:** Dron conectado (simulador o Pixhawk real)  
**Salida esperada:** Datos actualizados cada segundo en consola  
**Parar:** Presiona `Ctrl+C`

---

#### 🚁 **despegar.py** — Despegar, sostener y aterrizar
Script simple: despega 1 metro, aguanta 10 segundos y aterriza.

```bash
python3 despegar.py
```
**Requisitos:** 
- Dron armable y en GPS lock
- Conectado a simulador o Pixhawk real
  
**Secuencia:**
1. Arma los motores
2. Sube a 1 metro
3. Sostiene posición 10 segundos
4. Desciende y aterriza
5. Desarma motores

**Parar:** Presiona `Ctrl+C` (aterriza de emergencia)

---

#### 🎯 **mision.py** — Ejecutar misión con waypoints GPS
El dron vuela automáticamente entre varios puntos de ruta.

```bash
python3 mision.py
```
**Requisitos:**
- GPS lock (simulador o real)
- Definir waypoints en el código antes de ejecutar

**Cómo editar waypoints:**
Abre `mision.py` y modifica la lista `waypoints`:
```python
waypoints = [
    LocationGlobalRelative(37.7749, -122.4194, 10),  # lat, lon, alt(m)
    LocationGlobalRelative(37.7750, -122.4195, 15),
    LocationGlobalRelative(37.7751, -122.4196, 20),
]
```

---

#### 🎥 **deteccion_personas_ai.py** — Detectar personas con chip IA (IMX500)
Usa el chip IA de la cámara para detectar personas en **tiempo real**.

```bash
python3 deteccion_personas_ai.py
```
**Requisitos:**
- Raspberry Pi con cámara CSI conectada
- Chip IMX500 (en la cámara o adaptador)
- Modelo SSD MobileNetV2 instalado en `/usr/share/imx500-models/`

**Salida esperada:**
- Ventana de video con rectángulos **verdes** alrededor de personas
- Consola muestra: `Persona detectada con confianza 85%`

**Parar:** Presiona `Q` en la ventana de video

---

#### 📹 **prueba_camara.py** — Probar cámara sin IA
Verifica que la cámara funciona sin usar inteligencia artificial.

```bash
python3 prueba_camara.py
```
**Salida esperada:** Ventana con stream de video en tiempo real  
**Parar:** Presiona `Q`

---

#### 👁️ **detectar_personas.py** — Detectar personas con TensorFlow Lite
Usa modelo de deep learning (SSD MobileNet) para detectar personas.

```bash
# Requiere modelo descargado primero:
# wget -P ~/drone-env/modelos https://...modelo.tflite

python3 detectar_personas.py
```
**Requisitos:**
- Modelo TensorFlow Lite en `~/drone-env/modelos/ssd_mobilenet.tflite`
- Archivo de etiquetas en `~/drone-env/modelos/etiquetas.txt`

---

#### 🚶 **seguir_persona.py** — Dron sigue a una persona detectada
El dron vuela automáticamente siguiendo a una persona en tiempo real.

```bash
python3 seguir_persona.py
```
**Requisitos:**
- Dron armado y listo para volar
- Cámara conectada
- Modelo IA funcionando

**Comportamiento:**
1. Detecta a la persona en el frame
2. Calcula su posición relativa
3. Envía comandos de velocidad al dron
4. Mantiene a la persona en el centro de pantalla

**Parar:** Presiona `Ctrl+C`

---

#### 🎮 **movimiento.py** — Control manual de movimiento
Controla el dron mediante comandos de velocidad (útil para pruebas).

```bash
python3 movimiento.py
```
**Controles típicos** (depende de la implementación):
- Flechas o WASD para direcciones
- Q/E para subir/bajar
- Presiona `X` o `Ctrl+C` para parar

---

### Flujo recomendado de pruebas

1. **Prueba inicial (simulador):**
   ```bash
   # Terminal 1:
   python3 telemetria.py          # Ver datos
   
   # Terminal 2:
   python3 despegar.py             # Despega y aterriza
   ```

2. **Con IA (cámara conectada):**
   ```bash
   # Terminal 1:
   python3 prueba_camara.py        # Verifica cámara
   
   # Terminal 2:
   python3 deteccion_personas_ai.py # Prueba detección
   
   # Terminal 3:
   python3 seguir_persona.py       # Modo de seguimiento
   ```

3. **Misión completa:**
   ```bash
   python3 mision.py                # Ejecuta waypoints
   ```

---

## �📦 Lista de piezas

| Pieza | Detalle | Notas |
|---|---|---|
| Raspberry Pi 4 Model B (4GB) | Cerebro principal | Ya disponible |
| Frame quadcopter | Diseño propio impreso en 3D | PETG/ABS, 450mm diagonal |
| Pixhawk 2.4.8 clone | Controladora de vuelo | Kit con GPS incluido |
| GPS M9N + brújula | Módulo externo | Mejor que M8N |
| 4x Motor brushless ~400KV | Propulsión | GARTT ML4114 400KV |
| 4x ESC 30A (BLHeli_32) | Control de motores | |
| 4x Hélices 10"-11" | 2x CW + 2x CCW | |
| LiPo 4S 5000mAh (14.8V) | Batería principal | Conector XT60 |
| Cargador LiPo B6AC | Carga segura de batería | Obligatorio |
| Matek PDB-XT60 | Distribución de energía | Lleva BEC 5V integrado |
| 3DR Power Module | Alimenta Pixhawk + mide batería | |
| Receptor RC SBUS | FlySky FS-IA10B | |
| Emisora RC | FlySky FS-i10 | |
| RPi Camera Module 3 | Cámara CSI para IA | |
| microSD 32GB+ clase A2 | Sistema operativo RPi | Samsung Endurance |

---

## 🔌 Conexiones físicas

### Raspberry Pi ↔ Pixhawk (UART — MAVLink)
```
Pixhawk TELEM2          Raspberry Pi GPIO
──────────────          ────────────────
TX        ──────────── Pin 10 (RXD / GPIO15)
RX        ──────────── Pin 8  (TXD / GPIO14)
GND       ──────────── Pin 6  (GND)
5V        ──────────── NO conectar
```

### ESCs ↔ Pixhawk (PWM)
```
Pixhawk MAIN OUT 1 → ESC Motor 1 (delantero izquierdo)
Pixhawk MAIN OUT 2 → ESC Motor 2 (delantero derecho)
Pixhawk MAIN OUT 3 → ESC Motor 3 (trasero derecho)
Pixhawk MAIN OUT 4 → ESC Motor 4 (trasero izquierdo)
```

### GPS ↔ Pixhawk
```
GPS M9N → Puerto GPS1 del Pixhawk (conector JST-GH 6 pines)
```

### Receptor RC ↔ Pixhawk
```
FlySky FS-IA10B (SBUS) → Pixhawk RC IN
```

### Alimentación
```
LiPo 4S → PDB (Matek PDB-XT60)
              → 4x ESC (alimentación motores)
              → BEC 5V integrado → Raspberry Pi (Pin 4 +5V / Pin 6 GND)
              → 3DR Power Module → Pixhawk POWER1
```

---

## 💻 Fase 1 — Preparar la Raspberry Pi

### Actualizar el sistema
```bash
sudo apt update && sudo apt upgrade -y
```

### Deshabilitar Bluetooth (libera UART para Pixhawk)
```bash
# Editar /boot/config.txt y añadir al final:
sudo nano /boot/config.txt
# Añadir:
# dtoverlay=disable-bt
# enable_uart=1

# Editar /boot/cmdline.txt y eliminar: console=serial0,115200
sudo nano /boot/cmdline.txt

# Deshabilitar servicio bluetooth
sudo systemctl disable bluetooth
```

### Instalar dependencias
```bash
sudo apt install -y python3-pip python3-dev python3-opencv git
```

### Crear entorno virtual Python
```bash
python3 -m venv ~/drone-env
source ~/drone-env/bin/activate
```

### Instalar librerías del dron
```bash
pip install MAVProxy dronekit pymavlink dronekit-sitl
```

### Reiniciar y verificar UART
```bash
sudo reboot
# Tras reiniciar:
ls /dev/ttyAMA0
# Debe devolver: /dev/ttyAMA0
```

---

## 💻 Fase 2 — Comunicación con el Pixhawk

### Instalar ArduPilot SITL (simulador)
```bash
sudo apt install -y git
cd ~
git clone https://github.com/ArduPilot/ardupilot.git
cd ardupilot
git submodule update --init --recursive
Tools/environment_install/install-prereqs-ubuntu.sh -y

# Compilar
./waf configure --board sitl
./waf copter

# Dependencias adicionales necesarias
pip install pexpect empy==3.3.4
```

### Arrancar el simulador SITL
```bash
source ~/drone-env/bin/activate
cd ~/ardupilot/ArduCopter
python3 ~/ardupilot/Tools/autotest/sim_vehicle.py -v ArduCopter
```

### Script de telemetría (`~/drone-env/telemetria.py`)
```python
from dronekit import connect, VehicleMode
import time

print("Conectando al vehiculo...")
vehicle = connect('tcp:127.0.0.1:5760', wait_ready=True)

print("\n=== DATOS DEL VEHICULO ===")
print(f"Firmware:      {vehicle.version}")
print(f"Modo de vuelo: {vehicle.mode.name}")
print(f"Armado:        {vehicle.armed}")
print(f"Altitud:       {vehicle.location.global_relative_frame.alt}m")
print(f"Bateria:       {vehicle.battery}")
print(f"Es armable:    {vehicle.is_armable}")

print("\n=== ESCUCHANDO DATOS EN TIEMPO REAL ===")
print("Ctrl+C para salir\n")

try:
    while True:
        print(f"Alt: {vehicle.location.global_relative_frame.alt:.1f}m | "
              f"Bat: {vehicle.battery.voltage:.1f}V | "
              f"Modo: {vehicle.mode.name} | "
              f"Armado: {vehicle.armed}")
        time.sleep(1)

except KeyboardInterrupt:
    print("\nCerrando conexion...")
    vehicle.close()
```

### Ejecutar telemetría (en segundo terminal)
```bash
source ~/drone-env/bin/activate
python3 ~/drone-env/telemetria.py
```

### Cuando llegue el Pixhawk real — cambiar línea de conexión
```python
# Cambiar esta línea en todos los scripts:
# vehicle = connect('tcp:127.0.0.1:5760', wait_ready=True)
# Por esta:
vehicle = connect('/dev/ttyAMA0', baud=57600, wait_ready=True)
```

---

## 💻 Fase 3 — Control de vuelo

### Script de armar y despegar (`~/drone-env/despegar.py`)
```python
from dronekit import connect, VehicleMode
import time

vehicle = connect('tcp:127.0.0.1:5760', wait_ready=True)

def arm_and_takeoff(target_altitude):
    print("Esperando que sea armable...")
    while not vehicle.is_armable:
        time.sleep(1)

    print("Armando motores...")
    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True

    while not vehicle.armed:
        time.sleep(1)

    print(f"Despegando hacia {target_altitude}m")
    vehicle.simple_takeoff(target_altitude)

    while True:
        alt = vehicle.location.global_relative_frame.alt
        print(f"Altitud: {alt:.1f}m")
        if alt >= target_altitude * 0.95:
            print("Altitud alcanzada")
            break
        time.sleep(1)

arm_and_takeoff(5)
time.sleep(10)

print("Aterrizando...")
vehicle.mode = VehicleMode("LAND")
vehicle.close()
```

### Script de movimiento (`~/drone-env/movimiento.py`)
```python
from dronekit import connect, VehicleMode, LocationGlobalRelative
from pymavlink import mavutil
import time

vehicle = connect('tcp:127.0.0.1:5760', wait_ready=True)

def send_ned_velocity(vx, vy, vz, duration):
    msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0, 0, 0,
        mavutil.mavlink.MAV_FRAME_LOCAL_NED,
        0b0000111111000111,
        0, 0, 0,
        vx, vy, vz,
        0, 0, 0,
        0, 0)
    for _ in range(duration):
        vehicle.send_mavlink(msg)
        time.sleep(1)

# Ejemplo: moverse hacia adelante 5 segundos
send_ned_velocity(2, 0, 0, 5)   # adelante
send_ned_velocity(-2, 0, 0, 5)  # atrás
send_ned_velocity(0, 2, 0, 5)   # derecha
send_ned_velocity(0, -2, 0, 5)  # izquierda

vehicle.close()
```

### Script de misión con waypoints (`~/drone-env/mision.py`)
```python
from dronekit import connect, VehicleMode, LocationGlobalRelative
import time

vehicle = connect('tcp:127.0.0.1:5760', wait_ready=True)

waypoints = [
    LocationGlobalRelative(-35.363261, 149.165230, 10),
    LocationGlobalRelative(-35.363500, 149.165500, 10),
    LocationGlobalRelative(-35.364000, 149.165000, 10),
]

vehicle.mode = VehicleMode("GUIDED")
vehicle.armed = True
vehicle.simple_takeoff(10)
time.sleep(5)

for wp in waypoints:
    print(f"Yendo a: {wp.lat}, {wp.lon}")
    vehicle.simple_goto(wp)
    time.sleep(10)

vehicle.mode = VehicleMode("LAND")
vehicle.close()
```

---

## 💻 Fase 4 — Cámara

### Script de captura básica (`~/drone-env/camara.py`)
```python
import cv2

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    cv2.imshow('Drone Camera', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

### Stream de vídeo por WiFi
```bash
# En la RPi:
libcamera-vid -t 0 --inline --listen -o tcp://0.0.0.0:8888

# En el PC para ver el stream:
# gst-launch-1.0 tcpclientsrc host=IP_RPi port=8888 \
#   ! h264parse ! avdec_h264 ! autovideosink
```

---

## 💻 Fase 5 — IA (pendiente de definir objetivo)

```bash
# Instalar TensorFlow Lite
pip install tflite-runtime

# Instalar OpenCV (si no está)
pip install opencv-python
```

---

## 💻 Fase 6 — Automatización y seguridad

### Servicio systemd para MAVProxy (`/etc/systemd/system/drone.service`)
```ini
[Unit]
Description=Drone MAVProxy Bridge
After=network.target

[Service]
ExecStart=mavproxy.py --master=/dev/ttyAMA0 --baudrate 57600 \
          --out udp:127.0.0.1:14550
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable drone.service
sudo systemctl start drone.service
```

### Script de failsafe (`~/drone-env/failsafe.py`)
```python
from dronekit import connect, VehicleMode
import time

vehicle = connect('/dev/ttyAMA0', baud=57600, wait_ready=True)

@vehicle.on_attribute('battery')
def battery_callback(self, attr_name, value):
    if value.voltage < 14.0:  # Ajustar según batería
        print("BATERIA BAJA - Aterrizando...")
        vehicle.mode = VehicleMode("LAND")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    vehicle.close()
```

---

## ⚙️ Configuración Pixhawk en QGroundControl

1. Conectar Pixhawk por USB al PC
2. Flashear firmware ArduPilot (ArduCopter)
3. **Airframe** → Quadrotor X (Generic Quad X)
4. **Sensors** → Calibrar acelerómetro, brújula, radio RC y nivel
5. **Radio** → Asignar canales (throttle, yaw, pitch, roll)
6. **Flight Modes** → Stabilize / AltHold / GUIDED
7. **TELEM2** → Baud 57600 / MAVLink 2

---

## ✅ Orden de pruebas

1. Sin hélices: verificar giro correcto de motores
2. Verificar comunicación MAVLink RPi ↔ Pixhawk
3. Armar motores en tierra
4. Vuelo manual con RC en modo Stabilize
5. Probar modo AltHold
6. Probar modo GUIDED con scripts Python
7. Integrar cámara y stream de vídeo
8. Añadir capa de IA

---

## 📡 WiFi — Configuración como Access Point

```bash
sudo apt install hostapd dnsmasq -y

# /etc/hostapd/hostapd.conf
# interface=wlan0
# driver=nl80211
# ssid=Drone-AP
# hw_mode=g
# channel=7
# wpa=2
# wpa_passphrase=clave_segura
# wpa_key_mgmt=WPA-PSK
```

---

*Proyecto en desarrollo — Miguel / JuJu-Miguel*

## 🐛 Solución de problemas conocidos

### DroneKit incompatible con Python 3.13
```bash
sed -i 's/collections.MutableMapping/collections.abc.MutableMapping/g' ~/drone-env/lib/python3.13/site-packages/dronekit/__init__.py
sed -i 's/collections.Mapping/collections.abc.Mapping/g' ~/drone-env/lib/python3.13/site-packages/dronekit/__init__.py
sed -i 's/collections.Callable/collections.abc.Callable/g' ~/drone-env/lib/python3.13/site-packages/dronekit/__init__.py
```

### Módulos faltantes para SITL
```bash
pip install pexpect
pip install empy==3.3.4
pip install future
```

### Arrancar SITL correctamente
```bash
source ~/drone-env/activate
cd ~/ardupilot/ArduCopter
python3 ~/ardupilot/Tools/autotest/sim_vehicle.py -v ArduCopter
```

### Añadir puerto extra para DroneKit
# En la consola de MAVProxy escribir:
output add 127.0.0.1:14551

### Ver puertos abiertos en consola de MAVProx
output

### Conexión correcta de DroneKit al simulador
```python
# Con SITL (puerto UDP):
vehicle = connect('udp:127.0.0.1:14551', wait_ready=True)

# Con Pixhawk real (cuando llegue):
vehicle = connect('/dev/ttyAMA0', baud=57600, wait_ready=True)
```

### Ejecutar script de telemetría
```bash
source ~/drone-env/bin/activate
python3 ~/drone-env/telemetria.py
```


## 📷 Raspberry Pi AI Camera (IMX500)

### Instalación
```bash
sudo apt install -y rpicam-apps
sudo apt install -y python3-picamera2
sudo apt install -y imx500-all
```

### Verificar que la cámara funciona
```bash
rpicam-hello --timeout 0
```

### Ver imagen de la cámara en pantalla
```bash
python3 ~/drone-env/prueba_camara.py
```

### Detección de personas con chip IA integrado
```bash
python3 ~/drone-env/deteccion_personas_ai.py
```

### Notas importantes
- Ejecutar siempre SIN entorno virtual activado (deactivate primero)
- La cámara usa el chip Sony IMX500 con IA integrada
- Los modelos IA están en /usr/share/imx500-models/
- camera_auto_detect=1 debe estar en /boot/firmware/config.txt
