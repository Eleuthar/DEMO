import unittest
from os import mkdir, walk
from pathlib import Path
from src.dir_sync import DirSync, setup_logging, validate_log_path
from shutil import copytree, rmtree

"""
"test folders" tree before sync
├── destination
|     ├── 1. Auth.pdf
|     ├── Folder 1
|     |     └── Folder 3
|     |         ├── 1. Auth.pdf
|     |         └── to be removed 1
|     |             ├── 1. Auth.pdf
|     |             ├── Q.py
|     |             └── to be removed 2
|     |                 ├── to be removed 3
|     |                 |     └── to be removed 5
|     |                 |         └── to be replaced.pptx
|     |                 └── to be removed 4
|     |                     └── copy of Q.py
|     ├── Folder 2
|     |     ├── 1. Auth.pdf
|     |     └── to be removed.xml
|     ├── New folder
|     |     └── unique matching.txt
|     └── to be renamed by Proto$.pdf
|
|
└── source
    ├── Folder 1
    |     └── Folder 3
    |         └── 4 Codarea vorbirii.pptx
    ├── Folder 2
    |     ├── 1. Auth.pdf
    |     └── to mirror 1
    |         └── to mirror 2
    |             └── 1. Auth.pdf
    ├── New folder
    |     ├── 1. Auth.pdf
    |     └── unique matching.txt
    └── Proto$coale de Securitate.pdf
"""


class DirSyncTestCase(unittest.TestCase):
    dir_sync = None

    @classmethod
    def setUpClass(cls) -> None:
        # desynchronized test folders
        copytree(Path("./test folders/source"), Path("./source"))
        copytree(Path("./test folders/destination"), Path("./destination"))

        # setup log directory & file
        log_path = Path("logz").resolve()
        validate_log_path(log_path)
        logg = setup_logging(log_path)

        # new sync object
        src = Path("source").resolve()
        dst = Path("destination").resolve()
        cls.dir_sync = DirSync(src, dst, 15, logg)
        cls.dir_sync.source_hexmap, cls.dir_sync.source_tree = DirSync.generate_xmap(
            src, logg
        )
        (
            cls.dir_sync.destination_hexmap,
            cls.dir_sync.destination_tree,
        ) = DirSync.generate_xmap(dst, logg)

    @classmethod
    def tearDownClass(cls) -> None:
        # remove folders
        rmtree("./source")
        rmtree("./destination")

    def test_generate_hex(self):
        target = Path("test folders/destination/1. Auth.pdf").resolve()
        digest = DirSync.generate_file_hex(target)
        self.assertEqual(isinstance(digest, str), True)

    # 1st SYNC phase: mirroring directories
    def test_mirror_source_dir(self):
        DirSyncTestCase.dir_sync.mirror_source_dir()
        self.assertEqual(
            (
                Path.exists(Path("destination/Folder 2/to mirror 1"))
                and Path.exists(Path("destination/Folder 2/to mirror 1/to mirror 2"))
            ),
            True,
        )

    # 2nd SYNC phase:
    def test_remove_not_matching(self):
        # DELETE /home/qvq/PycharmProjects/dirSync/destination/Folder 2/to be removed.xml
        # DELETE "destination/Folder 1/Folder 3/to be deleted 1/to be deleted 2/to be removed 3/ \
        # to be removed 5/to be replaced.pptx"
        DirSyncTestCase.dir_sync.remove_not_matching()
        self.assertEqual(
            (
                not Path.exists(Path("destination/Folder 2/to be removed.xml"))
                and not Path.exists(
                    Path(
                        "destination/Folder 1/Folder 3/to be deleted 1/to be deleted 2"
                        "/to be removed 3/to be removed 5/to be replaced.pptx"
                    )
                )
            ),
            True,
        )

    # 3rd SYNC phase
    def test_handle_duplicates(self):
        # ensure the proper folder exists
        DirSyncTestCase.dir_sync.mirror_source_dir()
        # remove the extra duplicate on destination if any
        # rename non-extra copy
        DirSyncTestCase.dir_sync.handle_duplicates()

        src_file_duplicates = []
        dest_file_duplicates = []

        for dir_path, dir_name, fname in walk("source"):
            if fname == "1. Auth.pdf":
                src_file_duplicates.append(fname)

        for dir_path, dir_name, fname in walk("destination"):
            if fname == "1. Auth.pdf":
                dest_file_duplicates.append(fname)

        self.assertEqual(len(src_file_duplicates) == len(dest_file_duplicates), True)

    # 4th SYNC phase
    def test_handle_unique_matching(self):
        DirSyncTestCase.dir_sync.handle_unique_match()
        self.assertEqual(
            (
                Path.exists(
                    Path("destination/New folder/unique matching.txt").resolve()
                )
                and Path.exists(Path("source/New folder/unique matching.txt").resolve())
            ),
            True,
        )

    # 5th SYNC phase
    def test_rm_obsolete_dir(self):
        # Remove 'destination/Folder 1/Folder 3/to be deleted 1/to be deleted 2/to be removed 3'
        # Remove 'destination/Folder 1/Folder 3/to be deleted 1/to be deleted 2'
        # Remove 'destination/Folder 1/Folder 3/to be deleted 1'
        DirSyncTestCase.dir_sync.rm_obsolete_dir()
        self.assertEqual(
            (
                not Path.exists(
                    Path(
                        "destination/Folder 1/Folder 3/to be deleted 1/to be deleted 2/to be removed 3"
                    )
                )
                and not Path.exists(
                    Path(
                        "destination/Folder 1/Folder 3/to be deleted 1/to be deleted 2/"
                    )
                )
                and not Path.exists(
                    Path("destination/Folder 1/Folder 3/to be deleted 1")
                )
            ),
            True,
        )

    # 6th SYNC phase
    def test_selective_dump(self):
        # ADD "destination/Folder 1/Folder 3/4 Codarea vorbirii.pptx"
        DirSyncTestCase.dir_sync.selective_dump_to_destination()
        self.assertEqual(
            Path.exists(Path("destination/Folder 1/Folder 3/4 Codarea vorbirii.pptx")),
            True,
        )

    def test_full_dump(self):
        # empty the destination directory
        rmtree("destination")
        mkdir("destination")
        DirSyncTestCase.dir_sync.full_dump_to_destination()

        src_files = []
        dest_files = []

        for dirpath, dirname, fname in walk("source"):
            src_files.append(fname)

        for dirpath, dirname, fname in walk("destination"):
            dest_files.append(fname)

        self.assertEqual(src_files == dest_files, True)


if __name__ == "__main__":
    unittest.main()
