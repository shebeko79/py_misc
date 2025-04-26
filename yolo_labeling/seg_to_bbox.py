import os
import argparse

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

                minx = miny = float('inf')
                maxx = maxy = float('-inf')

                for i in range(1,len(vls),2):
                    x = float(vls[i])
                    y = float(vls[i+1])

                    if x < minx:
                        minx = x
                    elif x > maxx:
                        maxx = x

                    if y < miny:
                        miny = y
                    elif y > maxy:
                        maxy = y

                cx = (minx + maxx) / 2
                cy = (miny + maxy) / 2
                w = maxx - minx
                h = maxy - miny
                s = f"{idx} {cx} {cy} {w} {h}\n"
                content += s

    with open(txt_file, "w") as file:
        file.write(content)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--labelpath', help='Path to data folder containing image and annotation files',
                        required=True)
    args = parser.parse_args()

    label_path = args.labelpath
    process(label_path)
