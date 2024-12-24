from argparse import Namespace, _SubParsersAction


def exec_conf(args: Namespace):
    from pious.conf import pious_conf
    from os import path as osp
    import importlib.metadata

    install_dir = pious_conf.pio_install_directory

    print(f'Pious Version              : {importlib.metadata.version("pious")}')
    print(
        f"PioSOLVER Install Directory: `{install_dir}` EXISTS? {osp.exists(install_dir)}"
    )
    print(f"PioSOLVER Version          : {pious_conf.pio_version_no}")
    print(f"PioSOLVER Version Type     : {pious_conf.pio_version_type}")
    print(f"PioSOLVER Version Suffix   : {pious_conf.pio_version_suffix}")
    pio_exec = osp.join(install_dir, pious_conf.get_pio_solver_name()) + ".exe"
    print(f"PioSOLVER Executable       : {pio_exec}   EXISTS? {osp.exists(pio_exec)}")
    pio_viewer = osp.join(install_dir, pious_conf.get_pio_viewer_name()) + ".exe"
    print(
        f"PioVIEWER                  : {pio_viewer}   EXISTS? {osp.exists(pio_viewer)}"
    )


def register_command(sub_parsers: _SubParsersAction):
    parser_version = sub_parsers.add_parser(
        "conf", description="Print version and exit"
    )
    parser_version.set_defaults(function=exec_conf)
