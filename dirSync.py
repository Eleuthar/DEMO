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


def setup_log_path(log_path) -> bool:
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
    return True


class DirSync:
    timeframe = {"S": 1, "M": 60, "H": 3600, "D": 86400}

    def __init__(
        self, client: str, cloud: str, interval: int, time_unit: str, log_path: str
    ):
        self.client = pathlib.Path(client).resolve()
        self.cloud = pathlib.Path(cloud).resolve()
        self.interval = interval * DirSync.timeframe[time_unit.upper()]
        self.log_path = pathlib.Path(log_path).resolve()



    def new_log_file(self) -> IO:
        """
        Return a new file formatted like: dirSync_2023-04-18.txt
        """
        ymd_now = datetime.now().strftime("%Y-%m-%d")
        log_name = f"dirSync_{ymd_now}.txt"
        full_log_path = pathlib.Path.joinpath(self.log_path, log_name)
        return open(full_log_path, "a", encoding="UTF-8")

    @staticmethod
    def log_it(logger: IO, log_item: str):
        print(log_item)
        logger.write(log_item)

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

    def generate_hexmap(self, target: pathlib.Path, logger) -> (dict[str, list], set):
        """
        Map every single filename under the target directory to its own hex digest & path on the same index level.
        Gather unique root paths.
        :param target: either source path or destination path
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
        self.log_it(f"\n\n\n\nHEXMAP for base root '{target}'\n{120 * '-'}")
        for directory in walk(target):
            # directory[0] = dirname: str, directory[1] = [folder basenames], directory[2]=[filenames]
            common_root = directory[0][len(target.__str__()) :]
            common_root = common_root.lstrip("\\") if "\\" in common_root else common_root.lstrip("/")
            # make a set of all empty and non-empty folders
            target_tree.add(pathlib.Path(common_root))
            # map only non-empty folders to their children
            for fname in directory[2]:
                hexmap["root"].append(common_root)
                hexmap["fname"].append(fname)
                hx = generate_file_hex(target, common_root, fname)
                hexmap["hex"].append(hx)
                hexmap["flag"].append(None)
                self.log_it(logger, f"\n{pathlib.Path.joinpath(common_root, fname)}")
                self.log_it(logger, f"\n{hx}")
                self.log_it(logger, f"\n{120 * '-'}")
        return hexmap, target_tree

    def mirror_client_dir(self, client_tree, logger):
        """
        Mirror client directories on destination path from the deepest directory level
        This is a prerequisite for updating destination path files, to prevent OSError by non-existing directory.
        :param client_tree: The common_root path list to be traversed
        :return: action counter for later logging
        """
        action_counter = 0
        for dirpath in client_tree:
            next_level = pathlib.Path('')
            for dirname in dirpath.parts:
                # next_level is built progressively to allow mkdir without error
                next_level = pathlib.Path.joinpath(next_level, dirname)
                current_path = pathlib.Path.joinpath(self.cloud, next_level)
                if not pathlib.Path.exists(current_path):
                    mkdir(current_path)
                    self.log_it(logger, f"\nCreated '{current_path}\\' \n")
                    action_counter += 1
        return action_counter

    def rm_obsolete_dir(self, cloud_tree, logger):
        """
        Remove cloud directories that are no longer on client.
        The eligible directories are empty at this stage
        :param cloud_tree: The common_root path list to be traversed
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
                    self.log_it(logger, f"\nRemoved tree of '{rm_target}\\' \n")
                except Exception as X:
                    self.log_it(logger, f"\n{X}\n")
            return rm_counter

    def diff_hex(self, client_hexmap, cloud_hexmap, logger):
        # iterate each cloud file against client and mark handled for later dump
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
            if cloud_hexmap["flag"][j] != None:
                continue

            # hex match
            # both the client & cloud targets must have not been flagged previously
            if dst_hex in client_hexmap["hex"]:
                # client and\or cloud has at least 2 duplicates

                # get the matching client's file index by "client_hexmap[ 'hex' ].index( dst_hex )"
                if (
                    client_hexmap["hex"].count(dst_hex) > 1
                    or cloud_hexmap["hex"].count(dst_hex) > 1
                ):
                    self.log_it(logger, f"Handling duplicates for '{common_root}'\n")

                    # gather the index for each duplicate file of both endpoints
                    ndx_src = [
                        x
                        for x in range(len(client_hexmap["hex"]))
                        if client_hexmap["hex"][x] == dst_hex
                    ]
                    x = 0

                    ndx_dst = [
                        x
                        for x in range(len(cloud_hexmap["hex"]))
                        if cloud_hexmap["hex"][x] == dst_hex
                    ]
                    x = 0

                    max_len = max(len(ndx_dst), len(ndx_src))

                    # 1-1 name refresher
                    try:
                        for x in range(max_len):
                            # refresh "x" on each iteration to access the first index of ndx_dst & ndx_src after removing on line 354
                            x = 0

                            # can be invalid on client
                            dst_path_on_client = pathlib.Path.joinpath(
                                self.client,
                                cloud_hexmap["root"][ndx_dst[x]],
                                cloud_hexmap["fname"][ndx_dst[x]],
                            )

                            # current cloud path pending validation
                            dst_path = pathlib.Path.joinpath(
                                self.cloud,
                                cloud_hexmap["root"][ndx_dst[x]],
                                cloud_hexmap["fname"][ndx_dst[x]],
                            )

                            # client full path to be mirrored if not yet
                            src_path_on_cloud = pathlib.Path.joinpath(
                                self.cloud,
                                client_hexmap["root"][ndx_src[x]],
                                client_hexmap["fname"][ndx_src[x]],
                            )

                            # for debugging
                            # print(f"\n{dst_path} <<<<<<<<<<<<<< \n{dst_path_on_client} vs \n{src_path_on_cloud}\n")

                            # REMOVE <<<<<<<< dst_path is an obsolete duplicate that exists on a different path than "src_path_on_cloud"
                            if (
                                not pathlib.Path.exists(dst_path_on_client)
                                and pathlib.Path.exists(src_path_on_cloud)
                                and src_path_on_cloud != dst_path
                            ):
                                remove(dst_path)
                                diff_counter += 1
                                self.log_it(logger, f"\nDELETED extra duplicate {dst_path}\n")

                            # RENAME <<<<<<<< if the current cloud path does not exist on client
                            elif not pathlib.Path.exists(
                                dst_path_on_client
                            ) and not pathlib.Path.exists(src_path_on_cloud):
                                rename(dst_path, src_path_on_cloud)
                                diff_counter += 1
                                self.log_it(
                                    f"\nRENAMED duplicate {dst_path} TO {src_path_on_cloud}\n"
                                )

                            cloud_hexmap["flag"][ndx_dst[x]] = "Z"
                            client_hexmap["flag"][ndx_src[x]] = "Z"

                            del ndx_src[0], ndx_dst[0]

                    # one of the lists is bigger by at least 1 and the other is now empty
                    except IndexError as XX:
                        # the client has the bigger duplicate list of files; the remaining will be dumped now
                        if len(ndx_dst) == 0:
                            for ndx in ndx_src:
                                try:
                                    new_path = pathlib.Path.joinpath(
                                        client_hexmap["root"][ndx],
                                        client_hexmap["fname"][ndx],
                                    )
                                    from_path = pathlib.Path.joinpath(self.client, new_path)
                                    to_path = pathlib.Path.joinpath(self.cloud, new_path)

                                    if not pathlib.Path.exists(to_path):
                                        copy2(from_path, to_path)
                                        self.log_it(logger, f"Copied {to_path}\n")
                                        client_hexmap["flag"][ndx] = "Z"

                                except Exception as XXX:
                                    self.log_it(logger, f"\n{XXX}\n")

                        # remove the remaining obsolete cloud duplicates
                        else:
                            for ndx in ndx_dst:
                                try:
                                    remove(
                                        pathlib.Path.joinpath(
                                            self.cloud,
                                            cloud_hexmap["root"][ndx],
                                            cloud_hexmap["fname"][ndx],
                                        )
                                    )
                                    cloud_hexmap["flag"][ndx] = "Z"
                                    self.log_it(
                                        f"\nDELETED extra duplicate {dst_path}\n"
                                    )

                                except FileNotFoundError:
                                    # the file was previously removed
                                    pass

                    except Exception as X:
                        self.log_it(logger, f"\n{X}\n")

                    finally:
                        continue

                # unique hex match
                else:
                    index = client_hexmap["hex"].index(dst_hex)
                    client_hexmap["flag"][index] = "Z"

                    # PASS <<<<< cloud path matching
                    if pathlib.Path.exists(expected_path_on_client):
                        self.log_it(logger, f"\nPASS {common_root}\n")

                    # RENAME <<<<< path not matching
                    else:
                        new_path = pathlib.Path.joinpath(
                            self.cloud,
                            client_hexmap["root"][index],
                            client_hexmap["fname"][index],
                        )
                        rename(fpath_on_cloud, new_path)
                        diff_counter += 1
                        self.log_it(logger, f"\nRENAMED {fpath_on_cloud} TO {new_path}")

            # no hex match
            else:
                try:
                    remove(fpath_on_cloud)
                    diff_counter += 1
                    self.log_it(logger, f"\nDELETED {fpath_on_cloud}\n")

                # except OSError as XX:
                #    if XX.errno == 2:
                #        pass

                except Exception as X:
                    self.log_it(logger, f"{X}\n")

                finally:
                    continue

        return diff_counter

    def full_dump_to_cloud(self, logger):
        try:
            copytree(self.client, self.cloud)

        except OSError as XX:
            if XX.errno == errno.ENOSPC:
                self.log_it(logger, f"{strerror(XX.errno)}\n")
                exit()

        except Exception as X:
            self.log_it(logger, f"Error: {X}\n")

    def selective_dump_to_cloud(self, client_hexmap, cloud_hexmap, logger):
        # potential conflict handled in the previous stage as directories have been already created
        # dumping remaining unflagged files
        dump_counter = 0

        for q in range(len(client_hexmap["hex"])):
            if client_hexmap["flag"][q] == None:
                root = client_hexmap["root"][q]
                fname = client_hexmap["fname"][q]
                src = pathlib.Path.joinpath(self.client, root, fname)
                dst = pathlib.Path.joinpath(self.cloud, root, fname)

                if not pathlib.Path.exists(dst) and pathlib.Path.exists(src):
                    try:
                        copy2(src, dst)
                        self.log_it(logger, f"{dst}\n")
                        dump_counter += 1

                    except OSError as XX:
                        if XX.errno == errno.ENOSPC:
                            self.log_it(logger, f"{strerror(XX.errno)}\n")
                            exit()

                    except Exception as X:
                        self.log_it(logger, f"{X}\n")

        return dump_counter

    def one_way_sync(dir_sync, logger):
        sync_start = datetime.now()
        self.log_it(logger, f"Starting sync at {datetime.now().strftime('%y-%m-%d %H:%M')}\n")

        # initial full dump to cloud storage
        if len(listdir(self.cloud)) == 0 and len(listdir(self.client)) != 0:
            self.log_it(logger, f"\n\n\nPERFORMING FULL SYNC\n\n")
            self.full_dump_to_cloud(logger)
        else:
            # get the source directory hash map
            client_hexmap, client_tree = self.generate_hexmap(self.client, logger)
            # get the destination directory hash map
            cloud_hexmap, cloud_tree = self.generate_hexmap(self.cloud, logger)

            # both tree sets have only the common root extracted during hexmap generation
            self.log_it("\n\n\nUPDATING DESTINATION TREE\n`````````````````````````\n")
            new_dir_counter = self.mirror_client_dir(client_tree, logger)
            if new_dir_counter == 0:
                self.log_it("\nNo action taken\n")

            # cleanup on cloud storage
            self.log_it("\n\n\n\nFILE CLEANUP\n````````````\n")
            cleanup_counter = self.diff_hex(client_hexmap, cloud_hexmap, logger)
            if cleanup_counter == 0:
                self.log_it("\nNo action taken\n")

            # remove dirs after file cleanup
            self.log_it(
                "\n\n\nREMOVING OBSOLETE DIRECTORIES\n``````````````````````````````\n"
            )
            rm_dir_counter = self.rm_obsolete_dir(cloud_tree, logger)
            if rm_dir_counter == 0:
                self.log_it("\nNo action taken\n")

            # dump left-overs from client
            self.log_it("\n\n\nADDING NEW CONTENT\n```````````````````\n")
            dump_counter = self.selective_dump_to_cloud(client_hexmap, cloud_hexmap, logger)
            if dump_counter == 0:
                self.log_it("\nNo action taken\n")

        sync_finish = datetime.now()
        self.log_it(
            f"\n\n\nFinished sync at {datetime.now().strftime('%y-%m-%d %H:%M')}\n"
        )
        return (sync_finish - sync_start).seconds


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
        help=("Number of seconds | minutes | hours | days " "of the next argument"),
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
    argz = parser.parse_args()

    if None in argz.__dict__.values():
        print(__doc__)
        exit()

    return argz

def main_runner(dir_sync: DirSync):
    # setup log file
    log_path_set = DirSync.setup_log_path(dir_sync.)
    logger = DirSync.new_log_file()
    # sync folders
    sync_duration = dir_sync.one_way_sync(logger)
    # determine last sync duration to cut from the interval sleep time until next sync
    sync_delta = dir_sync.interval - sync_duration

    dir_sync.log_it(
        logger,
        f"\nLast sync took {sync_duration} seconds.\n\n\n{80 * '~'}\n\n\n\n\n\n"
    )
    # close log file to allow reading the last sync events
    logger.close()

    if sync_delta <= 0:
        sleep(dir_sync.interval)
        main_runner(log_path_set)
    else:
        sleep(sync_delta)
        main_runner(log_path_set)

if __name__ == "__main__":
    argz = validate_arg()

    dir_sync = DirSync(
        argz.client, argz.cloud, argz.interval, argz.time_unit, argz.log_path
    )
    # On lack of disk space the program will exit
    main_runner(dir_sync)


