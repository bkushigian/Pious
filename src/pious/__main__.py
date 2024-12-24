from argparse import ArgumentParser, Namespace

from ._executables.aggregation_viewer import (
    register_command as aggregation_viewer_register_command,
)
from ._executables.aggregate import register_command as aggregate_register_command
from ._executables.flops import register_command as flops_register_command
from ._executables.blockers import register_command as blockers_register_command
from ._executables.lines import register_command as lines_register_command
from ._executables.version import register_command as version_register_command
from ._executables.conf import register_command as conf_register_command

PIOUS_DESCRIPTION = """Pious: The PIO Utility Suite

The Pious Library began as a wrapper around PioSOLVER's Universal Poker
Interface (UPI) and has evolved in to a full fledged poker software utility
suite.

"""


def main():
    parser = ArgumentParser(prog="pious", description="The PioSOLVER Utility Suite")

    ## DEFINE SUBPARSERS
    sub_parsers = parser.add_subparsers(title="commands")

    flops_register_command(sub_parsers)
    aggregation_viewer_register_command(sub_parsers)
    aggregate_register_command(sub_parsers)
    blockers_register_command(sub_parsers)
    lines_register_command(sub_parsers)
    version_register_command(sub_parsers)
    conf_register_command(sub_parsers)

    args = parser.parse_args()
    if "function" in args:
        args.function(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
