from argparse import Namespace, _SubParsersAction


def exec_version(args: Namespace):
    import importlib.metadata

    print(importlib.metadata.version("pious"))


def register_command(sub_parsers: _SubParsersAction):
    parser_version = sub_parsers.add_parser(
        "version", description="Print version and exit"
    )
    parser_version.set_defaults(function=exec_version)
