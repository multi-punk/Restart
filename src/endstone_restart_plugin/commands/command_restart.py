# command_restart.py
from endstone import Player
from endstone.plugin import Plugin
from endstone.command import CommandExecutor, Command, CommandSender
from endstone_restart_plugin.utils.base import RestartBase
from endstone_restart_plugin.utils.vote import VOTE

class CommadRestart(CommandExecutor, RestartBase):
    def __init__(self, plugin: Plugin):
        self.plugin = plugin
        CommandExecutor.__init__(self)
        RestartBase.__init__(self, plugin)

    def on_command(self, sender: CommandSender, _: Command, args: list[str]) -> bool:
        if not isinstance(sender, Player) or not args:
            return False

        action = args[0].lower()

        match action:
            case "start" if sender.is_op:
                self.start_shutdown()
            case "yes":
                self.vote(sender, "yes")
            case "no":
                self.vote(sender, "no")

        return True

    def vote(self, sender: Player, vote_type: str):
        if int(VOTE["start"]) != 1:
            sender.send_message("nope")
            return

        other = "no" if vote_type == "yes" else "yes"
        if sender.xuid in VOTE["data"].get(other, []):
            VOTE["data"][other].remove(sender.xuid)

        if sender.xuid in VOTE["data"].get(vote_type, []):
            return

        VOTE["data"][vote_type].append(sender.xuid)
        sender.send_message(self.vote_voted.format(**{"type": vote_type}))
    
    def start_shutdown(self):
        super().start_shutdown()
