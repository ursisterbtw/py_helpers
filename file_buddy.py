import os
import json


def json_to_txt(input_path, output_path):
    with open(input_path, "r") as json_file:
        data = json.load(json_file)

    with open(output_path, "w") as txt_file:
        txt_file.write(json.dumps(data, indent=2))

    print(f"Converted {input_path} to {output_path}")


def txt_to_json(input_path, output_path):
    with open(input_path, "r") as txt_file:
        data = txt_file.read()

    try:
        json_data = json.loads(data)
        with open(output_path, "w") as json_file:
            json.dump(json_data, json_file, indent=2)
        print(f"Converted {input_path} to {output_path}")
    except json.JSONDecodeError:
        print(f"Error: {input_path} does not contain valid JSON data. Skipping conversion.")


def convert_file(input_path, output_path):
    input_ext = os.path.splitext(input_path)[1].lower()
    output_ext = os.path.splitext(output_path)[1].lower()

    if input_ext == ".json" and output_ext == ".txt":
        json_to_txt(input_path, output_path)
    elif input_ext == ".txt" and output_ext == ".json":
        txt_to_json(input_path, output_path)
    else:
        print(f"Unsupported conversion: {input_ext} to {output_ext}")


def process_directory(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith((".json", ".txt")):
                input_path = os.path.join(root, file)
                output_ext = ".txt" if file.endswith(".json") else ".json"
                output_path = os.path.splitext(input_path)[0] + output_ext
                convert_file(input_path, output_path)


if __name__ == "__main__":
    directory = input("Enter the directory path: ")
    process_directory(directory)
