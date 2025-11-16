#!/usr/bin/env python

"""The main entrypoint for the atto-py interpreter"""

from argparse import ArgumentParser
from pathlib import Path

def main():
    argparser = ArgumentParser()
    argparser.add_argument("file", help="The atto-script to run")
    args = argparser.parse_args()
    script = Path(__file__).parent.absolute() / args.file
    print(f"File to run: {script}")


if __name__ == "__main__":
    main()