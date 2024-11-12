# Restart
A Plugin plugin in Python for Endstone

## Usage
create folder in dir /plugins/configuration/restart


than in this folder create file conf.json
this file should have this fields

```json
{
    "shutdown_interval": 7200, //Interval in seconds
    "restart_message_count": 10, //Number of messages
    "message_delay": 0.5, //Delay between messages in seconds
    "restart_message_text": "Restart!", //restart notification text
    "night_satrt": "23:00", //start time of the night
    "night_end": "08:00", //end of the night
    "vote": {
        "start": 1,
        "data": {
            "yes": [],
            "no": []
        }
    }
}
```