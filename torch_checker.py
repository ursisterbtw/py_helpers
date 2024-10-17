import os

import torch

print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")
if torch.cuda.is_available():
    print(f"CUDNN version: {torch.backends.cudnn.version()}")
    print(f"Number of GPUs: {torch.cuda.device_count()}")
    print(f"Current GPU: {torch.cuda.get_device_name(torch.cuda.current_device())}")

print("\nEnvironment variables:")
for key, value in os.environ.items():
    if "cuda" in key.lower() or "gpu" in key.lower() or "nvidia" in key.lower():
        print(f"{key}: {value}")

print("\nCUDA library path:")
try:
    print(torch.utils.cpp_extension.CUDA_HOME)
except:
    print("CUDA_HOME not found")

if not torch.cuda.is_available():
    print("\nChecking CUDA libraries:")
    try:
        import ctypes

        ctypes.CDLL("nvcuda.dll")
        print("nvcuda.dll loaded successfully")
    except:
        print("Failed to load nvcuda.dll")

    try:
        ctypes.CDLL("cudart64_110.dll")
        print("cudart64_110.dll loaded successfully")
    except:
        print("Failed to load cudart64_110.dll")
