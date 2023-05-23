r"""
    Usage: python dirSync.py -s|--source_path <source_path> -d|--destination_path <destination_path>
        -i|--interval <integer> -t <S||M||H||D> -l|--log <log_path>

    S = SECONDS, M = MINUTES, H = HOURS, D = DAYS

    Example for synchronizing every 5 minutes with absolute path:
    $ python dirSync.py -s "C:\Users\MrRobot\Documents\Homework"
    -d "C:\Users\MrRobot\Downloads\Homework" -i 5 -t M
    -l "C:\Program Files\DirSync\logs"
"""

import argparse
import logging
from hashlib import md5
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from os import mkdir, rename, remove, walk, listdir, strerror
from shutil import copytree, copy2, rmtree
from datetime import datetime
from time import sleep
import errno
from sys import exit
from concurrent.futures import ProcessPoolExecutor


class DirSync:
    """
    DirSync(source, destination, logger)

    Synchronize a destination directory with a source directory every 'x' seconds|minutes|hours|days
     while the program runs in the background.
    """

    def __init__(
        self, source_root, destination_root, time_window, log_obj: logging.Logger
    ):
        self.logger = log_obj
        self.source: Path = source_root
        self.destination: Path = destination_root
        # will be assigned values during one_way_sync
        self.destination_hexmap = None
        self.source_hexmap = None
        self.source_tree = None
        self.destination_tree = None
        self.timeframe = time_window

    @staticmethod
    def generate_file_hex(
        target: Path,
        blocksize: int = 8192,
    ) -> str:
        """
        Generate a file's hash digest
        :param target: file absolute path
            source & destination directories
        :param blocksize: Any value as the power of 2. Chunks of 8192 bytes to handle large files
        :return: Cryptographic hash digest
        """
        md5_hash = md5()
        with open(target, "rb") as file:
            while buff := file.read(blocksize):
                md5_hash.update(buff)
        return md5_hash.hexdigest()

    @staticmethod
    def generate_xmap(
        target: Path, logger: logging.Logger
    ) -> tuple[dict[str, list], set[Path]]:
        """
        Acts as a setter for:
            source_hexmap, source_tree,
            destination_hexmap, destination_tree

        Map every file under the target directory to its own
            hex digest & path on the same index level.
        Gather unique root paths.

        :param target: either source path or destination path
        :param logger: auto-rotating instance logger
        :return:
        dict with keys:'root', 'file_name', 'hex', 'flag'
            root[j] = full path on the target directory up to the filename
            common_path[j] = path from common root including the filename;
                the common root being the slice between the target & filename
            full_path[j]
            hex[j] = generated hash digest
            flag[j] = False
                The flag is set to True during diff_hex.
                Necessary in the multiple duplication scenario, to avoid unnecessary CPU load
                  if big files with the same digest are duplicated and|or renamed
            Set of empty & non-empty directories used for obsolete directory removal
        """
        target_tree = set()
        hexmap = {"root": [], "common_path": [], "full_path": [], "hex": [], "flag": []}

        for directory in walk(target):
            # directory[0] = dirname:
            # str, directory[1] = [folder basenames]
            # directory[2]=[filenames]
            common_root = Path(directory[0][len(target.__str__()) + 1:])

            # make a set of all empty and non-empty folders
            target_tree.add(common_root)

            # map only non-empty folders to their children
            for file_name in directory[2]:
                common_path = Path.joinpath(common_root, file_name)
                full_path = Path.joinpath(target, common_path)
                hexmap["common_path"].append(common_path)
                hexmap["root"].append(common_root)
                hexmap["full_path"].append(full_path)
                hexmap["flag"].append(False)

        # calculate cryptographic hash in the same order as the path input
        # enrich the current dictionary with the resulted digest
        with ProcessPoolExecutor() as executor:
            digested = executor.map(DirSync.generate_file_hex, hexmap["full_path"])

        for checksum in digested:
            hexmap["hex"].append(checksum)

        # record & print out the current file-digest mapping
        for index, common_path in enumerate(hexmap["common_path"]):
            logger.info(f"{common_path}\n{hexmap['hex'][index]}\n{120 * '-'}")

        return hexmap, target_tree

    def mirror_source_dir(self):
        """
        Mirror source directories on destination path from the deepest level
        This is a prerequisite for updating destination path files,
          to prevent OSError by non-existing directory.
        """
        for dir_path in self.source_tree:
            next_level = Path("")
            for dirname in dir_path.parts:
                # next_level is built progressively to allow mkdir without error
                next_level = Path.joinpath(next_level, dirname)
                current_path = Path.joinpath(self.destination, next_level)
                if not current_path.exists():
                    mkdir(current_path)
                    self.logger.info(f"Created '{current_path}\\' \n")

    def rm_obsolete_dir(self):
        """
        Remove destination directories that are no longer on source.
        The eligible directories are empty at this stage
        """
        for destination_dir_path in self.destination_tree:
            rmtree_target = Path.joinpath(self.destination, destination_dir_path)
            destination_path_on_source = Path.joinpath(
                self.source, destination_dir_path
            )
            # handle only joined paths that are not the base common root
            if (
                destination_path_on_source != self.source
                and not destination_path_on_source.exists()
                and rmtree_target.exists()
            ):
                rmtree(rmtree_target, ignore_errors=True)
                self.logger.info(f"Removed '{rmtree_target}\\' \n")

    def dump_source_copies(self, ndx_on_src_hexmap: list[int]):
        """
        Method called upon source directory files during duplicate handling scenario
        Source has more duplicate files than the destination
        Copy the source directory duplicates that are not already existing in the destination folder

        :param ndx_on_src_hexmap: the index of each duplicate in the source hexmap
        """
        for ndx in ndx_on_src_hexmap:
            new_path = self.source_hexmap["common_path"][ndx]
            from_path = Path.joinpath(self.source, new_path)
            to_path = Path.joinpath(self.destination, new_path)

            if not to_path.exists():
                copy2(from_path, to_path)
                self.logger.info(f"Copied {to_path}\n")
                self.source_hexmap["flag"][ndx] = True

    def remove_old_copies(self, ndx_on_dst_hexmap: list[int]):
        """
        Remove extra duplicates from destination directory
        This can happen when the sync is broken

        :param ndx_on_dst_hexmap: index values from destination_hexmap
        """
        for ndx in ndx_on_dst_hexmap:
            dst_dup = Path.joinpath(
                self.destination, self.destination_hexmap["common_path"][ndx]
            )

            if dst_dup.exists():
                remove(dst_dup)
                self.destination_hexmap["flag"][ndx] = True
                self.logger.info(f"DELETED extra duplicate {dst_dup}\n")

    def duplicate_pass_check(
        self,
        ndx_on_src_hexmap: list[int],
        ndx_on_dst_hexmap: list[int],
        src_common_list: list[Path],
        dst_common_list: list[Path],
    ):
        """
        Pass the same amount of destination duplicates as on the source directory
        :param ndx_on_src_hexmap: temp list of index values from source_hexmap
        :param ndx_on_dst_hexmap: temp list of index values from destination_hexmap
        :param src_common_list: temp list of common file paths from source_hexmap
        :param dst_common_list: temp list of common file paths from destination_hexmap
        """
        matching_index: [None, int] = None
        for path_index in range(len(dst_common_list)):
            # set iterator to last matching index to prevent skipping dst_common_list items
            path_index = matching_index if matching_index is not None else path_index

            if dst_common_list[path_index] in src_common_list:
                matching_index = path_index
                src_common_item = dst_common_list[path_index]
                ndx_src_common_item = src_common_list.index(src_common_item)

                self.logger.info(
                    f"PASS {Path.joinpath(self.destination, src_common_item)}\n"
                )

                # mark & cleanup handled destination items
                dst_index = ndx_on_dst_hexmap[path_index]
                self.destination_hexmap["flag"][dst_index] = True
                del ndx_on_dst_hexmap[path_index]
                del dst_common_list[path_index]

                # mark & cleanup handled source items
                src_index = ndx_on_src_hexmap[src_common_list.index(src_common_item)]
                self.source_hexmap["flag"][src_index] = True
                del ndx_on_src_hexmap[ndx_src_common_item]
                src_common_list.remove(src_common_item)

    def rename_duplicates(
        self,
        ndx_on_src_hexmap: list[int],
        ndx_on_dst_hexmap: list[int],
        src_common_list: list[Path],
        dst_common_list: list[Path],
    ):
        """
        1 - 1 renaming on same index level for both index & path lists
        :param ndx_on_src_hexmap: temp list containing index values from source_hexmap
        :param ndx_on_dst_hexmap: temp list containing index values from destination_hexmap
        :param src_common_list: temp list containing the common root path from source_hexmap
        :param dst_common_list: temp list containing the common root path from destination_hexmap
        """
        try:
            for dst_index in range(len(dst_common_list)):
                dst_index = 0
                old_path = Path.joinpath(self.destination, dst_common_list[dst_index])
                new_path = Path.joinpath(self.destination, src_common_list[dst_index])

                if old_path.exists():
                    rename(old_path, new_path)
                    self.logger.info(f"\nRENAMED {old_path} to {new_path}\n")

                    # mark & cleanup handled destination items
                    hexmap_index = ndx_on_dst_hexmap[dst_index]
                    self.destination_hexmap["flag"][hexmap_index] = True
                    del ndx_on_dst_hexmap[dst_index]
                    del dst_common_list[dst_index]

                    # mark & cleanup handled source items
                    hexmap_index = ndx_on_src_hexmap[dst_index]
                    self.source_hexmap["flag"][hexmap_index] = True
                    del ndx_on_src_hexmap[dst_index]
                    del src_common_list[dst_index]

        # src_common_list had fewer items, remaining dst_common_list items will be removed next
        except IndexError:
            return

    def handle_duplicates(self):
        """
        Rename or remove extra duplicates on destination path
        Copy new duplicates from source
        :return: action counter for later logging
        """
        for dst_index, dst_hex in enumerate(self.destination_hexmap["hex"]):
            # skip flagged items handled during duplication handling scenario
            # source and\or destination has at least 2 duplicates
            if (
                not self.destination_hexmap["flag"][dst_index]
                and dst_hex in self.source_hexmap["hex"]
                and (
                    self.destination_hexmap["hex"].count(dst_hex) > 1
                    or self.source_hexmap["hex"].count(dst_hex) > 1
                )
            ):
                common_path = self.destination_hexmap["common_path"][dst_index]
                self.logger.info(f"Handling duplicates for '{common_path}'\n")

                # gather the index of each duplicate file on both endpoints
                ndx_on_src_hexmap = [
                    ndx
                    for ndx, v in enumerate(self.source_hexmap["hex"])
                    if v == dst_hex
                ]
                ndx_on_dst_hexmap = [
                    ndx
                    for ndx, v in enumerate(self.destination_hexmap["hex"])
                    if v == dst_hex
                ]
                # gather the common paths of each duplicate file on both endpoints
                src_common_list = [
                    self.source_hexmap["common_path"][x] for x in ndx_on_src_hexmap
                ]
                dst_common_list = [
                    self.destination_hexmap["common_path"][x] for x in ndx_on_dst_hexmap
                ]

                # PASS matching common root
                self.duplicate_pass_check(
                    ndx_on_src_hexmap,
                    ndx_on_dst_hexmap,
                    src_common_list,
                    dst_common_list,
                )

                # RENAME remaining destination files after PASS check
                if len(dst_common_list) != 0 and len(src_common_list) != 0:
                    self.rename_duplicates(
                        ndx_on_src_hexmap,
                        ndx_on_dst_hexmap,
                        src_common_list,
                        dst_common_list,
                    )

                # REMOVE remaining dst common list items
                if len(dst_common_list) != 0 and len(src_common_list) == 0:
                    self.remove_old_copies(ndx_on_dst_hexmap)

                # DUMP remaining source items
                if len(dst_common_list) == 0 and len(src_common_list) != 0:
                    self.dump_source_copies(ndx_on_src_hexmap)

    def handle_unique_match(self):
        """
        Compare each destination file against source
        Set flag to True for each matched or renamed file
        """
        for dst_index, dst_hex in enumerate(self.destination_hexmap["hex"]):
            if (
                not self.destination_hexmap["flag"][dst_index]
                and dst_hex in self.source_hexmap["hex"]
            ):
                common_path = self.destination_hexmap['common_path'][dst_index]
                fpath_on_destination = self.destination_hexmap['full_path'][dst_index]
                src_index = self.source_hexmap["hex"].index(dst_hex)
                self.source_hexmap["flag"][src_index] = True
                self.destination_hexmap["flag"][dst_index] = True

                # destination path matching << PASS
                expected_path_on_source = Path.joinpath(self.source, common_path)
                if expected_path_on_source.exists():
                    self.logger.info(f"PASS {common_path}\n")

                # path not matching << RENAME
                else:
                    new_path = Path.joinpath(
                        self.destination,
                        self.source_hexmap["common_path"][src_index],
                    )
                    rename(fpath_on_destination, new_path)
                    self.logger.info(f"RENAMED {fpath_on_destination} TO {new_path}\n")

    def remove_not_matching(self):
        """
        Remove destination files not matching the source
        """
        for dst_index, dst_hex in enumerate(self.destination_hexmap["hex"]):
            if not self.destination_hexmap["flag"][dst_index]:
                full_path = self.destination_hexmap['full_path'][dst_index]
                remove(self.destination_hexmap["full_path"][dst_index])
                self.destination_hexmap["flag"][dst_index] = True
                self.logger.info(f"DELETED {full_path}\n")

    def full_dump_to_destination(self):
        """
        Dump entire source content to destination
        """
        try:
            copytree(self.source, self.destination, dirs_exist_ok=True)

        except OSError as disk_err:
            if disk_err.errno == errno.ENOSPC:
                self.logger.critical(strerror(disk_err.errno), exc_info=True)
                exit(1)

        # to be monitored for specific exceptions
        except Exception:
            self.logger.error("Error during full dump to destination", exc_info=True)
            exit(2)

    def selective_dump_to_destination(self):
        """
        Dumping remaining non-flagged files and keep permissions
        Potential file conflict handled in the previous stage
        """
        for fpath, flag in zip(
            self.source_hexmap["common_path"],
            self.source_hexmap["flag"],
        ):
            if not flag:
                src = Path.joinpath(self.source, fpath)
                dst = Path.joinpath(self.destination, fpath)

                try:
                    copy2(src, dst)
                    self.logger.info(f"\n{dst}\n")

                except OSError as disk_err:
                    if disk_err.errno == errno.ENOSPC:
                        self.logger.critical(strerror(disk_err.errno), exc_info=True)
                        exit(1)

                except Exception:
                    self.logger.error(
                        "Error caught during selective dump", exc_info=True
                    )
                    exit(2)

    @staticmethod
    def format_log_item(text) -> str:
        """
        Used only for certain log entries under one_way_sync
        :return:
        """
        # '2023-05-17 11:27:44,411 - INFO - ' is 33 char
        formatted = f"{text}\n" f"{(33 + len(text)) * '`'}"
        return formatted

    def one_way_sync(self):
        """
        Encapsulates the main high level logic of the sync actions:
        Either perform full sync or 1 by 1 matching of destination items against source
        """

        # Update initialized
        self.source_hexmap, self.source_tree = DirSync.generate_xmap(
            self.source, self.logger
        )
        self.destination_hexmap, self.destination_tree = DirSync.generate_xmap(
            self.destination, self.logger
        )

        # full dump to destination storage if it is empty and the source is not
        if len(listdir(self.destination)) == 0 and len(listdir(self.source)) != 0:
            self.logger.info("PERFORMING FULL SYNC\n\n")
            self.full_dump_to_destination()

        # parse destination hexmap items 1 by 1
        else:
            # both tree sets have only the common root extracted during hexmap generation
            self.logger.info(DirSync.format_log_item("UPDATING DESTINATION TREE"))
            self.mirror_source_dir()

            # cleanup on destination storage
            self.logger.info(DirSync.format_log_item("FILE CLEANUP"))
            self.handle_duplicates()
            self.handle_unique_match()
            self.remove_not_matching()

            # remove dirs after file cleanup
            self.logger.info(DirSync.format_log_item("REMOVING OBSOLETE DIRECTORIES"))
            self.rm_obsolete_dir()

            # dump left-overs from source
            self.logger.info(DirSync.format_log_item("ADDING NEW CONTENT"))
            self.selective_dump_to_destination()

        return datetime.now()


