#!/usr/bin/env python3

"""The main entrypoint for the atto-py interpreter"""

from argparse import ArgumentParser
from pathlib import Path

from src.interpreter import Interpreter

def run_interpreter(script: Path):
    """Runs the interpreter

    Parameters
    ----------
    script : Path
        The path to the script file we want to execute
    """

    try:
        interp = Interpreter()
        interp.exec_file(script)
    except KeyboardInterrupt:
        print("Interupt signal, exiting atto interpreter...")

def main():
    """Main function of our interpreter program"""
    argparser = ArgumentParser()
    argparser.add_argument("file", help="The atto-script to run")
    args = argparser.parse_args()

    # handle other argv options in the future

    script = Path(__file__).parent.absolute() / args.file
    run_interpreter(script)

if __name__ == "__main__":
    main()
