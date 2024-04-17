import os
import json

# Get the directory of the current file (code_loader.py)
current_dir = os.path.dirname(os.path.abspath(__file__))


def load_code_examples():
    dir_name = "code_examples"
    config_file_name = "code_examples.json"
    return load_code(dir_name, config_file_name)


def load_nodered_flow_examples():
    dir_name = "nodered_flow_examples"
    config_file_name = "nodered_flow_examples.json"
    return load_code(dir_name, config_file_name)


def load_code(dir_name, config_file_name):
    # With code_examples directory as a subdirectory of the current directory
    examples_path = os.path.join(current_dir, dir_name)
    config_path = os.path.join(examples_path, config_file_name)

    with open(config_path, "r") as file:
        examples_config = json.load(file)

    examples_content = {}
    for key, example in examples_config.items():
        try:
            file_path = os.path.join(examples_path, example["filename"])
            with open(file_path, "r") as example_file:
                examples_content[key] = {
                    "headline": example["headline"],
                    "code": example_file.read(),
                }
        except IOError:
            examples_content[key] = {
                "headline": example["headline"],
                "code": "Error loading the example.",
            }

    return examples_content
