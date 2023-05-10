r"""
    Usage: python dirSync.py -s|--source_path <source_path> -d|--destination_path <destination_path>
        -i|--interval <integer> -t <S||M||H||D> -l|--log <log_path>

    S = SECONDS, M = MINUTES, H = HOURS, D = DAYS

    Example for synchronizing every 5 minutes with absolute path:
    $ python dirSync.py -s "C:\Users\MrRobot\Documents\Homework" -d "C:\Users\MrRobot\Downloads\Homework" -i 5 -t M
    -l "C:\Program Files\DirSync\logs"
"""

import argparse
from hashlib import md5
import pathlib
from os import mkdir, rename, remove, walk, listdir, strerror
from shutil import copytree, copy2, rmtree
from datetime import datetime
from time import sleep
from typing import IO
import errno


class DirSync:
    timeframe = {"S": 1, "M": 60, "H": 3600, "D": 86400}

    def __init__(
        self, client: str, cloud: str, interval: int, time_unit: str, log_path: str
    ):
        self.client = pathlib.Path(client).resolve()
        self.cloud = pathlib.Path(cloud).resolve()
        self.interval = interval * DirSync.timeframe[time_unit.upper()]
        self.log_path = pathlib.Path(log_path).resolve()

    @staticmethod
    def validate_arg():
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-s",
            "--source_path",
            type=str,
            help="The source directory that needs to be replicated",
        )
        parser.add_argument(
            "-d",
            "--destination_path",
            type=str,
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
            "-l", "--log_path", type=str, help="The directory where logs will be stored"
        )

        if None in parser.parse_args().__dict__.values():
            print(__doc__)
            exit()

        return parser.parse_args()

    @staticmethod
    def setup_log_path(log_path):
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
            exit()

        # only the target log folder may not exist
        if log_path.parent.exists() and not log_path.exists():
            print(f"The directory {log_path.name} does not exist, creating it now.\n")
            mkdir(log_path)

        print(f"Saving logs in {log_path}\n")

    @staticmethod
    def new_log_file(log_path, now: datetime) -> IO:
        """
        Return a new file formatted like: dirSync_2023-04-18.txt
        """
        ymd_now = now.strftime("%Y-%m-%d")
        log_name = f"dirSync_{ymd_now}.txt"
        full_log_path = pathlib.Path.joinpath(log_path, log_name)
        return open(full_log_path, "a", encoding="UTF-8")

    @staticmethod
    def log_it(logger: IO, log_item: str):
        print(log_item)
        logger.write(log_item)

    @staticmethod
    def generate_file_hex(
        target: pathlib.Path,
        common_root: pathlib.Path,
        filename: str,
        blocksize: int = 8192,
    ) -> str:
        """
        Generate a file's hash digest
        :param target: either client or cloud path from the -s or -d argument
        :param common_root: the same path that should be ultimately reflected on both source & destination directories
        :param filename: File's basename
        :param blocksize: Any value as the power of 2. Chunks of 8192 bytes to handle large files
        :return: Cryptographic hash digest
        """
        hh = md5()
        with open(pathlib.Path.joinpath(target, common_root, filename), "rb") as f:
            while buff := f.read(blocksize):
                hh.update(buff)
        return hh.hexdigest()

    @staticmethod
    def generate_hexmap(target: pathlib.Path, logger) -> (dict[str, list], set):
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
                flag[j] initialized to None, but later updated to 'Z' during comparison of source &
                   destination within diff_hex method.
                The flag is necessary in the multiple duplication scenario, if many big files with the same digest are
                   duplicated(same or new name) intentionally on source directory.
                Using this flag will avoid unnecessary CPU workload for deleting then later copying the same file
                   on another destination location
            Set of empty & non-empty directories that will be used for the removal of obsolete directories
        """
        target_tree = set()
        hexmap = {"root": [], "fname": [], "hex": [], "flag": []}
        DirSync.log_it(logger, f"\n\n\n\nHEXMAP for base root '{target}'\n{120 * '-'}")
        for directory in walk(target):
            # directory[0] = dirname: str, directory[1] = [folder basenames], directory[2]=[filenames]
            common_root = directory[0][len(target.__str__()):]
            common_root = pathlib.Path(
                common_root.lstrip("\\")
                if "\\" in common_root
                else common_root.lstrip("/")
            )
            # make a set of all empty and non-empty folders
            target_tree.add(common_root)
            # map only non-empty folders to their children
            for fname in directory[2]:
                hexmap["root"].append(common_root)
                hexmap["fname"].append(pathlib.Path(fname))
                hx = DirSync.generate_file_hex(target, common_root, fname)
                hexmap["hex"].append(hx)
                hexmap["flag"].append(None)

                DirSync.log_it(logger, f"\n{pathlib.Path.joinpath(common_root, fname)}")
                DirSync.log_it(logger, f"\n{hx}")
                DirSync.log_it(logger, f"\n{120 * '-'}")
        return hexmap, target_tree

    def mirror_client_dir(self, client_tree, logger):
        """
        Mirror client directories on destination path from the deepest directory level
        This is a prerequisite for updating destination path files, to prevent OSError by non-existing directory.
        :param client_tree: The common_root path list to be traversed
        :param logger: current date auto-rotating log file
        :return: action counter for later logging
        """
        action_counter = 0
        for dirpath in client_tree:
            next_level = pathlib.Path("")
            for dirname in dirpath.parts:
                # next_level is built progressively to allow mkdir without error
                next_level = pathlib.Path.joinpath(next_level, dirname)
                current_path = pathlib.Path.joinpath(self.cloud, next_level)
                if not pathlib.Path.exists(current_path):
                    mkdir(current_path)
                    DirSync.log_it(logger, f"\nCreated '{current_path}\\' \n")
                    action_counter += 1
        return action_counter

    def rm_obsolete_dir(self, cloud_tree, logger):
        """
        Remove cloud directories that are no longer on client.
        The eligible directories are empty at this stage
        :param cloud_tree: The common_root path list to be traversed
        :param logger: current date auto-rotating log file
        :return: action counter for later logging
        """
        rm_counter = 0
        for cloud_dirpath in cloud_tree:
            cloud_path_on_client = pathlib.Path.joinpath(self.client, cloud_dirpath)
            # handle only joined paths that are not the base common root
            if cloud_path_on_client != self.client and not pathlib.Path.exists(
                cloud_path_on_client
            ):
                try:
                    rm_target = pathlib.Path.joinpath(self.cloud, cloud_dirpath)
                    rmtree(rm_target, ignore_errors=True)
                    rm_counter += 1
                    DirSync.log_it(logger, f"\nRemoved tree of '{rm_target}\\' \n")
                except Exception as X:
                    DirSync.log_it(logger, f"\n{X}\n")
            return rm_counter

    def dump_client_copies(self, ndx_on_src, client_hexmap, logger) -> int:
        diff_counter = 0
        for ndx in ndx_on_src:
            new_path = pathlib.Path.joinpath(
                client_hexmap["root"][ndx], client_hexmap["fname"][ndx]
            )
            from_path = pathlib.Path.joinpath(self.client, new_path)
            to_path = pathlib.Path.joinpath(self.cloud, new_path)

            if not to_path.exists():
                copy2(from_path, to_path)
                diff_counter = 1
                DirSync.log_it(logger, f"Copied {to_path}\n")
                client_hexmap["flag"][ndx] = "Z"
        return diff_counter

    def remove_old_copies(
        self, ndx_on_dst: list[int], cloud_hexmap: dict[str, list], logger: IO
    ) -> int:
        diff_counter = 0
        for ndx in ndx_on_dst:
            dst_dup = pathlib.Path.joinpath(
                self.cloud, cloud_hexmap["root"][ndx], cloud_hexmap["fname"][ndx]
            )
            if dst_dup.exists():
                remove(dst_dup)
                diff_counter = 1
                cloud_hexmap["flag"][ndx] = "Z"
                DirSync.log_it(logger, f"\nDELETED extra duplicate {dst_dup}\n")

        return diff_counter

    def handle_duplicates(self, dst_hex, client_hexmap, cloud_hexmap, logger) -> int:
        """
        Rename or remove extra duplicates on destination path
        Copy new duplicates from source
        :param dst_hex: Hash digest that is found multiple times on either source or destination
        :param client_hexmap: Dictionary that holds the current duplicates on destination path
        :param cloud_hexmap: Dictionary that holds the current duplicates on source path
        :param logger: log file
        :return: action counter for later logging
        """
        diff_counter = 0
        # gather the index of each duplicate file on both endpoints
        ndx_on_src = [
            x
            for x in range(len(client_hexmap["hex"]))
            if client_hexmap["hex"][x] == dst_hex
        ]
        ndx_on_dst = [
            x
            for x in range(len(cloud_hexmap["hex"]))
            if cloud_hexmap["hex"][x] == dst_hex
        ]
        # one of the endpoints may have more duplicates
        max_len = max(len(ndx_on_dst), len(ndx_on_src))

        # 1-1 name refresher
        try:
            for x in range(max_len):
                # can be invalid on client
                dst_path_on_client = pathlib.Path.joinpath(
                    self.client,
                    cloud_hexmap["root"][ndx_on_dst[x]],
                    cloud_hexmap["fname"][ndx_on_dst[x]],
                )
                # current cloud path pending validation
                dst_path = pathlib.Path.joinpath(
                    self.cloud,
                    cloud_hexmap["root"][ndx_on_dst[x]],
                    cloud_hexmap["fname"][ndx_on_dst[x]],
                )
                # client full path to be mirrored if not yet
                src_path_on_cloud = pathlib.Path.joinpath(
                    self.cloud,
                    client_hexmap["root"][ndx_on_src[x]],
                    client_hexmap["fname"][ndx_on_src[x]],
                )
                # for debugging: print(f"\n{dst_path} << \n{dst_path_on_client} vs \n{src_path_on_cloud}\n")

                # REMOVE << dst_path is an obsolete duplicate that exists on a different path
                if (
                    not pathlib.Path.exists(dst_path_on_client)
                    and pathlib.Path.exists(src_path_on_cloud)
                    and src_path_on_cloud != dst_path
                    and pathlib.Path.exists(dst_path)
                ):
                    remove(dst_path)
                    diff_counter = 1
                    DirSync.log_it(
                        logger, f"\nDELETED old renamed duplicate {dst_path}\n"
                    )

                # RENAME << if the current cloud path does not exist on client
                elif not pathlib.Path.exists(
                    dst_path_on_client
                ) and not pathlib.Path.exists(src_path_on_cloud):
                    rename(dst_path, src_path_on_cloud)
                    diff_counter = 1
                    DirSync.log_it(
                        logger,
                        f"\nRENAMED duplicate {dst_path} TO {src_path_on_cloud}\n",
                    )

                cloud_hexmap["flag"][ndx_on_dst[x]] = "Z"
                client_hexmap["flag"][ndx_on_src[x]] = "Z"
                # removing the list item will trigger IndexError if they have different lengths
                del ndx_on_src[0], ndx_on_dst[0]

        # one of the lists is bigger by at least 1 and the other is now empty
        except IndexError:
            # client has the most duplicate files; the remaining will be dumped now
            if len(ndx_on_dst) == 0:
                diff_counter = self.dump_client_copies(
                    ndx_on_src, client_hexmap, logger
                )
            # remove the remaining obsolete cloud duplicates
            else:
                diff_counter = self.remove_old_copies(ndx_on_dst, cloud_hexmap, logger)

        return diff_counter

    def diff_hex(self, client_hexmap, cloud_hexmap, logger) -> int:
        """
        Compare each cloud file against client and mark handled for later use under selective dump to cloud
        This is where the actual synchronization takes place in the eventuality of a temporarily sync break.
        The most complex scenario is either directories having many identical duplicate files
        Some duplicates can have a different name but the same large content, so the objective is to avoid extra traffic
        """
        diff_counter = 0
        # cloud-side cleanup
        for j in range(len(cloud_hexmap["hex"])):
            dst_root = cloud_hexmap["root"][j]
            dst_fname = cloud_hexmap["fname"][j]
            dst_hex = cloud_hexmap["hex"][j]
            common_root = pathlib.Path.joinpath(dst_root, dst_fname)
            fpath_on_cloud = pathlib.Path.joinpath(self.cloud, common_root)
            expected_path_on_client = pathlib.Path.joinpath(self.client, common_root)

            # skip flagged items handled during duplication handling scenario
            if cloud_hexmap["flag"][j] is not None:
                continue

            # hex match << PASS or RENAME
            # both the client & cloud targets must have not been flagged previously
            if dst_hex in client_hexmap["hex"]:
                # client and\or cloud has at least 2 duplicates
                # get the client's matching file index
                if (
                    client_hexmap["hex"].count(dst_hex) > 1
                    or cloud_hexmap["hex"].count(dst_hex) > 1
                ):
                    DirSync.log_it(logger, f"Handling duplicates for '{common_root}'\n")
                    diff_counter += self.handle_duplicates(
                        dst_hex, client_hexmap, cloud_hexmap, logger
                    )
                    continue

                # unique hex match
                else:
                    index = client_hexmap["hex"].index(dst_hex)
                    client_hexmap["flag"][index] = "Z"
                    # cloud path matching << PASS
                    if pathlib.Path.exists(expected_path_on_client):
                        DirSync.log_it(logger, f"\nPASS {common_root}\n")

                    # path not matching << RENAME
                    else:
                        new_path = pathlib.Path.joinpath(
                            self.cloud,
                            client_hexmap["root"][index],
                            client_hexmap["fname"][index],
                        )
                        rename(fpath_on_cloud, new_path)
                        diff_counter += 1
                        DirSync.log_it(
                            logger, f"\nRENAMED {fpath_on_cloud} TO {new_path}"
                        )

            # no hex match << REMOVE
            else:
                remove(fpath_on_cloud)
                diff_counter += 1
                DirSync.log_it(logger, f"\nDELETED {fpath_on_cloud}\n")
                continue

        return diff_counter

    def full_dump_to_cloud(self, logger):
        try:
            copytree(self.client, self.cloud)

        except OSError as XX:
            if XX.errno == errno.ENOSPC:
                DirSync.log_it(logger, f"{strerror(XX.errno)}\n")
                exit()

        except Exception as X:
            DirSync.log_it(logger, f"Error: {X}\n")

    def selective_dump_to_cloud(self, client_hexmap, logger):
        # potential conflict handled in the previous stage as directories have been already created
        # dumping remaining unflagged files
        dump_counter = 0

        for q in range(len(client_hexmap["hex"])):
            if client_hexmap["flag"][q] is None:
                root = client_hexmap["root"][q]
                fname = client_hexmap["fname"][q]
                src = pathlib.Path.joinpath(self.client, root, fname)
                dst = pathlib.Path.joinpath(self.cloud, root, fname)

                if not pathlib.Path.exists(dst) and pathlib.Path.exists(src):
                    try:
                        copy2(src, dst)
                        DirSync.log_it(logger, f"{dst}\n")
                        dump_counter += 1

                    except OSError as XX:
                        if XX.errno == errno.ENOSPC:
                            DirSync.log_it(logger, f"{strerror(XX.errno)}\n")
                            exit()

                    except Exception as X:
                        DirSync.log_it(logger, f"{X}\n")

        return dump_counter

    def one_way_sync(self):
        # make log file
        sync_start = datetime.now()
        logger = DirSync.new_log_file(self.log_path, sync_start)
        DirSync.log_it(
            logger, f"Starting sync at {sync_start.strftime('%y-%m-%d %H:%M')}\n"
        )

        # initial full dump to cloud storage
        if len(listdir(self.cloud)) == 0 and len(listdir(self.client)) != 0:
            DirSync.log_it(logger, f"\n\n\nPERFORMING FULL SYNC\n\n")
            self.full_dump_to_cloud(logger)
        else:
            # get the source directory hash map
            client_hexmap, client_tree = DirSync.generate_hexmap(self.client, logger)
            # get the destination directory hash map
            cloud_hexmap, cloud_tree = DirSync.generate_hexmap(self.cloud, logger)

            # both tree sets have only the common root extracted during hexmap generation
            DirSync.log_it(
                logger, "\n\n\nUPDATING DESTINATION TREE\n`````````````````````````\n"
            )
            new_dir_counter = self.mirror_client_dir(client_tree, logger)
            if new_dir_counter == 0:
                DirSync.log_it(logger, "\nNo action taken\n")

            # cleanup on cloud storage
            DirSync.log_it(logger, "\n\n\n\nFILE CLEANUP\n````````````\n")
            cleanup_counter = self.diff_hex(client_hexmap, cloud_hexmap, logger)
            if cleanup_counter == 0:
                DirSync.log_it(logger, "\nNo action taken\n")

            # remove dirs after file cleanup
            DirSync.log_it(
                logger,
                "\n\n\nREMOVING OBSOLETE DIRECTORIES\n``````````````````````````````\n",
            )
            rm_dir_counter = self.rm_obsolete_dir(cloud_tree, logger)
            if rm_dir_counter == 0:
                DirSync.log_it(logger, "\nNo action taken\n")

            # dump left-overs from client
            DirSync.log_it(logger, "\n\n\nADDING NEW CONTENT\n```````````````````\n")
            dump_counter = self.selective_dump_to_cloud(client_hexmap, logger)
            if dump_counter == 0:
                DirSync.log_it(logger, "\nNo action taken\n")

        sync_finish = datetime.now()
        DirSync.log_it(
            logger,
            f"\n\n\nFinished sync at {datetime.now().strftime('%y-%m-%d %H:%M')}\n",
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
