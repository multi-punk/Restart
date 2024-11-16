from threading import Timer
from endstone.command import CommandExecutor
from endstone.plugin import Plugin
from endstone_restart_plugin.utils import GetConfiguration
from endstone_restart_plugin.commands.command_restart import CommadRestart
from endstone_restart_plugin.utils.vote import VOTE
from datetime import datetime, time, timedelta

class Restart(Plugin):
    api_version = "0.5" 
    restart_data = GetConfiguration("conf")
    shutdown_interval = restart_data["shutdown_interval"]
    restart_message_count = restart_data["restart_message_count"]  
    message_delay = restart_data["message_delay"]  
    restart_message_text = restart_data["restart_message_text"]
    night_start = restart_data["night_start"]
    night_end = restart_data["night_end"]

    def on_load(self) -> None:
        self.logger.info("on_load is called!")

    def on_enable(self) -> None:
        self.logger.info("on_enable is called!")
        self.check_night_time_and_start_timer()
        self.register_command(
            command_name="restart",
            executor=CommadRestart(self)
        )
    
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
            "default": "op",
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

        if night_end_time < night_start_time:
            night_end_datetime = datetime.combine(current_time.date() + timedelta(days=1), night_end_time)
        else:
            night_end_datetime = datetime.combine(current_time.date(), night_end_time)

        is_night_time = (night_start_time < night_end_time and night_start_time <= current_time.time() < night_end_time) or \
                        (night_start_time > night_end_time and (current_time.time() >= night_start_time or current_time.time() < night_end_time))

        if is_night_time:
            self.logger.info(f"Shutdown is disabled between {self.night_start} and {self.night_end}. Skipping.")
            delay = (night_end_datetime - current_time).total_seconds()
            self.logger.info(f"{delay} seconds until the end of the night.")
            Timer(delay, self.start_shutdown_timer).start()
        else:
            self.start_shutdown_timer()

    def start_shutdown_timer(self):
        self.logger.info(f"Starting shutdown timer for {self.shutdown_interval} seconds.")
        
        Timer(self.shutdown_interval, self.start_shutdown).start()
        
        notification_times = [600, 300, 60]  # 10 минут, 5 минут, 1 минута
        for seconds in notification_times:
            Timer(self.shutdown_interval - seconds, self.send_notification, args=(seconds,)).start()

    def send_notification(self, seconds: int):
        message = f"Сервер будет перезапущен через {seconds // 60} минут(ы)!"
        for player in self.server.online_players:
            player.send_toast(title="Рестарт", content=message)
        if seconds == 60:
            self.server.broadcast_message(message="Начинается голосование за скип рестарта! Воспользуйтесь командой '/restart yes' чтобы проголосовать за рестарт, и '/restart no' чтобы скипнуть его")
            self.VOTE["start"] = 1
            self.VOTE["data"] = {"yes": [],"no": []}

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
        
        if yes_len > no_len:
            self.server.broadcast_message(message="Голосование закончено, вы сейчас все плавно будете кикнуты.")
            for i in range(self.restart_data["restart_message_count"]):
                delay = i * self.restart_data["message_delay"] 
                Timer(delay, self.server.broadcast_message, args=(self.restart_data["restart_message_text"],)).start()

            Timer(self.restart_data["restart_message_count"] * self.restart_data["message_delay"], self.shutdown_server).start()
        else:
            self.server.broadcast_message(message="Голосование закончено, скип рестарта.")
            self.check_night_time_and_start_timer()
            
            
    def shutdown_server(self):
        self.logger.info("Shutting down the server...")
        for player in self.server.online_players:
            player.kick(message="рестарт")
        self.server.shutdown()