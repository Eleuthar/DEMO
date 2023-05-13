r"""
    Synchronize a destination directory with a source directory every 'x' seconds\minutes\hours\days
     while the program runs in the background.

    Usage: python dirSync.py -s|--source_path <source_path> -d|--destination_path <destination_path>
        -i|--interval <integer> -t <S||M||H||D> -l|--log <log_path>

    S = SECONDS, M = MINUTES, H = HOURS, D = DAYS

    Example for synchronizing every 5 minutes with absolute path:
    $ python dirSync.py -s "C:\Users\MrRobot\Documents\Homework" -d "C:\Users\MrRobot\Downloads\Homework" -i 5 -t M
    -l "C:\Program Files\DirSync\logs"
"""

import argparse
import sys
from hashlib import md5
from pathlib import Path
from os import mkdir, rename, remove, walk, listdir, strerror
from shutil import copytree, copy2, rmtree
from datetime import datetime
from time import sleep
from typing import IO
import errno


class DirSync:
    timeframe = {"S": 1, "M": 60, "H": 3600, "D": 86400}

    def __init__(
        self,
        source: Path,
        destination: Path,
        interval: int,
        time_unit: str,
        log_path: Path,
    ):
        # resolve relative paths
        self.source = source.resolve()
        self.destination = destination.resolve()
        self.interval = interval * DirSync.timeframe[time_unit.upper()]
        self.log_path = log_path.resolve()

    @staticmethod
    def validate_arg():
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
        input_argz = parser.parse_args()

        if None in input_argz.__dict__.values():
            print(__doc__)
            sys.exit()

        return input_argz

    @staticmethod
    def setup_log_path(log_path: Path):
        """
        Validate existing log directory path or create a new one if the parent exists
        """
        print(f'Validating log directory: "{log_path}"\n')

        # target log folder may not exist along with the parent
        if not log_path.exists() and not log_path.parent.exists():
            print(
                f'Directory "{log_path.name}" does not exist, nor the parent "{log_path.parent.name}"\n'
                "This program will now exit, please use an existing directory to store the logs.\n"
            )
            sys.exit()

        # only the target log folder may not exist
        if log_path.parent.exists() and not log_path.exists():
            print(f"The directory {log_path.name} does not exist, creating it now.\n")
            mkdir(log_path)

        print(f"Saving logs in {log_path.resolve()}\n")

    @staticmethod
    def new_log_file(log_path: Path, now: datetime) -> IO:
        """
        Return a new file formatted like: dirSync_2023-04-18.txt
        """
        ymd_now = now.strftime("%Y-%m-%d")
        log_name = f"dirSync_{ymd_now}.txt"
        full_log_path = Path.joinpath(log_path, log_name)
        return open(full_log_path, "a", encoding="UTF-8")

    @staticmethod
    def log_it(logger: IO, log_item: str):
        print(log_item)
        logger.write(log_item)

    @staticmethod
    def generate_file_hex(
        target: Path,
        common_root: Path,
        filename: str,
        blocksize: int = 8192,
    ) -> str:
        """
        Generate a file's hash digest
        :param target: either source or destination path from the -s or -d argument
        :param common_root: the same path that should be ultimately reflected on both source & destination directories
        :param filename: File's basename
        :param blocksize: Any value as the power of 2. Chunks of 8192 bytes to handle large files
        :return: Cryptographic hash digest
        """
        hh = md5()
        with open(Path.joinpath(target, common_root, filename), "rb") as f:
            while buff := f.read(blocksize):
                hh.update(buff)
        return hh.hexdigest()

    @staticmethod
    def generate_hexmap(target: Path, logger: IO) -> tuple[dict[str, list], set[Path]]:
        """
        Map every single filename under the target directory to its own hex digest & path on the same index level.
        Gather unique root paths.
        :param target: either source path or destination path
        :param logger: current date auto-rotating log file
        :return:
            dict with keys:'root', 'fname', 'hex', 'flag'
                root[j] = full path of the parent up to the common root
                fname[j] = file basename
                hex[j] = generated hash digest
                flag[j] = None
                   but later updated to 'Z' during comparison of source & destination within diff_hex method.
                   The flag is necessary in the multiple duplication scenario, if many big files with the same digest
                   are duplicated(same or new name) intentionally on source directory.
                   Using this flag will avoid unnecessary CPU workload for deleting then later copying the same file
                   on another destination location

            Set of empty & non-empty directories that will be used for the removal of obsolete directories
        """
        target_tree = set()
        hexmap: dict[str, list] = {"root": [], "fname": [], "hex": [], "flag": []}
        DirSync.log_it(logger, f"\n\n\n\nHEXMAP for base root '{target}'\n{120 * '-'}")
        for directory in walk(target):
            # directory[0] = dirname: str, directory[1] = [folder basenames], directory[2]=[filenames]
            common_root = Path(directory[0][len(target.__str__()) + 1:])
            # make a set of all empty and non-empty folders
            target_tree.add(common_root)
            # map only non-empty folders to their children
            for fname in directory[2]:
                hexmap["root"].append(common_root)
                hexmap["fname"].append(Path(fname))
                hx = DirSync.generate_file_hex(target, common_root, fname)
                hexmap["hex"].append(hx)
                hexmap["flag"].append(None)

                DirSync.log_it(logger, f"\n{Path.joinpath(common_root, fname)}")
                DirSync.log_it(logger, f"\n{hx}")
                DirSync.log_it(logger, f"\n{120 * '-'}")
        return hexmap, target_tree

    def mirror_source_dir(self, source_tree: set[Path], logger: IO):
        """
        Mirror source directories on destination path from the deepest directory level
        This is a prerequisite for updating destination path files, to prevent OSError by non-existing directory.
        :param source_tree: The common_root path list to be traversed
        :param logger: current date auto-rotating log file
        :return: action counter for later logging
        """
        for dirpath in source_tree:
            next_level = Path("")
            for dirname in dirpath.parts:
                # next_level is built progressively to allow mkdir without error
                next_level = Path.joinpath(next_level, dirname)
                current_path = Path.joinpath(self.destination, next_level)
                if not current_path.exists():
                    mkdir(current_path)
                    DirSync.log_it(logger, f"\nCreated '{current_path}\\' \n")

    def rm_obsolete_dir(self, destination_tree: set[Path], logger: IO):
        """
        Remove destination directories that are no longer on source.
        The eligible directories are empty at this stage
        :param destination_tree: The common_root path list to be traversed
        :param logger: current date auto-rotating log file
        :return: action counter for later logging
        """
        for destination_dirpath in destination_tree:
            rmtree_target = Path.joinpath(self.destination, destination_dirpath)
            destination_path_on_source = Path.joinpath(self.source, destination_dirpath)
            # handle only joined paths that are not the base common root
            if (
                destination_path_on_source != self.source
                and not destination_path_on_source.exists()
                and rmtree_target.exists()
            ):
                rmtree(rmtree_target, ignore_errors=True)
                DirSync.log_it(logger, f"\nRemoved tree of '{rmtree_target}\\' \n")

    def dump_source_copies(
        self, ndx_on_src_hexmap: list[int], source_hexmap: dict[str, list], logger: IO
    ):
        for ndx in ndx_on_src_hexmap:
            new_path = Path.joinpath(
                source_hexmap["root"][ndx], source_hexmap["fname"][ndx]
            )
            from_path = Path.joinpath(self.source, new_path)
            to_path = Path.joinpath(self.destination, new_path)

            if not to_path.exists():
                copy2(from_path, to_path)
                DirSync.log_it(logger, f"Copied {to_path}\n")
                source_hexmap["flag"][ndx] = "Z"

    def remove_old_copies(
        self,
        ndx_on_dst_hexmap: list[int],
        destination_hexmap: dict[str, list],
        logger: IO,
    ):
        for ndx in ndx_on_dst_hexmap:
            dst_dup = Path.joinpath(
                self.destination,
                destination_hexmap["root"][ndx],
                destination_hexmap["fname"][ndx],
            )
            if dst_dup.exists():
                remove(dst_dup)
                destination_hexmap["flag"][ndx] = "Z"
                DirSync.log_it(logger, f"\nDELETED extra duplicate {dst_dup}\n")

    def duplicate_pass_check(
        self,
        ndx_on_src_hexmap: list[int],
        ndx_on_dst_hexmap: list[int],
        src_common_list: list[Path],
        dst_common_list: list[Path],
        source_hexmap: dict[str, list],
        destination_hexmap: dict[str, list],
        logger: IO,
    ):
        matching_index: [None, int] = None
        for x in range(len(dst_common_list)):
            # set iterator to last matching index to prevent skipping dst_common_list items
            x = matching_index if matching_index is not None else x

            if dst_common_list[x] in src_common_list:
                matching_index = x
                src_common_item = dst_common_list[x]
                ndx_src_common_item = src_common_list.index(src_common_item)

                DirSync.log_it(
                    logger,
                    f"\nPASS {Path.joinpath(self.destination, src_common_item)}\n",
                )

                # cleanup handled destination index & common path item
                dst_hexmap_index = ndx_on_dst_hexmap[x]
                destination_hexmap["flag"][dst_hexmap_index] = "Z"
                del ndx_on_dst_hexmap[x]
                del dst_common_list[x]

                # cleanup handled source index & common path item
                hexmap_index = ndx_on_src_hexmap[src_common_list.index(src_common_item)]
                source_hexmap["flag"][hexmap_index] = "Z"
                del ndx_on_src_hexmap[ndx_src_common_item]
                src_common_list.remove(src_common_item)

    def rename_duplicates(
        self,
        ndx_on_src_hexmap: list[int],
        ndx_on_dst_hexmap: list[int],
        src_common_list: list[Path],
        dst_common_list: list[Path],
        source_hexmap: dict[str, list],
        destination_hexmap: dict[str, list],
        logger: IO,
    ):
        # 1 - 1 renaming on same index level for both index & path lists
        try:
            for q in range(len(dst_common_list)):
                q = 0
                old_path = Path.joinpath(self.destination, dst_common_list[q])
                new_path = Path.joinpath(self.destination, src_common_list[q])

                if old_path.exists():
                    rename(old_path, new_path)
                    DirSync.log_it(logger, f"\nRENAMED {old_path} to {new_path}\n")
                    # flag hexmap entry & cleanup handled from index list & path list
                    hexmap_index = ndx_on_dst_hexmap[q]
                    destination_hexmap["flag"][hexmap_index] = "Z"
                    del ndx_on_dst_hexmap[q]
                    del dst_common_list[q]
                    hexmap_index = ndx_on_src_hexmap[q]
                    source_hexmap["flag"][hexmap_index] = "Z"
                    del ndx_on_src_hexmap[q]
                    del src_common_list[q]

        # src_common_list had fewer items, remaining dst_common_list items will be removed next
        except IndexError:
            return

    def handle_duplicates(
        self,
        dst_hex: str,
        source_hexmap: dict[str, list],
        destination_hexmap: dict[str, list],
        logger: IO
    ):
        """
        Rename or remove extra duplicates on destination path
        Copy new duplicates from source
        :param dst_hex: Hash digest that is found multiple times on either source or destination
        :param source_hexmap: Dictionary that holds the current duplicates on destination path
        :param destination_hexmap: Dictionary that holds the current duplicates on source path
        :param logger: log file
        :return: action counter for later logging
        """
        # gather the index of each duplicate file on both endpoints
        ndx_on_src_hexmap = [
            ndx for ndx, v in enumerate(source_hexmap["hex"]) if v == dst_hex
        ]
        ndx_on_dst_hexmap = [
            ndx for ndx, v in enumerate(destination_hexmap["hex"]) if v == dst_hex
        ]
        # gather the common paths of each duplicate file on both endpoints
        src_common_list = [
            Path.joinpath(source_hexmap["root"][x], source_hexmap["fname"][x])
            for x in ndx_on_src_hexmap
        ]
        dst_common_list = [
            Path.joinpath(destination_hexmap["root"][x], destination_hexmap["fname"][x])
            for x in ndx_on_dst_hexmap
        ]

        # PASS matching common root
        self.duplicate_pass_check(
            ndx_on_src_hexmap,
            ndx_on_dst_hexmap,
            src_common_list,
            dst_common_list,
            source_hexmap,
            destination_hexmap,
            logger
        )

        # RENAME remaining destination files after PASS check
        if len(dst_common_list) != 0 and len(src_common_list) != 0:
            self.rename_duplicates(
                ndx_on_src_hexmap,
                ndx_on_dst_hexmap,
                src_common_list,
                dst_common_list,
                source_hexmap,
                destination_hexmap,
                logger
            )

        # REMOVE remaining dst common list items
        if len(dst_common_list) != 0 and len(src_common_list) == 0:
            self.remove_old_copies(ndx_on_dst_hexmap, destination_hexmap, logger)

        # DUMP remaining source items
        if len(dst_common_list) == 0 and len(src_common_list) != 0:
            self.dump_source_copies(ndx_on_src_hexmap, source_hexmap, logger)

    def diff_hex(
        self,
        source_hexmap: dict[str, list],
        destination_hexmap: dict[str, list],
        logger,
    ):
        """
        Compare each destination file against source and mark handled for later use under selective dump to destination
        This is where the actual synchronization takes place in the eventuality of a temporarily sync break.
        The most complex scenario is either directories having many identical duplicate files
        Some duplicates can have a different name but the same large content, so the objective is to avoid extra traffic
        """
        # destination-side cleanup
        for j in range(len(destination_hexmap["hex"])):
            dst_root = destination_hexmap["root"][j]
            dst_fname = destination_hexmap["fname"][j]
            dst_hex = destination_hexmap["hex"][j]
            common_root = Path.joinpath(dst_root, dst_fname)
            fpath_on_destination = Path.joinpath(self.destination, common_root)
            expected_path_on_source = Path.joinpath(self.source, common_root)

            # skip flagged items handled during duplication handling scenario
            if destination_hexmap["flag"][j] is not None:
                continue

            # hex match << PASS or RENAME
            # both the source & destination targets must have not been flagged previously
            if dst_hex in source_hexmap["hex"]:
                # source and\or destination has at least 2 duplicates
                if destination_hexmap["hex"].count(dst_hex) > 1:
                    DirSync.log_it(
                        logger, f"\nHandling duplicates for '{common_root}'\n"
                    )
                    self.handle_duplicates(
                        dst_hex, source_hexmap, destination_hexmap, logger
                    )

                # unique hex match
                else:
                    index = source_hexmap["hex"].index(dst_hex)
                    source_hexmap["flag"][index] = "Z"
                    # destination path matching << PASS
                    if expected_path_on_source.exists():
                        DirSync.log_it(logger, f"\nPASS {common_root}\n")

                    # path not matching << RENAME
                    else:
                        new_path = Path.joinpath(
                            self.destination,
                            source_hexmap["root"][index],
                            source_hexmap["fname"][index],
                        )
                        rename(fpath_on_destination, new_path)
                        DirSync.log_it(
                            logger, f"\nRENAMED {fpath_on_destination} TO {new_path}\n"
                        )
            # no hex match << REMOVE
            else:
                remove(fpath_on_destination)
                DirSync.log_it(logger, f"\nDELETED {fpath_on_destination}\n")

        return

    def full_dump_to_destination(self, logger: IO):
        try:
            copytree(self.source, self.destination)

        except OSError as XX:
            if XX.errno == errno.ENOSPC:
                DirSync.log_it(logger, f"{strerror(XX.errno)}\n")
                sys.exit()

        except Exception as X:
            DirSync.log_it(logger, f"Error: {X}\n")

    def selective_dump_to_destination(self, source_hexmap: dict[str, list], logger: IO):
        # potential conflict handled in the previous stage as directories have been already created
        # dumping remaining unflagged files
        for q in range(len(source_hexmap["hex"])):
            if source_hexmap["flag"][q] is None:
                root = source_hexmap["root"][q]
                fname = source_hexmap["fname"][q]
                src = Path.joinpath(self.source, root, fname)
                dst = Path.joinpath(self.destination, root, fname)

                try:
                    copy2(src, dst)
                    DirSync.log_it(logger, f"\n{dst}\n")
                except OSError as XX:
                    if XX.errno == errno.ENOSPC:
                        DirSync.log_it(logger, f"{strerror(XX.errno)}\n")
                        sys.exit()
                except Exception as X:
                    DirSync.log_it(logger, f"{X}\n")

    def one_way_sync(self):
        # make log file
        sync_start = datetime.now()
        logger = DirSync.new_log_file(self.log_path, sync_start)
        DirSync.log_it(
            logger, f"Starting sync at {sync_start.strftime('%y-%m-%d %H:%M')}\n"
        )

        # initial full dump to destination storage
        if len(listdir(self.destination)) == 0 and len(listdir(self.source)) != 0:
            DirSync.log_it(logger, f"\n\n\nPERFORMING FULL SYNC\n\n")
            self.full_dump_to_destination(logger)
        else:
            # get the source directory hash map
            source_hexmap, source_tree = DirSync.generate_hexmap(self.source, logger)
            # get the destination directory hash map
            destination_hexmap, destination_tree = DirSync.generate_hexmap(
                self.destination, logger
            )

            # both tree sets have only the common root extracted during hexmap generation
            DirSync.log_it(
                logger, "\n\n\nUPDATING DESTINATION TREE\n`````````````````````````\n"
            )
            self.mirror_source_dir(source_tree, logger)

            # cleanup on destination storage
            DirSync.log_it(logger, "\n\n\n\nFILE CLEANUP\n````````````\n")
            self.diff_hex(source_hexmap, destination_hexmap, logger)

            # remove dirs after file cleanup
            DirSync.log_it(
                logger,
                "\n\n\nREMOVING OBSOLETE DIRECTORIES\n``````````````````````````````\n",
            )
            self.rm_obsolete_dir(destination_tree, logger)

            # dump left-overs from source
            DirSync.log_it(logger, "\n\n\nADDING NEW CONTENT\n```````````````````\n")
            self.selective_dump_to_destination(source_hexmap, logger)

        sync_finish = datetime.now()

        DirSync.log_it(
            logger,
            f"\n\n\nFinished sync at {datetime.now().strftime('%y-%m-%d %H:%M')}\n\n\n\n{120 * '~'}",
        )

        # determine last sync duration to cut from the interval sleep time until next sync
        sync_duration = (sync_finish - sync_start).seconds
        sync_delta = self.interval - sync_duration

        # close log file to allow reading the last sync events
        logger.close()

        # Sleep for the remaining time interval
        if sync_delta <= 0:
            sleep(dir_sync.interval)
        else:
            sleep(sync_delta)


if __name__ == "__main__":
    # validate input parameters
    argz = DirSync.validate_arg()

    # create the log directory if the input path does not exist
    DirSync.setup_log_path(argz.log_path)

    # EXECUTE PROGRAM
    # On lack of disk space the program will exit
    dir_sync = DirSync(
        argz.source_path,
        argz.destination_path,
        argz.interval,
        argz.time_unit,
        argz.log_path,
    )
    while True:
        dir_sync.one_way_sync()
