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


class DropTableReader(HTMLParser):
    """
    This class reads and translates data from HTML downloaded from the official Warframe drop tables at
    "https://n8k6e2y6.ssl.hwcdn.net/repos/hnfvc0o3jnfvc873njb03enrf56.html"
    into data usable by the warframe info site.
    """
    def __init__(self):
        HTMLParser.__init__(self)
        """ Constant names for various things. """
        self.DROP_CHANCE_RARITY_NAMES: tuple = ("Very Common (", "Common (", "Uncommon (", "Rare (", "Ultra Rare (",
                                                "Legendary (")
        self.HEADER_2_NAMES: tuple = ("Rotation A", "Rotation B", "Rotation C", "Bounty Completion", "First Completion",
                                      "Subsequent Completions", "Mod Drop Chance", "Blueprint/Item Drop Chance",
                                      "Resource Drop Chance", "Sigil Drop Chance", "Additional Item Drop Chance")
        """ Specific storage dictionaries. """
        self.mission_storage: dict = {}
        self.relic_storage: dict = {}
        self.key_mission_storage: dict = {}
        self.dynamic_mission_storage: dict = {}
        # Dynamic mission storage includes sorties
        self.open_world_mission_storage: dict = {}
        self.enemy_drop_storage: dict = {}
        self.mod_storage: dict = {}
        self.item_storage: dict = {}

        """ Temporary tags assigned by self.handle_starttag() and used in the handlers."""
        self.temp_tag: str = ""
        self.temp_section: str = ""

        """ Temporary tags assigned and used by the various handlers. """
        self.temp_header_1: str = ""  # Used as the mission location, mission name, or relic name typically.
        self.temp_header_2: str = ""  # Used as the rotation name typically.
        self.temp_header_3: str = ""  # Used as the name of the stage typically.
        self.temp_item_name: str = ""  # Used as the name of the item being dropped.
        self.temp_drop_chance: str = ""  # Used as the chance for the item to be dropped.
        self.temp_mod_drop_chance: str = ""

    def export_full(self) -> dict:
        """
        Export all the different storage dictionaries in a single dictionary. Good for exporting to a single YAML file.
        :return: A dictionary with all the internal storage dictionaries in it.
        """
        return {"missions": self.mission_storage, "relics": self.relic_storage,
                "key_missions": self.key_mission_storage, "dynamic_missions": self.dynamic_mission_storage,
                "enemy_drops": self.enemy_drop_storage, "mods": self.mod_storage,
                "open_world_missions": self.open_world_mission_storage, "items": self.item_storage}

    def read_file(self, file_path: str):
        """
        Shortcut to quickly feed a file into the parser.
        :param file_path: String path to the file.
        :return:
        """
        self.feed(open(file_path, "r").read())

    def handle_starttag(self, tag: str, attrs: list):
        """
        Runs when the parser encounters a starting HTML tag.
        Assigns self.temp_tag to the latest tag found, and assigns self.temp_section when it reaches a new section of
        the html page.
        :param tag: The type of tag. Example: th, td, h3...
        :param attrs: Attributes of the tag. Example: [], [("id", "transientRewards)]...
        :return:
        """
        self.temp_tag = tag
        if tag == "h3" and attrs and "id" in attrs[0]:
            print("Section found:", attrs[0][1])
            self.clear_tags_and_headers()
            self.temp_section = attrs[0][1]

    def handle_data(self, data):
        """
        If the data isn't empty or pure whitespace, run a handler function based on what the current section is.
        :param data:
        :return:
        """
        if data.rstrip():
            if self.temp_section == "missionRewards":
                self.double_header_handler(self.mission_storage, data)
            elif self.temp_section == "relicRewards":
                self.single_header_handler(self.relic_storage, data)
            elif self.temp_section == "keyRewards":
                self.double_header_handler(self.key_mission_storage, data)
            elif self.temp_section == "transientRewards" or self.temp_section == "sortieRewards":
                self.double_header_handler(self.dynamic_mission_storage, data)
            elif self.temp_section == "cetusRewards" or self.temp_section == "solarisRewards":
                self.triple_header_handler(self.open_world_mission_storage, data)
            elif self.temp_section == "modByAvatar":
                self.double_header_handler(self.enemy_drop_storage, data)
            elif self.temp_section == "modByDrop":
                self.single_header_triple_tag_handler(self.mod_storage, data)
            elif self.temp_section == "blueprintByAvatar":
                self.double_header_handler(self.enemy_drop_storage, data)
            elif self.temp_section == "blueprintByDrop":
                self.single_header_triple_tag_handler(self.item_storage, data)
            elif self.temp_section == "resourceByAvatar":
                self.double_header_handler(self.enemy_drop_storage, data)
            elif self.temp_section == "resourceByDrop":
                self.single_header_triple_tag_handler(self.item_storage, data)
            elif self.temp_section == "sigilByAvatar":
                self.double_header_handler(self.enemy_drop_storage, data)
            elif self.temp_section == "additionalItemByAvatar":
                self.double_header_handler(self.enemy_drop_storage, data)

    def handle_endtag(self, tag):
        """
        Nothing to see here, move along.
        :param tag: A string with the data inside the tag being read.
        :return:
        """
        pass

    def error(self, message):
        print("A BASE ERROR HAS OCCURRED:", message)

    def single_header_handler(self, storage_location: dict, data: str):
        """
        The relic handler. Handles relic drop data in the following format:
        Name of Relic (Rarity upgrade level)
        Item that can drop              Rarity of item with percent
        Item that can drop 2            Rarity of item with percent

        No rotations/2nd level header. It goes the name and rarity of the relic, then immediately to the items that can
        drop.
        :param storage_location: Dictionary object to put data inside
        :param data: A string with the data inside the tag being read.
        :return:
        """
        if self.temp_tag == "th":
            # if "Relic" in data:
            self.header_1_handler(storage_location, data, [])
            # else:
            #     print("SINGLE HEADER HANDLER ISSUE:", data)
        elif self.temp_tag == "td":
            if any(substring in data for substring in self.DROP_CHANCE_RARITY_NAMES):
                self.temp_drop_chance = data
            else:  # Should be the name of the item.
                self.temp_item_name = data
        if self.temp_item_name and self.temp_drop_chance:
            self.item_and_drop_chance_handler(storage_location[self.temp_header_1])

    def single_header_triple_tag_handler(self, storage_location: dict, data: str):
        """

        :param storage_location:
        :param data:
        :return:
        """
        if self.temp_tag == "th" and data != "Enemy Name" and data != "Mod Drop Chance" and data != "Chance" and \
                data != "Blueprint/Item Drop Chance" and data != "Resource Drop Chance":
            self.header_1_handler(storage_location, data, [])
        elif self.temp_tag == "td":
            if any(substring in data for substring in self.DROP_CHANCE_RARITY_NAMES):
                self.temp_drop_chance = data
            elif "%" in data:
                self.temp_mod_drop_chance = data
            else:
                self.temp_item_name = data
        if self.temp_item_name and self.temp_drop_chance and self.temp_mod_drop_chance:
            self.triple_tag_handler(storage_location[self.temp_header_1])

    def double_header_handler(self, storage_location: dict, data: str):
        """
        A handler that assumes the following:
            The mission name or location is in a th tag;
            the rotation name, assuming one is there, will be in a th tag;
            the name of an item is in a td tag;
            the drop chance of an item is in a td tag;
            the amount of item names and item drop chance declarations are the same;
            and that an item name will be read, then the matching drop chance will be read, or vice-versa.

        Here is the following expected format.

        Mission Planet/Mission Node (Mission Type)
        Rotation Name
        Item that can drop              Rarity of item with percent
        Item that can drop 2            Rarity of item with percent

        Notes:
            There may not be a Rotation Name/2nd level header. For example, assassination missions don't have any
                rotations.
            The Mission Planet/Mission Node (Mission Type) header may be replaced with just a Mission Name header. For
                example, Mercury/Apollodorus (Survival) VS Mutalist Alad V Assassinate.

        :param storage_location: Dictionary object to put data inside.
        :param data: A string with the data inside the tag being read.
        :return:
        """
        if self.temp_tag == "th":
            if any(substring in data for substring in self.HEADER_2_NAMES):
                self.header_2_handler(storage_location, data, [])
            else:
                self.header_1_handler(storage_location, data, {}, create_default=True, default_type=[])
        elif self.temp_tag == "td":
            if any(substring in data for substring in self.DROP_CHANCE_RARITY_NAMES):
                self.temp_drop_chance = data
            else:
                self.temp_item_name = data
        if self.temp_item_name and self.temp_drop_chance:
            self.item_and_drop_chance_handler(storage_location[self.temp_header_1][self.temp_header_2])

    def triple_header_handler(self, storage_location: dict, data: str):
        """

        :param storage_location:
        :param data:
        :return:
        """
        if self.temp_tag == "th":
            if any(substring in data for substring in self.HEADER_2_NAMES):
                self.header_2_handler(storage_location, data, {})
            elif "Stage" in data:
                self.header_3_handler(storage_location, data, [])
            else:
                self.header_1_handler(storage_location, data, {})
        elif self.temp_tag == "td":
            if any(substring in data for substring in self.DROP_CHANCE_RARITY_NAMES):
                self.temp_drop_chance = data
            else:
                self.temp_item_name = data
        if self.temp_item_name and self.temp_drop_chance:
            self.item_and_drop_chance_handler(storage_location[self.temp_header_1][self.temp_header_2]
                                              [self.temp_header_3])

    def header_1_handler(self, storage: dict, data: str, set_type, create_default: bool = False, default_type=None):
        """
        Mostly created to stop copy and pasting code everywhere. This takes a dictionary, creates a key,
        and sets that key equal to to set_type, preferably an empty list or dictionary.
        :param storage: A dictionary, preferably the base level. Example, self.mission_storage.
        :param data: Name of the key to create.
        :param set_type: Object to make inside of the dictionary. Example, {} or []
        :param create_default: Should a default be created.
        :param default_type: Object that the default should be. Example, {} or []
        :return:
        """
        if storage.get(data, None) is None:
            storage[data] = set_type
        self.temp_header_1 = data
        if create_default:
            self.header_2_handler(storage, "default", default_type)

    def header_2_handler(self, storage: dict, data: str, set_type):
        """
        Mostly created to stop copy and pasting code everywhere. This takes a dictionary, creates a key inside of a
        nested dictionary, and sets that key equal to to set_type, preferably an empty list or dictionary.
        :param storage: A dictionary, preferably the base level. Example, self.mission_storage
        :param data: Name of the key to create.
        :param set_type: Object to make inside of the dictionary. Example, {} or []
        :return:
        """
        if storage[self.temp_header_1].get(data, None) is None:
            storage[self.temp_header_1][data] = set_type
        self.temp_header_2 = data

    def header_3_handler(self, storage: dict, data: str, set_type):
        """

        :param storage:
        :param data:
        :param set_type:
        :return:
        """
        storage[self.temp_header_1][self.temp_header_2][data] = set_type
        self.temp_header_3 = data

    def item_and_drop_chance_handler(self, storage: list):
        """
        Appends a dictionary with self.temp_item_name and self.temp_drop_chance to the given storage variable.
        :param storage: A list, preferably preferably one or two layers inside of a dictionary.
        Example, self.mission_storage[self.temp_header_1][self.temp_header_2]
        :return:
        """
        storage.append({"item_name": self.temp_item_name, "drop_chance": self.temp_drop_chance})
        self.temp_item_name = ""
        self.temp_drop_chance = ""

    def triple_tag_handler(self, storage_location: list):
        """

        :param storage_location:
        :return:
        """
        storage_location.append({"item_name": self.temp_item_name, "drop_chance": self.temp_drop_chance,
                                 "mod_drop_chance": self.temp_mod_drop_chance})
        self.temp_item_name = ""
        self.temp_drop_chance = ""
        self.temp_mod_drop_chance = ""

    def clear_tags_and_headers(self):
        """

        :return:
        """
        self.temp_header_1: str = ""
        self.temp_header_2: str = ""
        self.temp_header_3: str = ""
        self.temp_item_name: str = ""
        self.temp_drop_chance: str = ""
        self.temp_mod_drop_chance: str = ""

"""
import yaml
import class_logic
test = class_logic.DropTableReader()
test.read_file("Unminified_Warframe_DropTables.html")
yaml.dump(test.export_full(), open("Test.yaml", "w"), default_flow_style=None)
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
