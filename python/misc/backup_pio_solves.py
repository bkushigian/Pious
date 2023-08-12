#!/usr/bin/env python3

"""
This script automatically detects new or updated .cfr files in a folder and
copies them to a backup folder. It is intended to be used with the 
PIOSolver software, which generates .cfr files as output

The script is intended to be run as a scheduled task in Windows.

By default this will copy files from C:\PioSOLVER\Saves to a D:\PioSOLVER\Saves.
"""

import os
from argparse import ArgumentParser
from typing import List, Optional
from ansi.color import fg

COPY_NEW = fg.green("[COPY NEW]")
OFFSET = fg.boldmagenta("[ OFFSET ]")
OVERWRITE = fg.red("[ OVERWRITE ]")
SKIP = fg.yellow("[  SKIP  ]")
SKIP_DIR = fg.boldyellow("[SKIP DIR]")


def skip_dir(dirs_to_skip, dir):
    if dirs_to_skip is None:
        return False
    dir = dir.rstrip("\\")
    for d in dirs_to_skip:
        if dir.startswith(d.rstrip("\\")):
            return True
    return False


def file_passes_extension_filter(fname: str, extensions: Optional[List[str]]):
    """Check if a file should be backed up based on the extension filters.
    If the extension filter is None, all files pass. Otherwise, check to see if
    the file ends with any of the extensions in the filter.

    Args:
        fname (str): _description_
        extensions (_type_): _description_

    Returns:
        _type_: _description_
    """
    if extensions is None:
        return True
    for ext in extensions:
        if fname.endswith(ext):
            return True
    return False


def backup_pio_solves(
    source,
    backup_location,
    extensions=None,
    overwrite_with_newer=False,
    trial_run=False,
    verbose=False,
    skip=None,
):
    """Recursively backup all .cfr files in source to backup_location, creating
    any directories as needed.

    This function assumes that the backup_location already exists, and will
    raise an exception if it does not.

    Args:
        source (str): the source file location
        backup_location (str): the destination location
        overwrite_with_newer (bool, optional): optionally overwrite modified files. Defaults to False.
        trial_run (bool, optional): Do a trial run without actually modifying disk. Defaults to True.
    """

    num_copied, num_skipped, num_overwritten = 0, 0, 0

    if skip is None:
        skip = []

    if not os.path.exists(backup_location):
        raise FileNotFoundError(backup_location)

    for root, dirs, files in os.walk(source):
        # We want to preserve the directory structure of source. In each
        # directory we visit we need to know the offset from the source so that
        # we can copy the files to the correct backup location
        #
        # Break path into three segments:
        # C:\D\PioSOLVER\Saves\6max\3betPot\AsKsQs.cfr
        # |------------------| |----------| |--------|
        #        source          offset        file
        offset = root.replace(source, "").lstrip("\\")
        if verbose:
            print(f"{OFFSET} {offset}")
        if os.path.join(source, offset).rstrip("\\") != root:
            raise Exception(
                f"'root/offset' != source: '{os.path.join(root, offset)}' != '{source}'"
            )

        if skip_dir(skip, offset):
            print(f"{SKIP_DIR} Skipping directory {root}")
            continue

        if not os.path.exists(os.path.join(backup_location, offset)):
            if verbose:
                print(f"Creating {os.path.join(backup_location, offset)}")
            os.makedirs(os.path.join(backup_location, offset))

        for fname in files:
            if file_passes_extension_filter(fname, extensions=extensions):
                source_file = os.path.join(root, fname)
                file_offset_from_source = os.path.join(offset, fname)
                backup_file = os.path.join(backup_location, file_offset_from_source)
                if not os.path.exists(backup_file):
                    num_copied += 1
                    if trial_run:
                        print(f"{COPY_NEW} {source_file} => {backup_file} (trial run)")
                    else:
                        print(f"{COPY_NEW} {source_file} => {backup_file}")
                        os.system(f"copy {source_file} {backup_file}")
                elif overwrite_with_newer:
                    source_mtime = os.path.getmtime(source_file)
                    backup_mtime = os.path.getmtime(backup_file)
                    if source_mtime > backup_mtime:
                        num_overwritten += 1
                        if trial_run:
                            print(
                                f"{OVERWRITE} {source_file} => {backup_file} (trial run)"
                            )
                            pass
                        else:
                            print(f"{OVERWRITE} {source_file} => {backup_file}")
                            # os.system(f"copy {source_file} {backup_file}")
                    else:
                        num_skipped += 1
                        if verbose:
                            print(f"{SKIP} {source_file} => {backup_file} (up to date)")
                else:
                    num_skipped += 1
                    if verbose:
                        print(f"{SKIP} {source_file} => {backup_file} (up to date)")
    return num_copied, num_skipped, num_overwritten


def main():
    parser = ArgumentParser()
    parser.add_argument(
        "--backup_location",
        default=r"D:\PioSOLVER\Saves",
        help="Location to backup files to",
    )
    parser.add_argument(
        "--source",
        help="Source folder to check for new files",
        default=r"C:\PioSOLVER\Saves",
    )
    parser.add_argument(
        "--create_backup",
        action="store_true",
        help="Create backup directoryj if it doesn't already exist",
    )
    parser.add_argument(
        "--overwrite_with_newer",
        "-O",
        action="store_true",
        help="Overwrite older cfr files in backup location with newer",
    )
    parser.add_argument(
        "--trial_run",
        "-T",
        action="store_true",
        help="Do a trial run (don't modify disk)",
    )
    parser.add_argument(
        "--offset",
        default=None,
        help="Common offset from the source and backup location to backup (this will ony backup files within this subdirectory)",
    )

    parser.add_argument(
        "--skip",
        nargs="+",
        default=[],
        help="Skip these subdirectories (listed as offsets from the `source` directory)",
    )
    parser.add_argument(
        "--extensions", nargs="+", default=[".cfr"], help="File extensions to backup"
    )

    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    backup_location = args.backup_location
    source = args.source
    if args.offset:
        backup_location = os.path.join(backup_location, args.offset)
        source = os.path.join(source, args.offset)

    if not os.path.exists(backup_location):
        if args.create_backup:
            os.makedirs(backup_location)
        else:
            print(f"Backup location {backup_location} does not exist.")
            print(f"Use --create_backup to attempt create it.")
            raise FileNotFoundError(backup_location)

    # Now, recursively copy all directories and .cfr files in those directories
    # to the backup location

    num_copied, num_skipped, num_overwritten = backup_pio_solves(
        source=source,
        backup_location=backup_location,
        overwrite_with_newer=args.overwrite_with_newer,
        trial_run=args.trial_run,
        skip=args.skip,
        verbose=args.verbose,
    )

    print(fg.cyan("Summary"))
    print(fg.cyan("======="))
    print(fg.green(f"Copied {num_copied} files"))
    print(fg.yellow(f"Skipped {num_skipped} files"))
    print(fg.red(f"Overwrote {num_overwritten} files"))


if __name__ == "__main__":
    main()
