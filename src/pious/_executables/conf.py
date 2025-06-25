import typer


def conf_cmd():
    """Show configuration information"""
    from pious.conf import pious_conf
    from os import path as osp
    import importlib.metadata

    install_dir = pious_conf.pio_install_directory

    typer.echo(f"Pious Config File Location: {pious_conf.pious_toml}")
    typer.echo(f"Pious Config File Exists: {osp.exists(pious_conf.pious_toml)}")
    typer.echo(f'Pious Version: {importlib.metadata.version("pious")}')
    typer.echo(f"PioSOLVER:")
    typer.echo(
        f"    Install Directory          : {install_dir:32} EXISTS? {osp.exists(install_dir)}"
    )
    typer.echo(f"    PioSOLVER Version          : {pious_conf.pio_version_no}")
    typer.echo(f"    PioSOLVER Version Type     : {pious_conf.pio_version_type}")
