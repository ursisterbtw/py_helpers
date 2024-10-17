import os
import shutil


def get_cache_dirs():
    home = os.path.expanduser("~")
    cache_dirs = [
        os.path.join(home, ".cache", "huggingface"),
        os.path.join(home, ".cache", "torch"),  # PyTorch cache
        os.path.join(home, ".cache", "pip"),  # pip cache
        os.path.join(home, ".cache", "diffusers"),  # Diffusers cache
        os.path.join(home, ".huggingface"),  # Alternative Hugging Face cache
    ]
    return list(set(cache_dirs))  # Remove duplicates


def print_cache_sizes(cache_dirs):
    for directory in cache_dirs:
        if os.path.exists(directory):
            size = sum(
                os.path.getsize(os.path.join(dirpath, filename)) for dirpath, dirnames, filenames in os.walk(directory) for filename in filenames
            )
            print(f"Cache directory: {directory}")
            print(f"Size: {size / (1024 * 1024):.2f} MB")
        else:
            print(f"Cache directory does not exist: {directory}")
        print()


def clear_cache(cache_dirs):
    for directory in cache_dirs:
        if os.path.exists(directory):
            try:
                shutil.rmtree(directory)
                print(f"Cleared cache directory: {directory}")
            except Exception as e:
                print(f"Error clearing {directory}: {e}")
        else:
            print(f"Cache directory does not exist: {directory}")


if __name__ == "__main__":
    cache_dirs = get_cache_dirs()
    print("Current cache directories and sizes:")
    print_cache_sizes(cache_dirs)

    user_input = input("Do you want to clear these cache directories? (yes/no): ").lower()
    if user_input == "yes":
        clear_cache(cache_dirs)
    else:
        print("Cache clearing aborted.")
