from endstone.command import CommandExecutor
from endstone.plugin import Plugin
from endstone_restart_plugin.utils import GetConfiguration
from endstone_restart_plugin.commands.command_restart import CommadRestart
from endstone_restart_plugin.utils.vote import VOTE
from datetime import datetime, timedelta
from endstone_restart_plugin.utils.task import *

class Restart(Plugin):
    api_version = "0.5" 
    restart_data = GetConfiguration("conf")
    shutdown_interval = restart_data["shutdown_interval"]
    restart_message_count = restart_data["restart_message_count"]  
    message_delay = restart_data["message_delay"]  
    restart_message_text = restart_data["restart_message_text"]
    night_start = restart_data["night_start"]
    night_end = restart_data["night_end"]
    last_restart = datetime.now()

    def on_load(self) -> None:
        self.logger.info("on_load is called!")

    def on_enable(self) -> None:
        self.logger.info("on_enable is called!")
        self.check_night_time_and_start_timer()
        self.register_command(
            command_name="restart",
            executor=CommadRestart(self)
        )
        self.server.scheduler.run_task(self, check_tasks,  0, 20)
        # tasks.append(Task(0, self.check_night_time_and_start_timer))
    
    commands = {
        "restart": {
            "description": "Запуск рестарта.",
            "usages": ["/restart (start|yes|no)<name: RestartAction>"],
            "permissions": ["plugin.command.restart"],
        }
    }

    permissions = { 
        "plugin.command.restart": {
            "description": f"Только операторы могут использовать команду /restart.",
            "default": True,
        }
    }
        
    def register_command(self, command_name: str, executor: CommandExecutor):
        command = self.get_command(command_name)
        if command is not None:
            command.executor = executor
        else:
            self.logger.warning(f"Command '{command_name}' not found during registration.")
        
    def check_night_time_and_start_timer(self):
        current_time = datetime.now()
        night_start_time = datetime.strptime(self.night_start, "%H:%M").time()
        night_end_time = datetime.strptime(self.night_end, "%H:%M").time()

        is_night_time = (night_start_time < night_end_time and night_start_time <= current_time.time() < night_end_time) or (night_start_time > night_end_time and (current_time.time() >= night_start_time or current_time.time() < night_end_time))

        if is_night_time:
            tasks.append(Task(0, self.check_night_time_and_start_timer))
        else:
            self.shutdown_timer()


    first_was = False
    second_was = False
    third_was = False
    forth_was = False
    def shutdown_timer(self):
        restart_time = self.last_restart + timedelta(seconds=self.shutdown_interval)
        now = datetime.now()
        one_minute = restart_time - timedelta(minutes=1)
        five_minutes = restart_time - timedelta(minutes=5)
        ten_minutes = restart_time - timedelta(minutes=10)

        if restart_time < now and not self.forth_was:
            self.forth_was = True
            self.start_shutdown()
        elif one_minute < now and not self.third_was:
            self.third_was = True
            self.send_vote_notification()
        elif five_minutes < now and not self.second_was:
            self.second_was = True
            self.send_notification(5)
        elif ten_minutes < now and not self.first_was:
            self.first_was = True
            self.send_notification(10)
        else:
            tasks.append(Task(0, self.shutdown_timer))


    def send_vote_notification(self):
        self.server.broadcast_message(message="Начинается голосование за скип рестарта! Воспользуйтесь командой '/restart yes' чтобы проголосовать за рестарт, и '/restart no' чтобы скипнуть его")
        VOTE["start"] = 1
        VOTE["data"] = {"yes": [],"no": []}
        tasks.append(Task(0, self.shutdown_timer))

    def send_notification(self, minutes):
        message = f"Сервер будет перезапущен менее чем через {minutes} минут(ы)!"
        for player in self.server.online_players:
            player.send_toast(title="Рестарт", content=message)
        tasks.append(Task(0, self.shutdown_timer))

    def start_shutdown(self):
        yes_count = []
        no_count = []
        for player in self.server.online_players:
            if player.xuid in VOTE["data"]["yes"]:
                yes_count.append(player.xuid)
            elif player.xuid in VOTE["data"]["no"]:
                no_count.append(player.xuid)
            else:
                yes_count.append(player.xuid)
                
        yes_len = len(yes_count)
        no_len = len(no_count)
        
        if yes_len >= no_len:
            self.server.broadcast_message(message="Голосование закончено, вы сейчас все плавно будете кикнуты.")
            for i in range(self.restart_message_count):
                delay = i * self.message_delay
                tasks.append(Task(delay, self.server.broadcast_message, args=(self.restart_message_text,)))

            tasks.append(Task(self.restart_message_count * self.message_delay, self.shutdown_server))
        else:
            self.server.broadcast_message(message="Голосование закончено, скип рестарта.")
            self.first_was = False
            self.second_was = False
            self.third_was = False
            self.forth_was = False
            self.last_restart = datetime.now()
            self.check_night_time_and_start_timer()
            VOTE["start"] = 0
            
            
    def shutdown_server(self):
        self.logger.info("Shutting down the server...")
        self.server.shutdown()