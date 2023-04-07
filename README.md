# Quantum Task Scheduler

A Python script that uses D-Wave's quantum annealing to optimally schedule tasks over several days. The script takes into account task duration, deadline, priority, unavailable hours, and favorite hours (preferred working hours).

## Usage

python task_scheduler.py <tasks_file> <num_days> [--unavailable_hours_file <unavailable_hours_file>] [--favorite_hours_file <favorite_hours_file>]

- `<tasks_file>`: Path to the CSV file containing the tasks. The CSV file should have the following columns: task, duration, deadline, and priority.
- `<num_days>`: Number of days to schedule tasks.
- `<unavailable_hours_file>` (optional): Path to the file containing space-separated list of hours during which the person does not want to work.
- `<favorite_hours_file>` (optional): Path to the file containing space-separated list of hours during which the person prefers to work.

## Example

python test.py task.csv 1 --unavailable_hours_file unavailable_hours --favorite_hours_file favorite_hours