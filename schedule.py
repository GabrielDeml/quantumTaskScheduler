import argparse
import csv
from dimod import DiscreteQuadraticModel
from dwave.system import LeapHybridDQMSampler


class TaskScheduler:
    def __init__(self, tasks_file, num_days, unavailable_hours_file=None, max_task_duration=1, favorite_hours_file=None):
        self.tasks_file = tasks_file
        self.num_days = num_days
        self.unavailable_hours_file = unavailable_hours_file
        self.max_task_duration = max_task_duration
        self.favorite_hours_file = favorite_hours_file
        self.tasks = self._read_tasks()
        self.tasks = self._split_tasks()
        self.max_deadline = self.num_days * 24
        self.unavailable_hours = self._read_unavailable_hours()
        self.favorite_hours = self._read_favorite_hours()
        self.dqm = DiscreteQuadraticModel()
        self._add_variables()
        self._add_constraints_and_penalties()
        self._add_deadline_and_unavailable_penalties()
        self._add_priority_rewards()

    def _read_favorite_hours(self):
        if self.favorite_hours_file is None:
            return set()

        with open(self.favorite_hours_file, "r") as f:
            favorite_hours = set(map(int, f.read().split()))
        return favorite_hours

    def _read_unavailable_hours(self):
        if self.unavailable_hours_file is None:
            return set()

        with open(self.unavailable_hours_file, "r") as f:
            unavailable_hours = set(map(int, f.read().split()))
        return unavailable_hours

    def _read_tasks(self):
        tasks = {}
        with open(self.tasks_file, "r") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                task = row["task"]
                duration = int(row["duration"])
                deadline = int(row["deadline"])
                priority = int(row["priority"])
                tasks[task] = {"duration": duration, "deadline": deadline, "priority": priority}
        return tasks

    def _add_variables(self):
        for task, info in self.tasks.items():
            num_start_times = self.max_deadline - info['duration'] + 1
            self.dqm.add_variable(num_start_times, label=task)

    def _add_constraints_and_penalties(self):
        penalty = 10
        for task1, info1 in self.tasks.items():
            for task2, info2 in self.tasks.items():
                if task1 < task2:  # To avoid double counting
                    for t1 in range(self.max_deadline - info1['duration'] + 1):
                        for t2 in range(self.max_deadline - info2['duration'] + 1):
                            if t1 <= t2 < t1 + info1['duration'] or t2 <= t1 < t2 + info2['duration']:
                                self.dqm.set_quadratic(task1, task2, {(t1, t2): penalty})

    def _add_deadline_and_unavailable_penalties(self):
        deadline_penalty = 10
        unavailable_penalty = 10
        for task, info in self.tasks.items():
            penalties = [deadline_penalty if t + info['duration'] > info['deadline'] else 0 for t in range(self.max_deadline - info['duration'] + 1)]
            unavailable_penalties = [unavailable_penalty if t in self.unavailable_hours else 0 for t in range(self.max_deadline - info['duration'] + 1)]
            combined_penalties = [penalty + unavailable_penalty for penalty, unavailable_penalty in zip(penalties, unavailable_penalties)]
            self.dqm.set_linear(task, combined_penalties)

    def _add_priority_rewards(self):
            reward_factor = 1
            favorite_hour_reward = 1
            for task, info in self.tasks.items():
                rewards = [reward_factor * info['priority'] / (t + 1) for t in range(self.max_deadline - info['duration'] + 1)]
                favorite_hour_rewards = [favorite_hour_reward if t in self.favorite_hours else 0 for t in range(self.max_deadline - info['duration'] + 1)]
                combined_rewards = [reward + favorite_hour_reward for reward, favorite_hour_reward in zip(rewards, favorite_hour_rewards)]
                current_penalties = self.dqm.get_linear(task)
                combined_biases = [penalty + reward for penalty, reward in zip(current_penalties, combined_rewards)]
                self.dqm.set_linear(task, combined_biases)

    def _split_tasks(self):
        split_tasks = {}
        for task, info in self.tasks.items():
            duration = info['duration']
            num_chunks = duration // self.max_task_duration
            remainder = duration % self.max_task_duration

            for i in range(num_chunks):
                new_task = f"{task}_{i}"
                split_tasks[new_task] = {
                    "duration": self.max_task_duration,
                    "deadline": info['deadline'],
                    "priority": info['priority'],
                }

            if remainder > 0:
                new_task = f"{task}_{num_chunks}"
                split_tasks[new_task] = {
                    "duration": remainder,
                    "deadline": info['deadline'],
                    "priority": info['priority'],
                }

        return split_tasks

    def schedule_tasks(self):
        sampler = LeapHybridDQMSampler()
        sampleset = sampler.sample_dqm(self.dqm)
        best_solution = sampleset.first.sample
        return best_solution


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Schedule tasks optimally over several days.")
    parser.add_argument("tasks_file", help="Path to the CSV file containing the tasks.")
    parser.add_argument("num_days", type=int, help="Number of days to schedule tasks.")
    parser.add_argument("--unavailable_hours_file", type=str, default=None,
                        help="Path to the file containing space-separated list of hours during which the person does not want to work.")
    parser.add_argument("--favorite_hours_file", type=str, default=None,
                        help="Path to the file containing space-separated list of hours during which the person prefers to work.")
    args = parser.parse_args()

    task_scheduler = TaskScheduler(args.tasks_file, args.num_days, args.unavailable_hours_file, favorite_hours_file=args.favorite_hours_file)

    optimal_schedule = task_scheduler.schedule_tasks()

    print("Optimal task schedule:", optimal_schedule)