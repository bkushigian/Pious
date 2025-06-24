import importlib.metadata


def version_cmd():
    """Print version and exit"""
    print(importlib.metadata.version("pious"))
