from endstone import Player
from threading import Timer
from endstone.plugin import Plugin
from endstone.command import CommandExecutor, Command, CommandSender
from endstone_restart_plugin.utils.vote import VOTE

class CommadRestart(CommandExecutor):
    def __init__(self, plugin: Plugin):
        self.plugin = plugin
        self.restart_data = GetConfiguration("conf")
        super().__init__()

    def on_command(self, sender: CommandSender, command: Command, args: list[str]) -> bool:
        if not isinstance(sender, Player):
            return False
        
        action = args[0].lower()
        
        if action == "start":
            if sender.is_op:
                self.start_shutdown()
        elif action == "yes":
            self.vote(sender, "yes")
        elif action == "no":
            self.vote(sender, "no")
        
        return True

    def vote(self, sender: Player, vote_type: str):
        if int(VOTE["start"]) == 1:
            
            no_vote_type = ""
            if vote_type == "no":
                no_vote_type = "yes"  
            else:
                no_vote_type = "no"  
            try:
                VOTE["data"][no_vote_type].remove(sender.xuid)
            except:
                pass
            
            if sender.xuid in VOTE["data"][vote_type]:
                return
            
            VOTE["data"][vote_type].append(sender.xuid)
            sender.send_message(f"Вы проголосовали за {vote_type}.")
            print(VOTE)

        else:
            sender.send_message("Голосование о рестарте ещё не началось.")

    def start_shutdown(self):
        self.plugin.server.broadcast_message(message="Вы сейчас все плавно будете кикнуты ;)")
        for i in range(self.restart_data["restart_message_count"]):
            delay = i * self.restart_data["message_delay"] 
            Timer(delay, self.plugin.server.broadcast_message, args=(self.restart_data["restart_message_text"],)).start()

        Timer(self.restart_data["restart_message_count"] * self.restart_data["message_delay"], self.shutdown_server).start()
    
    def shutdown_server(self):
        self.plugin.logger.info("Shutting down the server...")
        for player in self.plugin.server.online_players:
            player.kick(message="рестарт")
        self.server.shutdown()
