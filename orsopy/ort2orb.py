import sys

from .fileio import load_orso, save_nexus


def main():
    for fn in sys.argv[1:]:
        print(fn)
        res = load_orso(fn)
        save_nexus(res, fn.rsplit(".", 1)[0] + ".orb")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Convert ORSO text representation to Nexus.\nUsage: orsopy.py file1.ort file2.ort ...")
    main()
