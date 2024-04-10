import os
import json

# Get the directory of the current file (code_loader.py)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Code examples directory and config file name
code_examples_dir = 'code_examples'
# config_file = 'code_examples.json'


def load_code_examples(config_file='code_examples.json'):
    # Assuming the code_examples directory is a subdirectory of the current directory
    examples_path = os.path.join(current_dir, code_examples_dir)
    config_path = os.path.join(examples_path, config_file)

    with open(config_path, 'r') as file:
        examples_config = json.load(file)

    examples_content = {}
    for key, example in examples_config.items():
        try:
            file_path = os.path.join(examples_path, example['filename'])
            with open(file_path, 'r') as example_file:
                examples_content[key] = {
                    'headline': example['headline'],
                    'code': example_file.read()
                }
        except IOError:
            examples_content[key] = {
                'headline': example['headline'],
                'code': "Error loading the example."
            }

    return examples_content
