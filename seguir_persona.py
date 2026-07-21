from dronekit import connect, VehicleMode
from pymavlink import mavutil
import cv2
import numpy as np
import tensorflow.lite as tflite
import time
import os

# Configuracion
UMBRAL_CONFIANZA = 0.5
VELOCIDAD_SEGUIMIENTO = 1.5  # m/s
MODEL_DIR = os.path.expanduser('~/drone-env/modelos')
MODELO    = f'{MODEL_DIR}/ssd_mobilenet.tflite'
ETIQUETAS = f'{MODEL_DIR}/etiquetas.txt'

# Cargar modelo y etiquetas
with open(ETIQUETAS, 'r') as f:
    etiquetas = [line.strip() for line in f.readlines()]

interpreter = tflite.Interpreter(model_path=MODELO)
interpreter.allocate_tensors()
input_details  = interpreter.get_input_details()
output_details = interpreter.get_output_details()
altura_modelo  = input_details[0]['shape'][1]
anchura_modelo = input_details[0]['shape'][2]

# Conectar al dron
print("Conectando al vehiculo...")
vehicle = connect('udp:0.0.0.0:14552', wait_ready=True, heartbeat_timeout=60)

def mover(vx, vy, vz=0):
    """Enviar comando de velocidad al dron"""
    msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0, 0, 0,
        mavutil.mavlink.MAV_FRAME_LOCAL_NED,
        0b0000111111000111,
        0, 0, 0,
        vx, vy, vz,
        0, 0, 0,
        0, 0)
    vehicle.send_mavlink(msg)

def detener():
    mover(0, 0, 0)

# Abrir camara
cap = cv2.VideoCapture(0)
ancho_frame = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
alto_frame  = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
centro_x    = ancho_frame // 2
centro_y    = alto_frame  // 2

print("Iniciando seguimiento de personas...")
print("Pulsa Q para aterrizar y salir")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Deteccion
    frame_rgb     = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_resized = cv2.resize(frame_rgb, (anchura_modelo, altura_modelo))
    input_data    = np.expand_dims(frame_resized, axis=0)

    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()

    boxes   = interpreter.get_tensor(output_details[0]['index'])[0]
    classes = interpreter.get_tensor(output_details[1]['index'])[0]
    scores  = interpreter.get_tensor(output_details[2]['index'])[0]

    persona_encontrada = False

    for i in range(len(scores)):
        if scores[i] < UMBRAL_CONFIANZA:
            continue
        if etiquetas[int(classes[i])] != 'person':
            continue

        persona_encontrada = True

        # Centro de la persona detectada
        ymin = int(boxes[i][0] * alto_frame)
        xmin = int(boxes[i][1] * ancho_frame)
        ymax = int(boxes[i][2] * alto_frame)
        xmax = int(boxes[i][3] * ancho_frame)

        persona_cx = (xmin + xmax) // 2
        persona_cy = (ymin + ymax) // 2

        # Calcular error respecto al centro del frame
        error_x = persona_cx - centro_x  # positivo = persona a la derecha
        error_y = persona_cy - centro_y  # positivo = persona abajo

        # Zona muerta — no mover si la persona está cerca del centro
        zona_muerta = 50  # pixeles

        vx, vy = 0, 0

        if abs(error_x) > zona_muerta:
            vy = VELOCIDAD_SEGUIMIENTO if error_x > 0 else -VELOCIDAD_SEGUIMIENTO

        if abs(error_y) > zona_muerta:
            vx = VELOCIDAD_SEGUIMIENTO if error_y > 0 else -VELOCIDAD_SEGUIMIENTO

        mover(vx, vy)

        # Dibujar en pantalla
        cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
        cv2.circle(frame, (persona_cx, persona_cy), 5, (0, 255, 0), -1)
        cv2.putText(frame, f'Siguiendo {scores[i]:.0%}',
                    (xmin, ymin - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        break  # Solo seguir a la primera persona detectada

    if not persona_encontrada:
        detener()
        cv2.putText(frame, 'Buscando persona...',
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # Dibujar centro del frame
    cv2.circle(frame, (centro_x, centro_y), 5, (255, 0, 0), -1)
    cv2.imshow('Seguimiento de persona', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("Aterrizando...")
        detener()
        vehicle.mode = VehicleMode("LAND")
        break

cap.release()
cv2.destroyAllWindows()
vehicle.close()
