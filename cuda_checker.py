import subprocess
import sys


def run_command(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    return result.stdout, result.stderr


print("Checking CUDA installation:")
stdout, stderr = run_command("nvcc --version")
if stdout:
    print(stdout)
else:
    print("nvcc not found in PATH. CUDA might not be installed or not in PATH.")
    print("Error:", stderr)

print("\nChecking cuDNN:")
stdout, stderr = run_command("where cudnn64_8.dll")
if stdout:
    print("cuDNN found:", stdout)
else:
    print("cuDNN not found in PATH.")
    print("Error:", stderr)

print("\nPython executable:")
print(sys.executable)

print("\nPython version:")
print(sys.version)
