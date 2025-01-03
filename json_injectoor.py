"""
JSON Configuration Injector.

This script allows you to load a JSON configuration file, inject a new command,
and save the updated configuration back to the file.
"""

import json

def load_config(file_path):
    """Load JSON configuration from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: The file {file_path} does not exist.")
        return {}
    except json.JSONDecodeError:
        print(f"Error: The file {file_path} is not a valid JSON.")
        return {}

def save_config(file_path, config):
    """Save JSON configuration to a file."""
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(config, file, indent=4)

def inject_command(config, command_key, command_value):
    """Inject a command into the configuration JSON."""
    config[command_key] = command_value
    return config

def main():
    """Main function to load, inject, and save JSON configuration."""
    config_file = r"PATH/TO/CONFIG/FILE"

    # load the current configuration
    config = load_config(config_file)

    # print the current configuration for reference
    print("Current Configuration:")
    print(json.dumps(config, indent=4))

    if command_key := input(
        "Enter the configuration key to inject (leave blank to skip): "
    ):
        command_value = input("Enter the value for the configuration key: ")

        # inject the command
        config = inject_command(config, command_key, command_value)

        # save the updated configuration back to the file
        save_config(config_file, config)
        print(f"Injected command: {command_key} = {command_value} into {config_file}")
    else:
        print("No key provided, skipping injection.")

if __name__ == "__main__":
    main()
