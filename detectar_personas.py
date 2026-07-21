import cv2
import numpy as np
import urllib.request
import os

import tensorflow.lite as tflite
    
# Descargar modelo si no existe
MODEL_DIR = os.path.expanduser('~/drone-env/modelos')
os.makedirs(MODEL_DIR, exist_ok=True)

MODELO    = f'{MODEL_DIR}/ssd_mobilenet.tflite'
ETIQUETAS = f'{MODEL_DIR}/etiquetas.txt'

if not os.path.exists(MODELO):
    print("Descargando modelo de deteccion...")
    urllib.request.urlretrieve(
        'https://storage.googleapis.com/download.tensorflow.org/models/tflite/coco_ssd_mobilenet_v1_1.0_quant_2018_06_29.zip',
        f'{MODEL_DIR}/modelo.zip'
    )
    import zipfile
    with zipfile.ZipFile(f'{MODEL_DIR}/modelo.zip', 'r') as z:
        z.extractall(MODEL_DIR)
    print("Modelo descargado!")

if not os.path.exists(ETIQUETAS):
    print("Descargando etiquetas...")
    urllib.request.urlretrieve(
        'https://raw.githubusercontent.com/tensorflow/examples/master/lite/examples/object_detection/raspberry_pi/labels.txt',
        ETIQUETAS
    )

# Cargar etiquetas
with open(ETIQUETAS, 'r') as f:
    etiquetas = [line.strip() for line in f.readlines()]


interpreter = tflite.Interpreter(model_path=MODELO)
interpreter.allocate_tensors()

input_details  = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Tamaño de entrada del modelo
altura_modelo = input_details[0]['shape'][1]
anchura_modelo = input_details[0]['shape'][2]

# Abrir camara
# Con camara USB:
cap = cv2.VideoCapture(0)
# Con camara CSI (cuando llegue tu RPi Camera Module 3):
# cap = cv2.VideoCapture('libcamerasrc ! video/x-raw,width=640,height=480 ! videoconvert ! appsink', cv2.CAP_GSTREAMER)

print("Camara iniciada. Detectando personas...")
print("Pulsa Q para salir")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error leyendo camara")
        break

    # Preprocesar frame para el modelo
    frame_rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_resized = cv2.resize(frame_rgb, (anchura_modelo, altura_modelo))
    input_data   = np.expand_dims(frame_resized, axis=0)

    # Ejecutar deteccion
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()

    # Obtener resultados
    boxes   = interpreter.get_tensor(output_details[0]['index'])[0]
    classes = interpreter.get_tensor(output_details[1]['index'])[0]
    scores  = interpreter.get_tensor(output_details[2]['index'])[0]

    alto, ancho, _ = frame.shape
    personas_detectadas = 0

    for i in range(len(scores)):
        if scores[i] < 0.5:  # Umbral de confianza 50%
            continue

        etiqueta = etiquetas[int(classes[i])]

        # Solo nos interesan las personas (clase 0 en COCO)
        if etiqueta != 'person':
            continue

        personas_detectadas += 1

        # Dibujar caja delimitadora
        ymin = int(boxes[i][0] * alto)
        xmin = int(boxes[i][1] * ancho)
        ymax = int(boxes[i][2] * alto)
        xmax = int(boxes[i][3] * ancho)

        cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
        cv2.putText(frame,
                    f'Persona {scores[i]:.0%}',
                    (xmin, ymin - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (0, 255, 0), 2)

    # Mostrar contador de personas
    cv2.putText(frame,
                f'Personas detectadas: {personas_detectadas}',
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1, (0, 0, 255), 2)

    cv2.imshow('Deteccion de personas', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
