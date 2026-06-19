import serial
import time
import sys

def monitor(port):
    try:
        ser = serial.Serial(port, 115200, timeout=1)
        print(f"Connected to {port}")
        while True:
            line = ser.readline()
            if line:
                print(line.decode('utf-8', errors='replace').strip())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        monitor(sys.argv[1])
    else:
        print("Usage: python monitor.py <port>")
