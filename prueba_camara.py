from picamera2 import Picamera2
import cv2

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration())
picam2.start()

print("Camara iniciada. Pulsa Q para salir")

while True:
    frame = picam2.capture_array()
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    cv2.imshow("RPi AI Camera", frame)
    tecla = cv2.waitKey(1) & 0xFF
    if tecla == ord('q') or tecla == ord('Q') or tecla == 27:  # 27 = ESC
        break

picam2.stop()
cv2.destroyAllWindows()
print("Camara cerrada")
