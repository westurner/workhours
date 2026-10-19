import contextlib
import io
import logging
import runpy
import sys
import unittest
from datetime import datetime, timedelta
from unittest import mock

from workhours import mergeseq


class MergeSequenceTests(unittest.TestCase):
    def test_extend_timestamps_handles_empty_and_duplicate_groups(self):
        start = datetime(2024, 1, 1)
        events = [
            mergeseq.Item(start, "first"),
            mergeseq.Item(start, "second"),
            mergeseq.Item(start + timedelta(seconds=1), "third"),
        ]

        self.assertEqual(list(mergeseq.extend_timestamps([])), [])
        self.assertEqual(
            list(mergeseq.extend_timestamps(events)),
            [
                mergeseq.Item(start, "first"),
                mergeseq.Item(start + timedelta(microseconds=1), "second"),
                mergeseq.Item(start + timedelta(seconds=1), "third"),
            ],
        )

    def test_embedded_examples_execute(self):
        test_case = mergeseq.Test_sequence_import
        with contextlib.redirect_stdout(io.StringIO()):
            test_case("test_create_test_data").test_create_test_data()
            test_case("test_extend_timestamps").test_extend_timestamps()

    def test_main_logging_modes(self):
        for arguments, expect_basic, expect_level in (
            (["mergeseq"], True, False),
            (["mergeseq", "--verbose"], True, True),
            (["mergeseq", "--quiet", "--verbose"], False, False),
        ):
            with (
                mock.patch.object(sys, "argv", arguments),
                mock.patch.object(logging, "basicConfig") as basic,
                mock.patch.object(logging, "getLogger") as get_logger,
            ):
                mergeseq.main()

            self.assertEqual(basic.called, expect_basic)
            self.assertEqual(get_logger.return_value.setLevel.called, expect_level)

    def test_main_test_option_and_script_entrypoint(self):
        with (
            mock.patch.object(sys, "argv", ["mergeseq", "--test", "case"]),
            mock.patch("unittest.main", return_value=0) as unittest_main,
            mock.patch("builtins.exit") as exit_mock,
        ):
            mergeseq.main()
            self.assertEqual(sys.argv, ["mergeseq", "case"])

        unittest_main.assert_called_once_with()
        exit_mock.assert_called_once_with(0)

        with (
            mock.patch.object(sys, "argv", ["mergeseq", "--quiet"]),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            runpy.run_path(
                "/workspaces/workhours/workhours/mergeseq.py",
                run_name="__main__",
            )
