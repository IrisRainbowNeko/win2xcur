import argparse
import os
import sys
import traceback
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool
from threading import Lock
from typing import BinaryIO

from win2xcur import scale
from win2xcur.parser import open_blob
from win2xcur.writer import to_smart


def main() -> None:
    parser = argparse.ArgumentParser(description='Converts Windows cursors to X11 cursors.')
    parser.add_argument('files', type=argparse.FileType('rb'), nargs='+',
                        help='X11 cursor files to convert (no extension)')
    parser.add_argument('-o', '--output', '--output-dir', default=os.curdir,
                        help='Directory to store converted cursor files.')
    parser.add_argument('-S', '--scale', default=None, type=str,
                        help='Scale the cursor by the specified factor. Multi-scale "[0.125,0.1875,0.25]"')
    parser.add_argument('--size', default=None, type=str,
                        help='Scale the cursor to the specified size. Multi-size "[32,28,64]"')

    args = parser.parse_args()
    print_lock = Lock()

    def process(file: BinaryIO) -> None:
        name = file.name
        blob = file.read()
        try:
            cursor = open_blob(blob)
        except Exception:
            with print_lock:
                print(f'Error occurred while processing {name}:', file=sys.stderr)
                traceback.print_exc()
        else:
            if args.scale:
                scales = eval(args.scale)
                if isinstance(scales, (int, float)):
                    scale.apply_to_frames(cursor.frames, scale=scales)
                else:
                    cursor.frames = scale.apply_to_frames_MS(cursor.frames, scales=scales)
            elif args.size:
                sizes = eval(args.size)
                if isinstance(sizes, (int, float)):
                    scale.apply_to_frames(cursor.frames, size=sizes)
                else:
                    cursor.frames = scale.apply_to_frames_MS(cursor.frames, sizes=sizes)

            ext, result = to_smart(cursor.frames)
            output = os.path.join(args.output, os.path.basename(name) + ext)
            with open(output, 'wb') as f:
                f.write(result)

    with ThreadPool(cpu_count()) as pool:
        pool.map(process, args.files)


if __name__ == '__main__':
    main()
