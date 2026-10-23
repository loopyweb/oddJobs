import io
import os
import tempfile
import unittest

from oddJobs import (
    ASSIGNED, COMPLETED, OPEN,
    DuplicateError, InvalidStateError, NotFoundError, OddJobs, main,
)


class OddJobsTests(unittest.TestCase):
    def setUp(self):
        self.board = OddJobs()
        self.board.add_client("Alice")
        self.board.add_freelancer("Bob")

    def test_add_job_gets_incrementing_ids(self):
        first = self.board.add_job("Mow lawn", "Alice")
        second = self.board.add_job("Paint fence", "Alice")
        self.assertEqual((first.id, second.id), (1, 2))
        self.assertEqual(first.status, OPEN)

    def test_add_job_requires_known_client(self):
        with self.assertRaises(NotFoundError):
            self.board.add_job("Mow lawn", "Nobody")

    def test_empty_names_rejected(self):
        with self.assertRaises(ValueError):
            self.board.add_freelancer("   ")
        with self.assertRaises(ValueError):
            self.board.add_job("", "Alice")

    def test_duplicates_rejected(self):
        with self.assertRaises(DuplicateError):
            self.board.add_client("Alice")
        with self.assertRaises(DuplicateError):
            self.board.add_freelancer("Bob")

    def test_assign_requires_known_freelancer(self):
        job = self.board.add_job("Mow lawn", "Alice")
        with self.assertRaises(NotFoundError):
            self.board.assign_job(job.id, "Mallory")
        self.assertEqual(job.status, OPEN)

    def test_assign_unknown_job(self):
        with self.assertRaises(NotFoundError):
            self.board.assign_job(99, "Bob")

    def test_full_lifecycle(self):
        job = self.board.add_job("Mow lawn", "Alice")
        self.board.assign_job(job.id, "Bob")
        self.assertEqual((job.status, job.assigned_to), (ASSIGNED, "Bob"))
        self.board.complete_job(job.id)
        self.assertEqual(job.status, COMPLETED)

    def test_reassign_before_completion(self):
        self.board.add_freelancer("Carol")
        job = self.board.add_job("Mow lawn", "Alice")
        self.board.assign_job(job.id, "Bob")
        self.board.assign_job(job.id, "Carol")
        self.assertEqual(job.assigned_to, "Carol")

    def test_cannot_complete_unassigned_job(self):
        job = self.board.add_job("Mow lawn", "Alice")
        with self.assertRaises(InvalidStateError):
            self.board.complete_job(job.id)

    def test_cannot_change_completed_job(self):
        job = self.board.add_job("Mow lawn", "Alice")
        self.board.assign_job(job.id, "Bob")
        self.board.complete_job(job.id)
        with self.assertRaises(InvalidStateError):
            self.board.complete_job(job.id)
        with self.assertRaises(InvalidStateError):
            self.board.assign_job(job.id, "Bob")

    def test_view_jobs_filters_by_status(self):
        a = self.board.add_job("Mow lawn", "Alice")
        self.board.add_job("Paint fence", "Alice")
        self.board.assign_job(a.id, "Bob")
        self.assertEqual([j.id for j in self.board.view_jobs(ASSIGNED)], [a.id])
        self.assertEqual(len(self.board.view_jobs()), 2)
        with self.assertRaises(ValueError):
            self.board.view_jobs("bogus")

    def test_view_lists_are_copies(self):
        self.board.view_freelancers().append("Eve")
        self.assertEqual(self.board.view_freelancers(), ["Bob"])

    def test_save_and_load_round_trip(self):
        job = self.board.add_job("Mow lawn", "Alice")
        self.board.assign_job(job.id, "Bob")
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "data.json")
            self.board.save(path)
            loaded = OddJobs.load(path)
        self.assertEqual(loaded.view_clients(), ["Alice"])
        self.assertEqual(loaded.get_job(job.id), job)
        self.assertEqual(loaded.add_job("Next", "Alice").id, 2)

    def test_load_missing_file_gives_empty_board(self):
        board = OddJobs.load(os.path.join(tempfile.gettempdir(), "does-not-exist-oddjobs.json"))
        self.assertEqual(board.view_jobs(), [])


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = os.path.join(self.tmp.name, "data.json")

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        code = main(["--data", self.data, *args], out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def test_workflow_persists_between_runs(self):
        self.assertEqual(self.run_cli("add-client", "Alice")[0], 0)
        self.assertEqual(self.run_cli("add-freelancer", "Bob")[0], 0)
        code, out, _ = self.run_cli("add-job", "Alice", "Mow lawn")
        self.assertEqual(code, 0)
        self.assertIn("Job #1 added", out)
        self.assertEqual(self.run_cli("assign", "1", "Bob")[0], 0)
        self.assertEqual(self.run_cli("complete", "1")[0], 0)

        code, out, _ = self.run_cli("jobs", "--status", "completed")
        self.assertEqual(code, 0)
        self.assertIn("Mow lawn", out)
        self.assertIn("Bob", out)

    def test_error_returns_nonzero_and_message(self):
        code, out, err = self.run_cli("add-job", "Nobody", "Mow lawn")
        self.assertEqual(code, 1)
        self.assertIn("Client 'Nobody' not found", err)
        self.assertFalse(os.path.exists(self.data))

    def test_empty_lists(self):
        self.assertIn("No freelancers yet.", self.run_cli("freelancers")[1])


if __name__ == "__main__":
    unittest.main()
