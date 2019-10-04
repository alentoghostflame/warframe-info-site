from html.parser import HTMLParser
from os import listdir
import yaml


DEFAULT_BASIC_OBJECT: dict = {
    "name": "Default Name",
    "description": "Default Description",
    "base_health": [100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100,
                    100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 200],
    "base_shields": [50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50,
                     50, 50, 50, 50, 50, 75],
    "base_energy": [150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150,
                    150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 300]
}


class ObjectStorage:
    def __init__(self):
        self.warframe_list = WarframeList()

    def load_all(self):
        self.warframe_load_all()

    def warframe_load_all(self):
        self.warframe_list.load_all()

    def warframe_load(self, file_path: str):
        self.warframe_list.load(file_path)


class DropTableParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.storage: dict = {}
        self.basic_missions: set = set()
        self.open_world_missions: set = set()
        self.relics: set = set()

        self.selected_type: str = ""

        self.mission_location: str = ""
        self.mission_rotation: str = "default"
        self.mission_stage: str = "default"
        self.mod_drop_chance: str = ""
        self.enemy_name: str = ""

        self.item_name: str = ""
        self.drop_chance = ""

        self.temp_tag: str = ""

    def read_file(self, file_path: str):
        self.feed(open(file_path, "r").read())

    def handle_starttag(self, tag, attrs):
        # print("Start tag: {}   Attributes: {}".format(tag, attrs))
        if tag == "h3":
            if attrs == [("id", "missionRewards")] or attrs == [("id", "keyRewards")] or \
                    attrs == [("id", "transientRewards")] or attrs == [("id", "sortieRewards")]:
                print("Basic mission encountered:", attrs)
                self.selected_type = "basic_mission"
            elif attrs == [("id", "cetusRewards")] or attrs == [("id", "solarisRewards")]:
                print("Open world mission encountered:", attrs)
                self.selected_type = "open_world_mission"
            elif attrs == [("id", "modByAvatar")]:
                self.selected_type = "enemy_mod_drops"
            else:
                self.selected_type = "other"

        self.temp_tag = tag

    def handle_endtag(self, tag):
        # print("End tag: {}".format(tag))
        pass

    def handle_data(self, data):
        # print("Data: {}".format(data))
        if data.rstrip():
            if self.selected_type == "basic_mission":
                self.handle_basic_mission(data)
            elif self.selected_type == "open_world_mission":
                self.handle_open_world_mission(data)
            elif self.selected_type == "enemy_mod_drops":
                self.handle_enemy_mod_drops(data)

    def handle_basic_mission(self, data):
        if self.temp_tag == "th":
            if "Rotation" in data:
                # Rotation in a mission; 1, 2, and 3 typically.
                self.mission_rotation = data
                self.storage[self.mission_location][self.mission_rotation] = []
            else:
                # Should be the name or location of the mission.
                self.mission_location = data
                self.basic_missions.add(self.mission_location)
                self.storage[self.mission_location] = {}
                self.storage[self.mission_location]["default"] = []
                self.mission_rotation = "default"
        elif self.temp_tag == "td":
            if "%" in data:
                # It's the drop chance of an item.
                self.drop_chance = data
            else:
                # Should be the name of the item.
                self.item_name = data
        if self.item_name and self.drop_chance:
            self.storage[self.mission_location][self.mission_rotation].append({"item_name": self.item_name,
                                                                               "drop_chance": self.drop_chance})
            self.item_name = ""
            self.drop_chance = ""

    def handle_open_world_mission(self, data: str):
        if self.temp_tag == "th":
            if "Cetus Bounty" in data or "Ghoul Bounty" in data or \
                    "Orb Vallis Bounty" in data or "PROFIT-TAKER" in data:
                # This should be the mission name/level. Example, Level 5 - 15 Cetus Bounty
                self.mission_location = data
                self.open_world_missions.add(self.mission_location)
                self.storage[self.mission_location] = {}
                # self.storage[self.mission_location]["default"] = []
                # self.mission_rotation = "default"
            elif "Rotation" in data or "Completion" in data:
                # This should be the mission rotation. Example, Rotation B
                self.mission_rotation = data
                self.storage[self.mission_location][self.mission_rotation] = {}
            elif "Stage" in data:
                # This should be the stage of the mission. Example, Stage 4 of 5
                self.mission_stage = data
                self.storage[self.mission_location][self.mission_rotation][self.mission_stage] = []
            else:
                print("SOMETHING TERRIBLE HAPPENED:", data)
        elif self.temp_tag == "td":
            if "%" in data:
                # It's the drop chance of an item.
                self.drop_chance = data
            else:
                # Should be the name of the item.
                self.item_name = data
        if self.item_name and self.drop_chance:
            self.storage[self.mission_location][self.mission_rotation][self.mission_stage].append(
                {"item_name": self.item_name, "drop_chance": self.drop_chance})
            self.item_name = ""
            self.drop_chance = ""

    def handle_enemy_mod_drops(self, data: str):
        if self.temp_tag == "th":
            if "%" in data:
                # This should be the chance for a mod to drop.
                self.mod_drop_chance = data
                self.storage[self.enemy_name][self.mod_drop_chance] = []
            else:
                # This sould be the name of an enemy
                self.enemy_name = data
                self.storage[self.enemy_name] = {}
        elif self.temp_tag == "td":
            if "%" in data:
                # It's the drop chance of an item.
                self.drop_chance = data
            else:
                # Should be the name of the item.
                self.item_name = data
        if self.item_name and self.drop_chance:
            self.storage[self.enemy_name][self.mod_drop_chance].append({"item_name": self.item_name,
                                                                        "drop_chance": self.drop_chance})
            self.item_name = ""
            self.drop_chance = ""

    def error(self, message):
        print("ERROR:", message)


"""
import yaml
import class_logic
test = class_logic.DropTableParser()
test.read_file("Unminified_Warframe_DropTables.html")
yaml.dump(test.storage, open("Test.yaml", "w"), default_flow_style=None)
exit()
"""


class WarframeList:
    def __init__(self):
        self.raw: list = []
        self.warframes: dict = {}
        self.names: list = []
        self.file_names: list = []

    def load_all(self):
        file_list = listdir("data/warframes/")
        for file in file_list:
            self.load("data/warframes/{}".format(file))

    def load(self, file_path: str):
        warframe = BasicObject()
        warframe.load_from_file(file_path)
        self.raw.append(warframe)
        self.names.append(warframe.get("name", "Name not found!"))
        self.file_names.append(file_path.split("/")[-1].rsplit(".", 1)[0])
        self.warframes[file_path.split("/")[-1].rsplit(".", 1)[0]] = warframe


class BasicObject(dict):
    def __init__(self):
        dict.__init__(self)
        self.update(DEFAULT_BASIC_OBJECT.copy())

    def load_from_file(self, file_path: str):
        file = open(file_path, "r")
        self.update(yaml.full_load(file))

    def save_to_file(self, file_name: str):
        file = open(file_name, "w")
        yaml.dump(self, file, default_flow_style=None)
