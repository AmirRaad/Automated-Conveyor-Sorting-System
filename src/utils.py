import cv2
import numpy as np


def detect_hole(img, lower, upper, circle, output=None):
    # Smoothening image using GaussianBlur
    img = cv2.GaussianBlur(img, (11, 11), 0)
    # Convert BGR to HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # Threshold the HSV image to get only black colors
    mask = cv2.inRange(hsv, lower, upper)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)
    # Get all the contours found in the threshold image
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) is not 0:
        status = "Accepted"
        contours = sorted(contours, key=cv2.contourArea, reverse=True)  # finding the contour with maximum area
        contour = contours[0]
        (x, y), r = cv2.minEnclosingCircle(contour)
        while r > circle[2]:
            contours.remove(contours[0])
            contour = contours[0]
            (x, y), r = cv2.minEnclosingCircle(contour)
        if (x - circle[0])**2 + (y - circle[1])**2 < (circle[2])**2 and cv2.contourArea(contour) > 2000:
            status = "Rejected"
            print(cv2.contourArea(contour))
            if output is not None:
                cv2.drawContours(output, [contour], 0, (0, 0, 255), 3)
        return mask, contour, status
    else:
        status = "Accepted"
        return mask, (0, 0), status


def detect_circles(img, output=None):
    img = cv2.medianBlur(img, 5)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # detect circles in the image
    circles = cv2.HoughCircles(img, cv2.HOUGH_GRADIENT, 1.2, 100)
    # ensure at least some circles were found
    if circles is not None:
        # convert the (x, y) coordinates and radius of the circles to integers
        circles = np.round(circles[0, :]).astype("int")
        if output is not None:
            # loop over the (x, y) coordinates and radius of the circles
            (x, y, r) = circles[0]
            # draw the circle in the output image, then draw a rectangle
            # corresponding to the center of the circle
            cv2.circle(output, (x, y), r, (0, 255, 0), 4)
            cv2.rectangle(output, (x - 5, y - 5), (x + 5, y + 5), (0, 255, 0), -1)
        print("Can detected")
        return circles[0]
    else:
        # print("No can detected")
        return None


def detect_hole_v2(img, circle, output=None):
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Set up the detector with default parameters.
    detector = cv2.SimpleBlobDetector_create()
    # Detect blobs.
    keypoints = detector.detect(img)

    if len(keypoints) != 0:
        status = "Accepted"
        keypoints = sorted(keypoints, key=lambda k: k.size, reverse=True)
        hole = keypoints[0]

        if hole.size > 50:
            x = int(hole.pt[0])
            y = int(hole.pt[1])
            r = int(hole.size/3)

            if (x - circle[0])**2 + (y - circle[1])**2 < (circle[2])**2:
                status = "Rejected"
                if output is not None:
                    cv2.circle(output, (x, y), r, (0, 0, 255), -1)
        return hole, status
    else:
        status = "Accepted"
        return 0, status
