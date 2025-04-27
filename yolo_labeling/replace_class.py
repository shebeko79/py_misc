import os
import argparse
import yaml

input_classes = {}
output_classes = {}
add_match = {
    'dining table': 'table',
    'tv': 'monitor'
}

class_map = {}


def process(path):

    for entry in os.scandir(path):
        if not entry.is_file():
            continue

        basename = os.path.basename(entry)
        filename, ext = os.path.splitext(basename)
        if ext.lower() == '.txt':
            txt_file = os.path.join(path, basename)
            process_file(txt_file)


def process_file(txt_file):
    content = ""

    with open(txt_file, "r") as file:
        lines = file.read().splitlines()
        for l in lines:
            vls = l.split()
            if len(vls) > 1:
                idx = int(vls[0])

                if idx in class_map:
                    content += str(class_map[idx])
                    for i in range(1, len(vls)):
                        content += " " + vls[i]
                    content += '\n'

    with open(txt_file, "w") as file:
        file.write(content)


def read_input_yaml(yaml_file_name):
    global input_classes

    with open(yaml_file_name) as stream:
        yaml_content = yaml.safe_load(stream)

    names = yaml_content['names']

    input_classes = {names[index]: index for index in names}


def read_output_yaml(yaml_file_name):
    global output_classes

    with open(yaml_file_name) as stream:
        yaml_content = yaml.safe_load(stream)

    output_classes = {value: index for index, value in enumerate(yaml_content['names'])}


def match_classes():
    global input_classes
    global output_classes
    global class_map

    for out_name in output_classes:
        out_idx = output_classes[out_name]

        if out_name in input_classes:
            in_idx = input_classes[out_name]
            class_map[in_idx] = out_idx
            print(f'{out_name=} {in_idx=} {out_idx=}')

    for add_key in add_match:
        add_val = add_match[add_key]

        if (add_key in input_classes) and (add_val in output_classes):
            in_idx = input_classes[add_key]
            out_idx = output_classes[add_val]
            class_map[in_idx] = out_idx
            print(f'{add_key}:{add_val} {in_idx=} {out_idx=}')

    rev_class_map = {class_map[index]: index for index in class_map}

    for out_name in output_classes:
        out_idx = output_classes[out_name]

        if out_idx not in rev_class_map:
            print(f'Class {out_name} not mapped')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--labelpath', help='Path to data folder containing image and annotation files',
                        required=True)
    parser.add_argument('--input_yaml', help='Path to input yaml',
                        required=True)

    parser.add_argument('--output_yaml', help='Path to output yaml',
                        required=True)

    args = parser.parse_args()

    read_input_yaml(args.input_yaml)
    read_output_yaml(args.output_yaml)
    match_classes()

    process(args.labelpath)
