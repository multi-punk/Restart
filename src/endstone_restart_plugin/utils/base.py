# restart_base.py
from endstone.plugin import Plugin
from datetime import datetime, timedelta
from endstone_restart_plugin.utils.config_provider import GetConfiguration
from endstone_restart_plugin.utils.task import Task, tasks
from endstone_restart_plugin.utils.vote import VOTE

class RestartBase:
    def __init__(self, plugin: Plugin):
        self.plugin = plugin
        self.configuration = GetConfiguration("conf")

        self.notify_sound = self.configuration["sound"]

        self.hub_ip = self.configuration["hub"]["ip"]
        self.hub_port = self.configuration["hub"]["port"]

        self.vote_start = self.configuration["vote"]["start"]
        self.vote_delay = self.configuration["vote"]["delay"]
        self.vote_voted = self.configuration["vote"]["voted"]
        self.vote_notification = self.configuration["vote"]["notification"]

        self.toast_title = self.configuration["toast"]["title"]
        self.toast_message = self.configuration["toast"]["message"]

        self.message_delay = self.configuration["messages"]["restart"]["delay"]
        self.restart_message_text = self.configuration["messages"]["restart"]["text"]
        self.restart_message_count = self.configuration["messages"]["restart"]["count"]

        self.shutdown_interval = self.configuration["interval"]

        self.night_start = self.configuration["night"]["start"]
        self.night_end = self.configuration["night"]["end"]

        self.last_restart = datetime.now()

        self.vote_started = False
        self.first_warning_sent = False
        self.second_warning_sent = False
        self.shutdown_initiated = False

    def send_notification(self, minutes: int):
        print("Sending notification...")
        message = self.toast_message.format(**{
            "minutes": minutes,
        })
        for player in self.plugin.server.online_players:
            player.send_toast(title=self.toast_title, content=message)
        tasks.append(Task(0, self.run_shutdown_timer))

    def send_vote_notification(self):
        server = self.plugin.server
        server.broadcast_message(self.vote_notification)
        if self.notify_sound != None:
            for player in server.online_players:
                player.play_sound(player.location, self.notify_sound, 1, 1)
        VOTE["start"] = 1
        VOTE["data"] = {"yes": [], "no": []}
        tasks.append(Task(0, self.run_shutdown_timer))

    def run_shutdown_timer(self):
        now = datetime.now()
        restart_at = self.last_restart + timedelta(seconds=self.shutdown_interval)
        in_10 = restart_at - timedelta(minutes=10)
        in_5 = restart_at - timedelta(minutes=5)
        in_1 = restart_at - timedelta(minutes=1)

        if now >= restart_at and not self.shutdown_initiated:
            self.shutdown_initiated = True
            self.start_shutdown()
        elif now >= in_1 and not self.vote_started:
            self.vote_started = True
            self.send_vote_notification()
        elif now >= in_5 and not self.second_warning_sent:
            self.second_warning_sent = True
            self.send_notification(5)
        elif now >= in_10 and not self.first_warning_sent:
            self.first_warning_sent = True
            self.send_notification(10)
        else:
            tasks.append(Task(0, self.run_shutdown_timer))

    def reset_restart_state(self):
        self.vote_started = False
        self.first_warning_sent = False
        self.second_warning_sent = False
        self.shutdown_initiated = False
        self.last_restart = datetime.now()

    def start_shutdown(self):
        self.plugin.server.broadcast_message(self.vote_start)
        for i in range(self.restart_message_count):
            delay = i * self.message_delay
            tasks.append(Task(delay, self.plugin.server.broadcast_message, args=(self.restart_message_text,)))
        total_delay = self.restart_message_count * self.message_delay
        tasks.append(Task(total_delay, self.shutdown_server))

    def shutdown_server(self):
        self.plugin.logger.info("Shutting down the server...")
        for player in self.plugin.server.online_players:
            player.transfer(self.hub_ip, self.hub_port)
        self.plugin.server.shutdown()
