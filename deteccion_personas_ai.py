import cv2
import time
from picamera2 import Picamera2
from picamera2.devices.imx500 import IMX500, NetworkIntrinsics

# Modelo de deteccion de objetos (SSD MobileNetV2 entrenado en COCO)
# El sufijo _pp indica que el chip ya aplica NMS internamente
MODEL_PATH = "/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk"

PERSON_CLASS = 0   # indice de "person" en COCO (0-indexed en este modelo)
THRESHOLD = 0.3    # confianza minima

# Inicializar la camara con el chip IA
imx500 = IMX500(MODEL_PATH)
intrinsics = imx500.network_intrinsics or NetworkIntrinsics()

picam2 = Picamera2(imx500.camera_num)

config = picam2.create_preview_configuration(
    main={"size": (640, 480)},
    controls={"FrameRate": 30},
    buffer_count=12
)
picam2.configure(config)

# Esperar a que el modelo se cargue completamente en el chip IMX500
print("Cargando modelo en el chip IMX500...")
imx500.show_network_fw_progress_bar()

picam2.start()

print("Deteccion de personas iniciada con chip IA IMX500")
print("Pulsa Q en la ventana de video para salir")

while True:
    with picam2.captured_request() as request:
        frame = request.make_array("main")
        metadata = request.get_metadata()

    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    h, w = frame.shape[:2]

    outputs = imx500.get_outputs(metadata, add_batch=True)

    if outputs is not None:
        # outputs[0]=boxes(1,N,4)  outputs[1]=scores(1,N)  outputs[2]=classes(1,N)
        # formato de caja normalizado: (y0, x0, y1, x1)
        boxes   = outputs[0][0]
        scores  = outputs[1][0]
        classes = outputs[2][0]

        personas = 0
        for box, score, cls in zip(boxes, scores, classes):
            print(f"JuJú - Box: {box}, Score: {score}, Class: {cls}")
            score_f = float(score)
            cls_int = int(round(float(cls)))
            if score_f < THRESHOLD:
                continue
            y0, x0, y1, x1 = [float(v) for v in box]
            px0, py0 = int(x0 * w), int(y0 * h)
            px1, py1 = int(x1 * w), int(y1 * h)
            es_persona = (cls_int == PERSON_CLASS)
            color = (0, 255, 0) if es_persona else (0, 165, 255)
            cv2.rectangle(frame, (px0, py0), (px1, py1), color, 2)
            cv2.putText(frame, f"cls={cls_int} {score_f:.0%}", (px0, max(0, py0 - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
            if es_persona:
                personas += 1
                print(f"Persona detectada con confianza {score_f:.0%})")
            else:
                print(f"Objeto no-persona detectado: clase {cls_int} con confianza {score_f:.0%})")
                

        if personas > 0:
            print(f"Personas detectadas: {personas}")

    cv2.imshow("Deteccion IA", frame)
    tecla = cv2.waitKey(1) & 0xFF
    if tecla in (ord('q'), ord('Q'), 27):
        break

    time.sleep(1.1)  # pausa de 1.1 segundos entre frames

picam2.stop()
cv2.destroyAllWindows()