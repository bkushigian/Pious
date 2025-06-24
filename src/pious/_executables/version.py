import typer
import importlib.metadata

app = typer.Typer(help="Print version and exit")


@app.command()
def version():
    """Print version and exit"""
    print(importlib.metadata.version("pious"))


# For backward compatibility during migration
def exec_version(args):
    version()


def register_command(sub_parsers):
    # Legacy argparse registration - can be removed after migration
    parser_conf = sub_parsers.add_parser(
        "version", description="Print version and exit"
    )
    parser_conf.set_defaults(function=exec_version)
