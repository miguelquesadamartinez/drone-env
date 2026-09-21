"""
Streaming de la camara IA (IMX500) con deteccion de personas en tiempo
real. SUSTITUYE POR COMPLETO al pipeline anterior de rpicam-vid: este
script es ahora la UNICA fuente de video del dron, siempre con los
recuadros de deteccion superpuestos (no hace falta pedirlo, va incluido
en el streaming normal).

Captura fotogramas con Picamera2, corre la deteccion en el propio chip
IMX500 (SSD MobileNetV2 sobre COCO), dibuja un recuadro verde sobre
cada persona detectada (naranja para otros objetos por encima del
umbral) y manda cada fotograma ya anotado a ffmpeg por su entrada
estandar. ffmpeg lo codifica en H264 y lo publica en el mismo
rtsp://localhost:8554/drone que ya recogia MediaMTX antes con
rpicam-vid, asi que la app y MediaMTX no necesitan ningun cambio.

Pensado para correr como servicio systemd (que arranca solo con la
Raspberry, igual que hacia antes "drone-camera.service"), no como un
script que la app lanza bajo demanda - por eso ya no aparece en
SCRIPTS_DISPONIBLES de comando_server.py ni hay boton para el en la
app. Ver mas abajo, al final del fichero, un ejemplo de unidad
systemd para sustituir a la anterior.
"""

import subprocess
import time

import cv2
from picamera2 import Picamera2
from picamera2.devices.imx500 import IMX500, NetworkIntrinsics

# Modelo de deteccion de objetos (SSD MobileNetV2 entrenado en COCO)
# El sufijo _pp indica que el chip ya aplica NMS internamente
MODEL_PATH = "/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk"

PERSON_CLASS = 0   # indice de "person" en COCO (0-indexed en este modelo)
THRESHOLD = 0.3    # confianza minima

ANCHO, ALTO = 640, 480
# FPS de partida para el streaming. La inferencia en el IMX500 en si es
# rapida (corre en su propio chip), pero capturar + dibujar los recuadros
# + codificar con ffmpeg tiene su coste en la RPi - si aguanta mas fluido,
# sube este numero; si se queda corto o se acumula retraso, bajalo.
FPS_OBJETIVO = 10

RTSP_URL = "rtsp://localhost:8554/drone"


def _lanzar_ffmpeg() -> subprocess.Popen:
    """Arranca ffmpeg leyendo fotogramas crudos (BGR) por su entrada
    estandar y publicandolos por RTSP - el mismo destino al que antes
    publicaba rpicam-vid, asi que MediaMTX sigue sirviendo el HLS de
    siempre sin tocar su configuracion."""
    comando = [
        "ffmpeg", "-y",
        "-use_wallclock_as_timestamps", "1",
        "-f", "rawvideo", "-pixel_format", "bgr24",
        "-video_size", f"{ANCHO}x{ALTO}", "-framerate", str(FPS_OBJETIVO),
        "-i", "-",
        "-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency",
        "-pix_fmt", "yuv420p",
        "-f", "rtsp", RTSP_URL,
    ]
    return subprocess.Popen(comando, stdin=subprocess.PIPE)


def main() -> None:
    imx500 = IMX500(MODEL_PATH)
    imx500.network_intrinsics or NetworkIntrinsics()

    picam2 = Picamera2(imx500.camera_num)
    config = picam2.create_preview_configuration(
        main={"size": (ANCHO, ALTO)},
        controls={"FrameRate": 30},
        buffer_count=12,
    )
    picam2.configure(config)

    print("Cargando modelo en el chip IMX500...")
    imx500.show_network_fw_progress_bar()
    picam2.start()

    ffmpeg = _lanzar_ffmpeg()
    print("Deteccion de personas + streaming iniciados (IMX500 -> RTSP -> MediaMTX).")

    intervalo = 1.0 / FPS_OBJETIVO
    try:
        while True:
            inicio = time.time()
            with picam2.captured_request() as request:
                frame = request.make_array("main")
                metadata = request.get_metadata()

            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            h, w = frame.shape[:2]

            outputs = imx500.get_outputs(metadata, add_batch=True)
            if outputs is not None:
                # outputs[0]=boxes(1,N,4)  outputs[1]=scores(1,N)  outputs[2]=classes(1,N)
                # formato de caja normalizado: (y0, x0, y1, x1)
                boxes, scores, classes = outputs[0][0], outputs[1][0], outputs[2][0]
                personas = 0
                for box, score, cls in zip(boxes, scores, classes):
                    score_f = float(score)
                    if score_f < THRESHOLD:
                        continue
                    cls_int = int(round(float(cls)))
                    y0, x0, y1, x1 = [float(v) for v in box]
                    px0, py0 = int(x0 * w), int(y0 * h)
                    px1, py1 = int(x1 * w), int(y1 * h)
                    es_persona = cls_int == PERSON_CLASS
                    color = (0, 255, 0) if es_persona else (0, 165, 255)
                    cv2.rectangle(frame, (px0, py0), (px1, py1), color, 2)
                    cv2.putText(frame, f"cls={cls_int} {score_f:.0%}", (px0, max(0, py0 - 8)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
                    if es_persona:
                        personas += 1
                # Solo se imprime un resumen cuando hay alguna persona -
                # nada de un print por cada candidato de cada fotograma
                # (eso era lo que inundaba la consola antes).
                if personas > 0:
                    print(f"Personas detectadas: {personas}")

            try:
                ffmpeg.stdin.write(frame.tobytes())
            except BrokenPipeError:
                print("ffmpeg se ha cerrado solo, reiniciandolo...")
                ffmpeg = _lanzar_ffmpeg()

            # Si el ciclo (captura + inferencia + dibujo) va mas rapido que
            # el FPS objetivo, esperamos lo que falte; si va mas lento, no
            # esperamos nada (mejor ir un poco por detras que acumular retraso).
            resto = intervalo - (time.time() - inicio)
            if resto > 0:
                time.sleep(resto)
    except KeyboardInterrupt:
        pass
    finally:
        picam2.stop()
        if ffmpeg.stdin:
            ffmpeg.stdin.close()
        ffmpeg.terminate()


if __name__ == "__main__":
    main()


# --- Unidad systemd de ejemplo, para sustituir a "drone-camera.service" ---
#
# [Unit]
# Description=Streaming de camara IA (deteccion de personas) hacia MediaMTX
# After=mediamtx.service
# Requires=mediamtx.service
#
# [Service]
# User=emiki
# WorkingDirectory=/home/emiki/Documents/_Codes/drone-env
# ExecStart=/home/emiki/venv-ardupilot/bin/python3 /home/emiki/Documents/_Codes/drone-env/deteccion_personas_ai.py
# Restart=on-failure
# RestartSec=2
#
# [Install]
# WantedBy=multi-user.target
#
# OJO antes de activarlo (ver aviso en el chat): picamera2 suele
# necesitar los paquetes del sistema (via apt), no siempre funciona
# bien instalado solo dentro de un venv aislado - comprueba que
# "venv-ardupilot" se creo con --system-site-packages, o usa
# directamente /usr/bin/python3 en el ExecStart si no.
