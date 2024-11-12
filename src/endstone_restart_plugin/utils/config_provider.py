import os
import ujson as json

configuration_path = f"{os.getcwd()}/plugins/configuration/restart/"

def GetConfiguration(file: str) -> dict | list:
    file_path = f"{configuration_path}{file}.json"
    with open(file_path, "r", encoding="utf-8") as jsonFile:
        data = json.load(jsonFile)
        return data
    
def SetConfiguration(file: str, data: dict | list):
    file_path = f"{configuration_path}{file}.json"
    with open(file_path, "w", encoding="utf-8") as jsonFile:
        json.dump(data, jsonFile, ensure_ascii=False, indent=4)