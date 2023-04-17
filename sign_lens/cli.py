"""Console script for sign_lens."""
import os
import sys
import argparse

from .sign_lens import SignBipartiteLens, SignLens


def help():
    print("sign_lens")
    print("=" * len("sign_lens"))
    print("A toolkit for analyzing signed networks")


def error(e, message):
    """ print errors
    """
    print("[-] {}: {}".format(e, message))
    sys.exit(0)


def check(args):
    """ Error checking
    """
    if not os.path.exists(args.file):
        error("The file does not exit", 
              "Please input the file you want to analyze")


def options():
    """ Parse arguments
    """
    ap = argparse.ArgumentParser(prog="signlens",
                                 usage="python3 %(prog)s [options]",
                                 description="signlens - A package for analyzing signed graphs.")
    ap.add_argument("-f", "--file", help="The tsv file need to be analyzed")
    ap.add_argument("-t", '--type', help="The signed network type need to be analyzed")

    args = ap.parse_args()
    return args


def main():
    """ Main
    """
    args = options()
    check(args)
    fpath = args.file
    if args.type == 'bipartite':
        model = SignBipartiteLens(fpath)
    else:
        model = SignLens(fpath)
    
    model.report_signed_metrics()


def run_as_command():
    version = ".".join(str(v) for v in sys.version_info[:2])
    if float(version) < 3.6:
        print("[-] signlens requires Python version 3.6+.")
        sys.exit(0)
    main()


if __name__ == '__main__':
    main()
