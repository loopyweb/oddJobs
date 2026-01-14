#Build an odd jobs management system which connects clients with freelancers for small tasks.
#functions: add_job, view_jobs, assign_job, complete_job, view_freelancers
class OddJobs:
    def __init__(self):
        self.jobs = []
        self.freelancers = []

    def add_job(self, job_description):
        job = {'description': job_description, 'assigned_to': None, 'completed': False}
        self.jobs.append(job)
        return f"Job added: {job_description}"

    def view_jobs(self):
        return self.jobs

    def assign_job(self, job_index, freelancer_name):
        if 0 <= job_index < len(self.jobs):
            self.jobs[job_index]['assigned_to'] = freelancer_name
            return f"Job '{self.jobs[job_index]['description']}' assigned to {freelancer_name}"
        else:
            return "Invalid job index"

    def complete_job(self, job_index):
        if 0 <= job_index < len(self.jobs):
            self.jobs[job_index]['completed'] = True
            return f"Job '{self.jobs[job_index]['description']}' marked as completed"
        else:
            return "Invalid job index"

    def view_freelancers(self):
        return self.freelancers

    def add_freelancer(self, freelancer_name):
        self.freelancers.append(freelancer_name)
        return f"Freelancer added: {freelancer_name}"
