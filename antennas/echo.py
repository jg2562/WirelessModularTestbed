#!/usr/bin/python3
import argparse
import os
import selectors

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode')
    parser.add_argument('in_filename')
    parser.add_argument('out_filename')
    args = parser.parse_args()
    mode = args.mode

    if not mode == "rw":
        print("Bad mode for echo")
        exit(1)

    sel = selectors.DefaultSelector()

    try:
        fh_out = os.open(args.in_filename, os.O_WRONLY)
        fh_in = os.open(args.out_filename, os.O_RDONLY)

        sel.register(fh_in, selectors.EVENT_READ)

        while True:
            events = sel.select()
            if events:
                buff = os.read(fh_in, 1024)
                if buff:
                    os.write(fh_out, buff)

    finally:
        sel.unregister(fh_in)
        os.close(fh_in)
        os.close(fh_out)

if __name__ == "__main__":
    main()
