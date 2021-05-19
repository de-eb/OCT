import numpy as np
import cv2
from modules.artcam130mi import ArtCam130


if __name__ == "__main__":

    camera = ArtCam130()
    camera.open(exposure_time=10000)

    while True:
        img = camera.capture()

        centre_v = int(img.shape[0]/2)
        centre_h = int(img.shape[1]/2)
        cv2.line(img, (centre_h, 0), (centre_h, img.shape[0]), 255, thickness=1, lineType=cv2.LINE_4)
        cv2.line(img, (0, centre_v), (img.shape[1], centre_v), 255, thickness=1, lineType=cv2.LINE_4)
        cv2.imshow('capture', img)

        key = cv2.waitKey(10)
        if key == 27:  # ESC key to exit
            break
        elif key == ord('s'):  # 'S' key to save image
            cv2.imwrite('data/image.png', img)
            print("The image has been saved.")

    camera.close()
    cv2.destroyAllWindows()
