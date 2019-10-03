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
        # self.names.append([warframe.get("name", "Name Not Found!"), file_path.split("/")[-1].rsplit(".")[0]])
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