def validate_arg() -> argparse.Namespace:
    """
    Validate user input according to specifications
    :return: parsed arguments
    """
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-s",
        "--source_path",
        type=Path,
        help="The source directory that needs to be replicated",
    )
    parser.add_argument(
        "-d",
        "--destination_path",
        type=Path,
        help="The destination directory that will replicate the " "source",
    )
    parser.add_argument(
        "-i",
        "--interval",
        type=int,
        help="Number of seconds | minutes | hours | days " "of the next argument",
    )
    parser.add_argument(
        "-t",
        "--time_unit",
        type=str,
        help=(
            "Time unit for interval of the replication job: S for "
            "seconds, M for minutes, H for hours, D for days"
        ),
    )
    parser.add_argument(
        "-l",
        "--log_path",
        type=Path,
        help="The directory where logs will be stored",
    )

    return parser.parse_args()


def validate_log_path(log_path: Path):
    """
    Validate existing log directory path or create a new one if the parent exists
    """
    print(f'Validating log directory: "{log_path}"\n')

    # target log folder may not exist along with the parent
    if not log_path.exists() and not log_path.parent.exists():
        exit(
            f'Directory "{log_path.name}" does not exist, nor the parent "{log_path.parent.name}"\n'
            "This program will now exit, please use an existing directory to store the logs.\n"
        )

    # only the target log folder may not exist
    if log_path.parent.exists() and not log_path.exists():
        print(f"The directory {log_path.name} does not exist, creating it now.\n")
        mkdir(log_path)

    print(f"Saving logs in {log_path.resolve()}\n")


