import yaml


DEFAULT_BASIC_OBJECT: dict = {
    "name": "Default Name",
    "description": "Default Description",
    "base_heath": [100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100,
                   100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 200],
    "base_shields": [50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50,
                     50, 50, 50, 50, 50, 75],
    "base_energy": [150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150,
                    150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 300]
}


class BasicObject:
    def __init__(self):
        self.data: dict = DEFAULT_BASIC_OBJECT.copy()

    def load(self, file_object):
        pass

    def save(self, file_name):
        file = open(file_name, "w")
        yaml.dump(self.data, file, default_flow_style=None)
