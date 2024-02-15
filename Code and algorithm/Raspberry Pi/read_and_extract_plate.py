
import os
import util2
import cv2
import numpy as np
import matplotlib.pyplot as plt
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import pathlib
import paho.mqtt.client as mqtt
import time
import datetime



RED = (0,0,255)
BLUE = (255,0,0)
GREEN =  (0,255,0)


n = 1

Min_char = 0.01
Max_char = 0.09

RESIZED_IMAGE_WIDTH = 20
RESIZED_IMAGE_HEIGHT = 30
LOCAL_CAR_REGISTATION_SYMBOL = ["11","12","14","15","16","17","18","19","20","21","22",
"23","24","25","26","27","28","29","30","31","32","33","34","35","36","37","38","40",
"41","43","47","48","49","50","59","39","60","61","62","63","64","65","66","67","68","69","70","71","72","73","75","76","77","78","79","81","82","83","84","85","86","88","89","90","92","93","94","95","97","98","99","51","52","53","54","55","56","57","58"]

REGISTRATION_SERIES = ["A", "B", "C", "D", "E", "F", "G", "H", "K",
 "L", "M", "N", "P", "S", "T", "U", "V", "X", "Y", "Z", "Q"]


def read_plate_number(img_path):
    ################################# Upload KNN model ######################
    npaClassifications = np.loadtxt("/home/pi/Documents/Detect_plate/classifications.txt", np.float32)
    npaFlattenedImages = np.loadtxt("/home/pi/Documents/Detect_plate/flattened_images.txt", np.float32)
    npaClassifications = npaClassifications.reshape((npaClassifications.size, 1))  # reshape numpy array to 1d, necessary to pass to call to train
    kNearest = cv2.ml.KNearest_create()  # instantiate KNN object
    kNearest.train(npaFlattenedImages, cv2.ml.ROW_SAMPLE, npaClassifications)
    #######################################################################
    
        
    image = cv2.imread(img_path)
    # image = cv2.imread("C:/Users/Admin/Downloads/Image/New folder/50/50 (24).jpg")
    # image = cv2.imread("C:/Users/Admin/Downloads/Image/picture133.jpg")
    img = cv2.resize(image, dsize=(1280, 960))
    imgGrayscaleplate, imgThreshplate = util2.preprocess(img)
    canny_image = cv2.Canny(imgThreshplate, 250, 255)  # Canny Edge
    ################################################################# Preprocess image ##########################################
    plt.figure()
    plt.title("Gray image")
    plt.imshow(cv2.cvtColor(imgGrayscaleplate, cv2.COLOR_BGR2RGB))
    plt.show()
    
    #plt.title("Thresholed img")
    #plt.imshow(cv2.cvtColor(imgThreshplate, cv2.COLOR_BGR2RGB))
    #plt.show()
    #plt.title("Canny img")
    #plt.imshow(cv2.cvtColor(canny_image, cv2.COLOR_BGR2RGB))
    #plt.show()
    

    kernel = np.ones((3, 3), np.uint8)
    dilated_image = cv2.dilate(canny_image, kernel, iterations=1)  # Dilation
    #plt.title("dilated")
    #plt.imshow(cv2.cvtColor(dilated_image, cv2.COLOR_BGR2RGB))
    #plt.show()
    #img_erosion = cv2.erode(dilated_image, kernel, iterations=3) 
    # plt.title("erosion")
    # plt.imshow(cv2.cvtColor(img_erosion, cv2.COLOR_BGR2RGB))
    # plt.show()

 
    ############################### Draw contour and filter out the license plate  ############################################
    contours, hierarchy = cv2.findContours(dilated_image, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

    contours1 = sorted(contours, key=cv2.contourArea, reverse=True)[:3]  # Láº¥y 3 contours cÃ³ diá»‡n tÃ­ch lá»›n nháº¥t
    clone_img2 = np.zeros((canny_image.shape[0],canny_image.shape[1],3), dtype = np.uint8) 
    clone_img = imgGrayscaleplate.copy()
    cv2.drawContours(clone_img2, contours1, -1, (255, 0, 0), 1)  
    #plt.title("Contours")
    #plt.imshow(cv2.cvtColor(clone_img2, cv2.COLOR_BGR2RGB))
    #plt.show()

    screenCnt = []
    wid_img, height_img, _  = img.shape
    S = wid_img * height_img

    clone_img = np.zeros((canny_image.shape[0],canny_image.shape[1],3), dtype = np.uint8) 
    clone_img = img.copy()
    # print(height_img * wid_img)
    for c in contours1:
        peri = cv2.arcLength(c, True)  # TÃ­nh chu vi
        approx = cv2.approxPolyDP(c, 0.09 * peri, True)  
        [x, y, w, h] = cv2.boundingRect(approx.copy())
        #cv2.rectangle(img, (x, y), (x + w, y + h), (RED), 2)
        s = w * h
        
        print(w, h, S/s, w/h)
        # cv2.putText(img, str(len(approx.copy())), (x,y),cv2.FONT_HERSHEY_DUPLEX, 2, (0, 255, 0), 3)
        # cv2.putText(img, str(ratio), (x,y),cv2.FONT_HERSHEY_DUPLEX, 2, (0, 255, 0), 3)
        if (len(approx) == 4):
            screenCnt.append(approx)
            cv2.putText(img, str(len(approx.copy())), (x, y), cv2.FONT_HERSHEY_DUPLEX, 2, (0, 255, 0), 3)
        if s != 0:
                r = S / s
        else:
            r = 1000

        if (w == 0) and (h == 0):
            ratio = 0
        else:
            ratio = float(w)/float(h)
        plate = None
        if r > float(3.45) and r < float(13.3):
            cv2.rectangle(img, (x, y), (x + w, y + h), (BLUE), 2)
            if ratio >= float(1.77) and ratio <=  float (6):
                cv2.rectangle(img, (x, y), (x + w, y + h), (GREEN), 3)
                plate = clone_img[y:y + h, x:x + w]
                break
    
    if plate is None:
        return "", 1
    plt.title("Contours1")
    plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    #plt.show()
    gray_plate= cv2.cvtColor(plate, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray_plate, (5,5), 0)
    binary_image = cv2.adaptiveThreshold(blurred, 255.0, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 199, 5)
    roi = plate
    imgThresh = binary_image
    ########################################## Preprocess plate image #################################################3
    #plt.title("plate")
    #plt.imshow(cv2.cvtColor(roi, cv2.COLOR_BGR2RGB))
    #plt.show()
    #plt.figure()
    #plt.title("high contrast plate")
    #plt.imshow(cv2.cvtColor(imgThresh, cv2.COLOR_BGR2RGB))
    #plt.show()
    roi = cv2.resize(roi, (0, 0), fx=3, fy=3)
    imgThresh = cv2.resize(imgThresh, (0, 0), fx=3, fy=3)
    kerel3 = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    thre_mor = cv2.morphologyEx(imgThresh, cv2.MORPH_DILATE, kerel3)
    #plt.figure()
    #plt.title(str(n + 20))
    #plt.imshow(cv2.cvtColor(thre_mor, cv2.COLOR_BGR2RGB))
    edged = cv2.Canny(thre_mor, 250, 255) 
    #plt.title("edged")
    #plt.imshow(cv2.cvtColor(edged, cv2.COLOR_BGR2RGB))
    #plt.show()
    cont, hier = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)


    ##################### Filter out characters #################
    cv2.drawContours(roi, cont, -1, (BLUE), 3)  
    
    char_x_ind = {}
    char_x = []
    height, width, _ = roi.shape
    roiarea = height * width
  
    for ind, cnt in enumerate(cont):
        (x, y, w, h) = cv2.boundingRect(cont[ind])
        cv2.rectangle(roi, (x, y), (x + w, y + h), (RED), 2)
        ratiochar = w / h
        char_area = w * h
        #print("Area")
        #print(ratiochar, char_area)
        #print("Min, max")
        #print(Min_char * roiarea, Max_char * roiarea)
        #plt.title("contour number")
        #plt.imshow(cv2.cvtColor(roi, cv2.COLOR_BGR2RGB))
        #plt.show()
        if (Min_char * roiarea < char_area < Max_char * roiarea) and (0.25 < ratiochar < 0.9):
            cv2.rectangle(roi, (x, y), (x + w, y + h), (GREEN), 3)
            
            if x in char_x:  # Sá»­ dá»¥ng Ä‘á»ƒ dÃ¹ cho trÃ¹ng x váº«n váº½ Ä‘Æ°á»£c
                x = x + 1
            char_x.append(x)
            char_x_ind[x] = ind
            #print( char_x, ", ", char_x_ind[x], ",", ind)
            

    #plt.figure(2)
    #plt.title("Crop plate image")
    #plt.imshow(cv2.cvtColor(roi, cv2.COLOR_BGR2RGB))
    #plt.show()
    ##########################3######## Character recognition ##########################
    char_x = sorted(char_x)
    strFinalString = ""
    first_line = ""
    second_line = ""
    print(height / width)
    for i in char_x:
        (x, y, w, h) = cv2.boundingRect(cont[char_x_ind[i]])
        cv2.rectangle(roi, (x, y), (x + w, y + h), (RED), 2)
        #plt.title("contour number")
        #plt.imshow(cv2.cvtColor(roi, cv2.COLOR_BGR2RGB))
        #plt.show()
        imgROI = thre_mor[y:y + h, x:x + w]  # Crop the characters

        imgROIResized = cv2.resize(imgROI, (RESIZED_IMAGE_WIDTH, RESIZED_IMAGE_HEIGHT))  # resize image
        npaROIResized = imgROIResized.reshape((1, RESIZED_IMAGE_WIDTH * RESIZED_IMAGE_HEIGHT))

        npaROIResized = np.float32(npaROIResized)
        _, npaResults, neigh_resp, dists = kNearest.findNearest(npaROIResized,k=3)  # call KNN function find_nearest;
        strCurrentChar = str(chr(int(npaResults[0][0])))  # ASCII of characters
        cv2.putText(roi, strCurrentChar, (x, y + 50), cv2.FONT_HERSHEY_DUPLEX, 2, (255, 255, 0), 5)
        
        if 0.4 < height / width < 2.2:
            if (y < height / 3):  # decide 1 or 2-line license plate
                first_line = first_line + strCurrentChar
                #print("first line" , first_line)
            else:
                second_line = second_line + strCurrentChar
                #print("second line" ,second_line)
        elif 0.1 < height / width < 0.5:
            first_line = first_line + strCurrentChar
            #print("first line" , first_line)
        

    print("\n License Plate " + str(n) + " is: " + first_line + " - " + second_line + "\n")
    wrong_plate = 0
    number_plate = first_line + "" + second_line
    if len(number_plate) == 8 or len(number_plate) == 7:
        city_iden = number_plate[0] + "" + number_plate[1]
        car_seri = number_plate[2]
        print(city_iden)
        print(car_seri)
        if len(number_plate) == 8:
            registration_order = number_plate[3:8]
            
        if len(number_plate) == 7:
            registration_order = number_plate[3:7]
        if not(registration_order.isdecimal()):
            wrong_plate = 1
        if city_iden not in LOCAL_CAR_REGISTATION_SYMBOL:
            wrong_plate = 1
        if car_seri not in REGISTRATION_SERIES:
            wrong_plate = 1
    else:
        wrong_plate = 1

        
    plt.figure(2)
    plt.title("read characters image")
    plt.imshow(cv2.cvtColor(roi, cv2.COLOR_BGR2RGB))
    plt.show()
    print(wrong_plate)
    return number_plate, wrong_plate


            
