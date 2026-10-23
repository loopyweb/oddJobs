"""Odd jobs management system: connects clients with freelancers for small tasks.

Use it as a library (the OddJobs class) or from the command line:

    python oddJobs.py --help
"""
import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from typing import Optional

OPEN = "open"
ASSIGNED = "assigned"
COMPLETED = "completed"
STATUSES = (OPEN, ASSIGNED, COMPLETED)

DEFAULT_DATA_FILE = "oddjobs.json"


class OddJobsError(Exception):
    """Base class for all errors raised by OddJobs."""


class NotFoundError(OddJobsError):
    """A job, client or freelancer does not exist."""


class InvalidStateError(OddJobsError):
    """The requested action is not allowed in the job's current state."""


class DuplicateError(OddJobsError):
    """A client or freelancer with that name already exists."""


@dataclass
class Job:
    id: int
    description: str
    client: str
    assigned_to: Optional[str] = None
    status: str = OPEN


def _clean_name(value, label):
    value = (value or "").strip()
    if not value:
        raise ValueError(f"{label} must not be empty")
    return value


class OddJobs:
    def __init__(self):
        self.jobs = {}
        self.clients = []
        self.freelancers = []
        self._next_id = 1

    # --- people ---

    def add_client(self, name):
        name = _clean_name(name, "Client name")
        if name in self.clients:
            raise DuplicateError(f"Client '{name}' already exists")
        self.clients.append(name)
        return name

    def add_freelancer(self, name):
        name = _clean_name(name, "Freelancer name")
        if name in self.freelancers:
            raise DuplicateError(f"Freelancer '{name}' already exists")
        self.freelancers.append(name)
        return name

    def view_clients(self):
        return list(self.clients)

    def view_freelancers(self):
        return list(self.freelancers)

    # --- jobs ---

    def add_job(self, description, client):
        description = _clean_name(description, "Job description")
        if client not in self.clients:
            raise NotFoundError(f"Client '{client}' not found")
        job = Job(id=self._next_id, description=description, client=client)
        self.jobs[job.id] = job
        self._next_id += 1
        return job

    def get_job(self, job_id):
        try:
            return self.jobs[job_id]
        except KeyError:
            raise NotFoundError(f"Job {job_id} not found") from None

    def view_jobs(self, status=None):
        if status is not None and status not in STATUSES:
            raise ValueError(f"Unknown status '{status}'")
        return [job for job in self.jobs.values() if status is None or job.status == status]

    def assign_job(self, job_id, freelancer):
        job = self.get_job(job_id)
        if freelancer not in self.freelancers:
            raise NotFoundError(f"Freelancer '{freelancer}' not found")
        if job.status == COMPLETED:
            raise InvalidStateError(f"Job {job_id} is already completed")
        job.assigned_to = freelancer
        job.status = ASSIGNED
        return job

    def complete_job(self, job_id):
        job = self.get_job(job_id)
        if job.status == OPEN:
            raise InvalidStateError(f"Job {job_id} has not been assigned yet")
        if job.status == COMPLETED:
            raise InvalidStateError(f"Job {job_id} is already completed")
        job.status = COMPLETED
        return job

    # --- persistence ---

    def to_dict(self):
        return {
            "next_id": self._next_id,
            "clients": self.clients,
            "freelancers": self.freelancers,
            "jobs": [asdict(job) for job in self.jobs.values()],
        }

    @classmethod
    def from_dict(cls, data):
        board = cls()
        board.clients = list(data.get("clients", []))
        board.freelancers = list(data.get("freelancers", []))
        for raw in data.get("jobs", []):
            job = Job(**raw)
            board.jobs[job.id] = job
        board._next_id = data.get("next_id", max(board.jobs, default=0) + 1)
        return board

    def save(self, path):
        tmp_path = f"{path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
        os.replace(tmp_path, path)

    @classmethod
    def load(cls, path):
        if not os.path.exists(path):
            return cls()
        with open(path, encoding="utf-8") as f:
            return cls.from_dict(json.load(f))


# --- command-line interface ---

def format_job(job):
    who = job.assigned_to or "-"
    return f"#{job.id:<4} [{job.status:<9}] {job.description}  (client: {job.client}, freelancer: {who})"


def build_parser():
    parser = argparse.ArgumentParser(prog="oddJobs", description="Manage odd jobs between clients and freelancers.")
    parser.add_argument("--data", default=DEFAULT_DATA_FILE,
                        help=f"JSON file to store data in (default: {DEFAULT_DATA_FILE})")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("add-client", help="register a client")
    p.add_argument("name")

    p = sub.add_parser("add-freelancer", help="register a freelancer")
    p.add_argument("name")

    p = sub.add_parser("add-job", help="post a job for a client")
    p.add_argument("client")
    p.add_argument("description")

    p = sub.add_parser("jobs", help="list jobs")
    p.add_argument("--status", choices=STATUSES)

    p = sub.add_parser("assign", help="assign a job to a freelancer")
    p.add_argument("job_id", type=int)
    p.add_argument("freelancer")

    p = sub.add_parser("complete", help="mark an assigned job as completed")
    p.add_argument("job_id", type=int)

    sub.add_parser("clients", help="list clients")
    sub.add_parser("freelancers", help="list freelancers")
    return parser


def main(argv=None, out=sys.stdout, err=sys.stderr):
    args = build_parser().parse_args(argv)
    board = OddJobs.load(args.data)
    changed = True

    try:
        if args.command == "add-client":
            print(f"Client added: {board.add_client(args.name)}", file=out)
        elif args.command == "add-freelancer":
            print(f"Freelancer added: {board.add_freelancer(args.name)}", file=out)
        elif args.command == "add-job":
            job = board.add_job(args.description, args.client)
            print(f"Job #{job.id} added: {job.description}", file=out)
        elif args.command == "assign":
            job = board.assign_job(args.job_id, args.freelancer)
            print(f"Job #{job.id} assigned to {job.assigned_to}", file=out)
        elif args.command == "complete":
            job = board.complete_job(args.job_id)
            print(f"Job #{job.id} marked as completed", file=out)
        else:
            changed = False
            if args.command == "jobs":
                items = [format_job(job) for job in board.view_jobs(args.status)]
            elif args.command == "clients":
                items = board.view_clients()
            else:
                items = board.view_freelancers()
            print("\n".join(items) if items else f"No {args.command} yet.", file=out)
    except (OddJobsError, ValueError) as e:
        print(f"Error: {e}", file=err)
        return 1

    if changed:
        board.save(args.data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
