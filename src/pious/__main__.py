from argparse import ArgumentParser, Namespace
from .flops import Flops

PIOUS_DESCRIPTION = """Pious: The PIO Utility Suite

The Pious Library began as a wrapper around PioSOLVER's Universal Poker
Interface (UPI) and has evolved in to a full fledged poker software utility
suite.

"""


def exec_flops(args: Namespace):
    flops = Flops()

    if args.filter is not None:
        flops.filter(args.filter)
    print(flops)
    if args.count:
        print(f'{len(flops)} flops satisfy filter "{args.filter}"')
    if args.file is not None:
        with open(args.file, "w+") as f:
            f.write(str(flops))


parser = ArgumentParser(prog="pious", description="The PioSOLVER Utility Suite")

## DEFINE SUBPARSERS
sub_parsers = parser.add_subparsers(title="commands")

#### FLOPS SUBCOMMAND

parser_flops = sub_parsers.add_parser(
    "flops", description="Utility module for filtering and printing flop subsets"
)
parser_flops.set_defaults(function=exec_flops)

parser_flops.add_argument(
    "filter",
    nargs="?",
    help="Filter flops based on texture, e.g., 'not flush and straight'",
)
parser_flops.add_argument(
    "--count", action="store_true", help="Print number of flops satisfying filter"
)
parser_flops.add_argument("--file", "-f", help="print flops to file")

args = parser.parse_args()
if "function" in args:
    args.function(args)
else:
    parser.print_help()
