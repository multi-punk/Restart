# restart.py
from endstone.plugin import Plugin
from endstone.command import CommandExecutor
from datetime import datetime, timedelta
from endstone_restart_plugin.commands.command_restart import CommadRestart
from endstone_restart_plugin.utils.task import Task, tasks, check_tasks
from endstone_restart_plugin.utils.vote import VOTE
from endstone_restart_plugin.utils.base import RestartBase

class Restart(Plugin, RestartBase):
    api_version = "0.5"

    commands = {
        "restart": {
            "description": "Запуск рестарта.",
            "usages": ["/restart (start|yes|no)<name: RestartAction>"],
            "permissions": ["plugin.command.restart"],
        }
    }

    permissions = { 
        "plugin.command.restart": {
            "description": "Только операторы могут использовать команду /restart.",
            "default": True,
        }
    }

    def __init__(self):
        Plugin.__init__(self)
        RestartBase.__init__(self, self)

    def on_enable(self) -> None:
        Plugin.on_enable(self)
        self.schedule_restart_check()
        self.register_command("restart", CommadRestart(self))
        self.server.scheduler.run_task(self, check_tasks, 0, 20)
        tasks.append(Task(0, self.schedule_restart_check))

    def register_command(self, command_name: str, executor: CommandExecutor):
        command = self.get_command(command_name)
        if command:
            command.executor = executor
        else:
            self.logger.warning(f"Command '{command_name}' not found during registration.")

    def schedule_restart_check(self):
        now = datetime.now().time()
        night_start = datetime.strptime(self.night_start, "%H:%M").time()
        night_end = datetime.strptime(self.night_end, "%H:%M").time()

        is_night = (
            night_start < night_end and night_start <= now < night_end
        ) or (
            night_start > night_end and (now >= night_start or now < night_end)
        )

        if is_night:
            tasks.append(Task(0, self.schedule_restart_check))
        else:
            self.run_shutdown_timer()

    def start_shutdown(self):
        no_votes = {p.xuid for p in self.server.online_players if p.xuid in VOTE["data"]["no"]}
        yes_votes = {p.xuid for p in self.server.online_players if p.xuid in VOTE["data"]["yes"]}
        undecided = {p.xuid for p in self.server.online_players} - yes_votes - no_votes
        yes_votes.update(undecided)

        if len(yes_votes) >= len(no_votes):
            super().start_shutdown()
        else:
            self.reset_restart_state()
            self.schedule_restart_check()
            self.server.broadcast_message(self.vote_delay)
            VOTE["start"] = 0
