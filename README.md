# oddJobs

A small odd-jobs board that connects clients with freelancers for small tasks.
Pure Python 3.8+, no dependencies.

## Command line

Data is stored in `oddjobs.json` in the current folder (change it with `--data PATH`).

```bash
python oddJobs.py add-client Alice
python oddJobs.py add-freelancer Bob
python oddJobs.py add-job Alice "Mow the lawn"
python oddJobs.py assign 1 Bob
python oddJobs.py complete 1
python oddJobs.py jobs --status completed
python oddJobs.py clients
python oddJobs.py freelancers
```

Errors (unknown client, freelancer or job, or a step taken out of order) print a
message and exit with status 1.

## Rules

- A job belongs to a registered client and starts out `open`.
- It can only be assigned to a registered freelancer; it can be reassigned until it is completed.
- Only an `assigned` job can be completed, and a `completed` job cannot change.
- Names and descriptions cannot be empty, and client/freelancer names must be unique.

## Library

```python
from oddJobs import OddJobs

board = OddJobs()
board.add_client("Alice")
board.add_freelancer("Bob")
job = board.add_job("Mow the lawn", "Alice")
board.assign_job(job.id, "Bob")
board.complete_job(job.id)
board.save("oddjobs.json")
```

Failures raise `NotFoundError`, `InvalidStateError` or `DuplicateError` (all subclasses of
`OddJobsError`), or `ValueError` for empty input.

## Tests

```bash
python -m unittest -v
```
