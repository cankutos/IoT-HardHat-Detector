# 👷‍♂️ IoT Occupational Safety Access System

## 📌 Project Overview
This project is a smart access control mechanism designed to enforce Occupational Health and Safety (OHS) protocols. It features a hybrid architecture utilizing **Python** for heavy image processing on an Intel processor, and **Arduino (C++)** for real-time hardware control via an **ESP32 microcontroller**. 

The system uses a smartphone camera feed to detect hard hats. Upon positive detection, the Python script communicates with the ESP32, which triggers servo motors to unlock the door. The entire system is integrated with the **Blynk IoT platform** for remote monitoring and entry tracking.

## 🚀 Key Features
* **Computer Vision (Python):** Utilizes OpenCV on an Intel processor to analyze smartphone camera feeds and detect hard hats in real-time.
* **Hardware Control (Arduino/C++):** An ESP32 executes servo motor controls to operate the physical door mechanism based on signals received from the vision system.
* **IoT Dashboard (Blynk):** Provides live entry counting and wireless remote override capabilities.
