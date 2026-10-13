import argparse
import json
import tempfile
from pathlib import Path


TASKS_FILE = Path(__file__).with_name("tasks.json")


def main():
    parser = argparse.ArgumentParser(description="Manage tasks stored in tasks.json.")
    commands = parser.add_subparsers(dest="command", required=True)

    add = commands.add_parser("add", help="Add a task")
    add.add_argument("description")
    commands.add_parser("list", help="List tasks")
    for command in ("done", "delete"):
        subparser = commands.add_parser(command)
        subparser.add_argument("id", type=int)

    args = parser.parse_args()
    try:
        tasks = json.loads(TASKS_FILE.read_text(encoding="utf-8")) if TASKS_FILE.exists() else []
        if not isinstance(tasks, list) or any(
            not isinstance(task, dict)
            or type(task.get("id")) is not int
            or not isinstance(task.get("description"), str)
            or type(task.get("done")) is not bool
            for task in tasks
        ):
            parser.error("Invalid task data in tasks.json.")
        task_ids = [task["id"] for task in tasks]
        if len(task_ids) != len(set(task_ids)):
            parser.error("Duplicate task IDs in tasks.json.")
    except (OSError, ValueError) as error:
        parser.error(f"Cannot read tasks.json: {error}")

    if args.command == "list":
        if not tasks:
            print("No tasks.")
        for task in tasks:
            status = "x" if task["done"] else " "
            print(f'{task["id"]}. [{status}] {task["description"]}')
        return

    if args.command == "add":
        description = args.description.strip()
        if not description:
            parser.error("Task description cannot be empty.")
        task_id = max((task["id"] for task in tasks), default=0) + 1
        tasks.append({"id": task_id, "description": description, "done": False})
        message = f"Added task {task_id}."
    else:
        task = next((task for task in tasks if task["id"] == args.id), None)
        if task is None:
            parser.error(f"Task {args.id} not found.")
        if args.command == "done":
            task["done"] = True
            message = f"Completed task {args.id}."
        else:
            tasks.remove(task)
            message = f"Deleted task {args.id}."

    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=TASKS_FILE.parent,
            prefix=".tasks-", suffix=".tmp", delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            temporary_file.write(json.dumps(tasks, ensure_ascii=False, indent=2))
        temporary_path.replace(TASKS_FILE)
    except OSError as error:
        parser.error(f"Cannot save tasks.json: {error}")
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
    print(message)


if __name__ == "__main__":
    main()
