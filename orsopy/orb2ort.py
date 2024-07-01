import sys

from .fileio import load_nexus, save_orso


def main():
    for fn in sys.argv[1:]:
        print(fn)
        res = load_nexus(fn)
        save_orso(res, fn.rsplit(".", 1)[0] + ".ort")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Convert ORSO text representation to Nexus.\nUsage: orsopy.py file1.orb file2.orb ...")
    main()
