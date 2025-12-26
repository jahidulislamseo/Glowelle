
import os
try:
    with open("test_log.txt", "w") as f:
        f.write("Python is running!")
    print("Test script executed.")
except Exception as e:
    print(f"Error: {e}")