def setup_logging(log_path: Path):
    """
    Return console & rotating file logger
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    log_file = Path.joinpath(log_path, "dirSync.log")

    # console & file handlers
    console_handler = logging.StreamHandler()
    file_handler = TimedRotatingFileHandler(log_file, backupCount=32, when="midnight")

    # attach formatter to handlers
    console_format = logging.Formatter("%(message)s")
    file_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    console_handler.setFormatter(console_format)
    file_handler.setFormatter(file_format)

    # attach handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


if __name__ == "__main__":
    # validate input parameters
    argz = validate_arg()

    if None in argz.__dict__.values():
        print(__doc__)
        exit("Incorrect parameters")

    # create the log directory if the input path does not exist
    argz.log_path = argz.log_path.resolve()
    validate_log_path(argz.log_path)

    # setup logging
    logg = setup_logging(argz.log_path)

    # resolve the time interval
    timeframe = {"S": 1, "M": 60, "H": 3600, "D": 86400}
    interval = argz.interval * timeframe[argz.time_unit.upper()]

    # build object
    dir_sync = DirSync(
        argz.source_path.resolve(), argz.destination_path.resolve(), interval, logg
    )

    while True:
        sync_start_time = datetime.now()
        logg.info("STARTING SYNC\n\n")
        sync_finish_time = dir_sync.one_way_sync()
        logg.info("FINISHED SYNC\n\n%s", 120 * "~")

        # determine last sync duration to cut from the interval sleep time until next sync
        sync_duration = (sync_start_time - sync_finish_time).seconds
        sync_delta = dir_sync.timeframe - sync_duration

        # Sleep for the remaining time interval
        if sync_delta <= 0:
            sleep(dir_sync.timeframe)
        else:
            sleep(sync_delta)
