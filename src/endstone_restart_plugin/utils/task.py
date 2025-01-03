class Task:
    delay: int
    task: any
    args: tuple

    def __init__(self, delay: int, task: any, args: tuple = None , kwargs: dict = None):
        self.delay = delay
        self.task = task
        self.args = args if args is not None else []
        self.kwargs = kwargs if kwargs is not None else {}

tasks: list[Task] = []

def check_tasks():
    for task in tasks:
        if task.delay <= 0:
            if task.args is not None:
                task.task(*task.args, **task.kwargs)
            else:   
                task.task()
            tasks.remove(task)
        else:
            task.delay -= 1