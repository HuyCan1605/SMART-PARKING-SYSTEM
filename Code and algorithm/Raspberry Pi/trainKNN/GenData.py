# GenData.py

import numpy as np
import cv2
import matplotlib.pyplot as plt
import keyboard

# module level variables ##########################################################################
MIN_CONTOUR_AREA = 40


RESIZED_IMAGE_WIDTH = 20
RESIZED_IMAGE_HEIGHT = 30

###################################################################################################
def main():
    imgTrainingNumbers = cv2.imread("./font_chu3.png")            # read in training numbers image
    #imgTrainingNumbers = cv2.resize(imgTrainingNumbers, dsize = None, fx = 0.5, fy = 0.5)
    clone_img = imgTrainingNumbers.copy()
    imgGray = cv2.cvtColor(imgTrainingNumbers, cv2.COLOR_BGR2GRAY)          # get grayscale image
    imgBlurred = cv2.GaussianBlur(imgGray, (5,5), 0)                        # blur

                                                        # filter image from grayscale to black and white
    imgThresh = cv2.adaptiveThreshold(imgBlurred,                           # input image
                                      255,                                  # make pixels that pass the threshold full white
                                      cv2.ADAPTIVE_THRESH_GAUSSIAN_C,       # use gaussian rather than mean, seems to give better results
                                      cv2.THRESH_BINARY_INV,                # invert so foreground will be white, background will be black
                                      11,                                   # size of a pixel neighborhood used to calculate threshold value
                                      2)                                    # constant subtracted from the mean or weighted mean

    # plt.figure()
    # plt.title("imgThresh")
    # plt.imshow(cv2.cvtColor(imgThresh, cv2.COLOR_RGB2BGR))      # show threshold image for reference
    # plt.show()
    imgThreshCopy = imgThresh.copy()        # make a copy of the thresh image, this in necessary b/c findContours modifies the image

    npaContours, npaHierarchy = cv2.findContours(imgThreshCopy,        # input image, make sure to use a copy since the function will modify this image in the course of finding contours
                                                 cv2.RETR_EXTERNAL,                 # retrieve the outermost contours only
                                                 cv2.CHAIN_APPROX_SIMPLE)           # compress horizontal, vertical, and diagonal segments and leave only their end points

                                # declare empty numpy array, we will use this to write to file later
                                # zero rows, enough cols to hold all image data
    # print(npaContours)
    npaFlattenedImages =  np.empty((0, RESIZED_IMAGE_WIDTH * RESIZED_IMAGE_HEIGHT))
   

    intClassifications = []         # declare empty classifications list, this will be our list of how we are classifying our chars from user input, we will write to file at the end

                                    # possible chars we are interested in are digits 0 through 9, put these in list intValidChars
    intValidChars = [ord('0'), ord('1'), ord('2'), ord('3'), ord('4'), ord('5'), ord('6'), ord('7'), ord('8'), ord('9'),
                     ord('A'), ord('B'), ord('C'), ord('D'), ord('E'), ord('F'), ord('G'), ord('H'), ord('I'), ord('J'),
                     ord('K'), ord('L'), ord('M'), ord('N'), ord('O'), ord('P'), ord('Q'), ord('R'), ord('S'), ord('T'),
                     ord('U'), ord('V'), ord('W'), ord('X'), ord('Y'), ord('Z')] #Là mã ascii của mấy chữ này

    for npaContour in npaContours:                          # for each contour
        clone_img = imgTrainingNumbers.copy()
        if cv2.contourArea(npaContour) > MIN_CONTOUR_AREA:          # if contour is big enough to consider
            [intX, intY, intW, intH] = cv2.boundingRect(npaContour)         # get and break out bounding rect

                                                # draw rectangle around each contour as we ask user for input
            cv2.rectangle(clone_img,           # draw rectangle on original training image
                          (intX, intY),                 # upper left corner
                          (intX+intW,intY+intH),        # lower right corner
                          (0, 0, 255),                  # red
                          3)                            # thickness

            imgROI = imgThresh[intY:intY+intH, intX:intX+intW]                                  # crop char out of threshold image
            imgROIResized = cv2.resize(imgROI, (RESIZED_IMAGE_WIDTH, RESIZED_IMAGE_HEIGHT))     # resize image, this will be more consistent for recognition and storage

            plt.figure()
            plt.subplot(211)
            plt.title("imgROI")# show cropped out char for reference
            plt.imshow(cv2.cvtColor(imgROI, cv2.COLOR_RGB2BGR))      # show threshold image for reference
            plt.subplot(212)
            plt.imshow(cv2.cvtColor(clone_img, cv2.COLOR_RGB2BGR))
            plt.show()  
            # plt.title("imgROIResized")# show resized image for reference
            # plt.imshow(cv2.cvtColor(imgROIResized, cv2.COLOR_RGB2BGR))                    
            # plt.show()  
                

            intChar = keyboard.read_key()                     # get key press
            
            # if intChar == 27:                   # if esc key was pressed
            #     sys.exit()                      # exit program
            if ord(intChar) in intValidChars:      # else if the char is in the list of chars we are looking for . . .
                print(intChar)
                intClassifications.append(ord(intChar))        # append classification char to integer list of chars (we will convert to float later before writing to file)
                #Là file chứa label của tất cả các ảnh mẫu, tổng cộng có 32 x 5 = 160 mẫu.
                npaFlattenedImage = imgROIResized.reshape((1, RESIZED_IMAGE_WIDTH * RESIZED_IMAGE_HEIGHT))  # flatten image to 1d numpy array so we can write to file later
                
                npaFlattenedImages = np.append(npaFlattenedImages, npaFlattenedImage, 0)                    # add current flattened impage numpy array to list of flattened image numpy arrays
                
            # end if
        # end if
    # end for

    fltClassifications = np.array(intClassifications, np.float32)                   # convert classifications list of ints to numpy array of floats
    print(fltClassifications)
    npaClassifications = fltClassifications.reshape((fltClassifications.size, 1))   # flatten numpy array of floats to 1d so we can write to file later
    print(npaClassifications)
    print ("\n\ntraining complete !!\n")

    # Ghi npaClassifications vào cuối tệp classifications.txt
    with open('classifications.txt', 'a') as file:
        np.savetxt(file, npaClassifications)

    # Ghi npaFlattenedImages vào cuối tệp flattened_images.txt
    with open('flattened_images.txt', 'a') as file:
        np.savetxt(file, npaFlattenedImages)


    return

###################################################################################################
if __name__ == "__main__":
    main()
# end if