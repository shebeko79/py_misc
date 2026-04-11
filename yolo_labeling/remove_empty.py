import os
import argparse

def process(path):

    count = 0

    for entry in os.scandir(path):
        if not entry.is_file():
            continue

        basename = os.path.basename(entry)
        filename, ext = os.path.splitext(basename)
        if ext.lower() == '.txt':
            txt_file = os.path.join(path, basename)
            if os.path.getsize(txt_file) == 0:
                count += 1

    print(f'{count=}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--labelpath', help='Path to data folder containing image and annotation files',
                        required=True)

    args = parser.parse_args()
    process(args.labelpath)
