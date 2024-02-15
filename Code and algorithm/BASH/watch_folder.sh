#!/bin/bash

# Difine variables PYTHON_SCRIPT and  WATCH_FOLDER
PYTHON_SCRIPT="/home/pi/Documents/Detect_plate/main.py"
PYTHON_SCRIPT2="/home/pi/Documents/Detect_plate/main2.py"
WATCH_FOLDER="/var/www/html/uploads"

while true; do
    # Using inotifywait to watching the change in folder
    inotifywait -e close_write -q "$WATCH_FOLDER"
    
    # When an event occur, activate script
    /home/pi/Documents/Detect_plate/myenv/bin/python3 "$PYTHON_SCRIPT"
    #/home/pi/Documents/Detect_plate/myenv/bin/python3 "$PYTHON_SCRIPT2"
    sleep 1
done
