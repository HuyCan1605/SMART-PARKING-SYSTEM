#!/bin/bash

# định nghĩa biến PYTHON_SCRIPT và  WATCH_FOLDER
PYTHON_SCRIPT="/home/pi/Documents/Detect_plate/main.py"
PYTHON_SCRIPT2="/home/pi/Documents/Detect_plate/main2.py"
WATCH_FOLDER="/var/www/html/uploads"

while true; do
    # Sử dụng inotifywait để theo dõi thau đổi trong thư mục
    inotifywait -e close_write -q "$WATCH_FOLDER"
    
    # Khi có sự kiện thay đổi, kích hoạt script Python
    /home/pi/Documents/Detect_plate/myenv/bin/python3 "$PYTHON_SCRIPT"
    #/home/pi/Documents/Detect_plate/myenv/bin/python3 "$PYTHON_SCRIPT2"
    sleep 1
done
