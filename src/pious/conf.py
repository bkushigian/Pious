from os import path as osp
import tomllib


class PiousConf:
    def __init__(
        self,
        pio_install_directory="C:\\PioSOLVER",
        pio_version_no="3",
        pio_version_type="edge",
        pio_version_suffix=None,
    ):
        self.pio_install_directory = pio_install_directory
        self.pio_version_no = pio_version_no
        self.pio_version_type = pio_version_type
        self.pio_version_suffix = pio_version_suffix
        self.toml = None

        pious_toml = osp.join(osp.expanduser("~"), "pious.toml")

        if osp.exists(pious_toml):
            self.toml = self._read_from_toml(pious_toml)

    def _read_from_toml(self, toml_path):
        with open(toml_path) as f:
            toml = tomllib.loads(f.read())

        pio = toml["pio"]
        if "install_directory" in pio:
            self.pio_install_directory = pio["install_directory"]

        if "pio_version_no" in pio:
            self.pio_version_no = pio["pio_version_no"]

        if "pio_version_type" in pio:
            self.pio_version_type = pio["pio_version_type"]

    def get_pio_viewer_name(self):
        return f"PioViewer{self.pio_version_no}"

    def get_pio_solver_name(self):
        name = f"PioSOLVER{self.pio_version_no}-{self.pio_version_type}"
        if self.pio_version_suffix is not None:
            name = f"{name}-{self.pio_version_suffix}"
        return name


pious_conf = PiousConf()
