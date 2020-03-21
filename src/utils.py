import json


def read_channels():
    with open("../data/channels.json", "r") as file:
        json_file = json.load(file)
    return json_file


def save_channels(channels):
    with open("../data/channels.json", "w") as file:
        json.dump(channels, file, indent=2)
