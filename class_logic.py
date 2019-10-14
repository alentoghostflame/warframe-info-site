from html.parser import HTMLParser
from os import listdir
import yaml


DEFAULT_BASIC_OBJECT: dict = {
    "name": "Default Name",
    "in_game_description": "Default In-Game Description",
    "player_description": "Default player description",
    "base_health": [100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100,
                    100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 200],
    "base_shields": [50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50,
                     50, 50, 50, 50, 50, 75],
    "base_energy": [150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 150,
                    150, 150, 150, 150, 150, 150, 150, 150, 150, 150, 300],
    "chassis_item_name": "Default chassis name",
    "neuroptics_item_name": "Default neuroptics name",
    "systems_item_name": "Default systems name"
}
OFFICIAL_WARFRAME_DROP_TABLE_HTML_FILE = "Unminified_Warframe_DropTables.html"


class ObjectStorage:
    def __init__(self):
        self.warframe_list = WarframeList()
        self.drop_table_reader = DropTableReader()

    def load_all(self):
        self.warframe_load_all()
        self.drop_table_reader.read_file(OFFICIAL_WARFRAME_DROP_TABLE_HTML_FILE)

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
        This handler assumes that there is only one th tag, and that whatever is in that tag should be the first and
        only header. An expected layout follows as such:

        Header 1 (in a th tag)
        Item name 1             Percent chance to drop
        Item name 2             Percent chance to drop


        :param storage_location: Dictionary object to put data inside
        :param data: A string with the data inside the tag being read.
        :return:
        """
        if self.temp_tag == "th":
            self.header_1_handler(storage_location, data, [])
        elif self.temp_tag == "td":
            if any(substring in data for substring in self.DROP_CHANCE_RARITY_NAMES):
                self.temp_drop_chance = data
            else:  # Should be the name of the item.
                self.temp_item_name = data
        if self.temp_item_name and self.temp_drop_chance:
            self.item_and_drop_chance_handler(storage_location[self.temp_header_1])

    def single_header_triple_tag_handler(self, storage_location: dict, data: str):
        """
        This handler assumes that, except for certain key words, whatever is in the th tag should be the first and only
        header. An expected layout follows as such:

        Header 1 (in a th tag)
        Ignored keyword (in th tag)     Ignored keyword (in th tag)     Ignored keyword (in th tag)
        Item/Enemy name 1               Chance for the chance.          Rarity of item with percent
        Item/Enemy name 2               Chance for the chance.          Rarity of item with percent

        :param storage_location: Dictionary object to put data inside
        :param data: A string with the data inside the tag being read.
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
        The most commonly used handler, expecting two headers instead of just one. Tests certain key words (located in
        self.HEADER_2_NAMES) against the data given. If any of the key words are found, assign to header 2. Else, assign
        to header 1. Here is the following expected format:

        Header 1 (in a th tag)
        Header 2 (in th tag)
        Item that can drop              Rarity of item with percent
        Item that can drop 2            Rarity of item with percent

        Because there is not always a second header, a default is created as well, and data may be placed in there
        instead.

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
        This handler expects three headers, and uses key words to separate them. Self.HEADER_2_NAMES for header 2, the
        word "Stage" for header 3, otherwise it is header 1. Here is the following expected format:

        Header 1
        Header 2
        Header 3
        Item 1          Rarity of item with percent
        Item 2          Rarity of item with percent

        :param storage_location: Dictionary object to put data inside.
        :param data: A string with the data inside the tag being read.
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
        and sets that key equal to to set_type (if it does not exist), preferably an empty list or dictionary.

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
        nested dictionary, and sets that key equal to to set_type (if it does not exist), preferably an empty list or
        dictionary.

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
        Mostly created to stop copy and pasting code everywhere. This takes a dictionary, creates a key inside of a
        nest dictionary inside of a nested dictionary, and sets that key equal to set_type (if it does not exist).

        :param storage: A dictionary, preferably the base level. Example, self.mission_storage
        :param data: Name of the key to create.
        :param set_type: Object to make inside of the dictionary. Example, {} or []
        :return:
        """
        if storage[self.temp_header_1][self.temp_header_2].get(data, None) is None:
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
        Appends a dictionary with self.temp_item_name, self.temp_drop_chance, and self.temp_mod_drop_chance to the given
        storage variable.

        :param storage_location: A list, preferably preferably one or two layers inside of a dictionary.
        :return:
        """
        storage_location.append({"item_name": self.temp_item_name, "drop_chance": self.temp_drop_chance,
                                 "mod_drop_chance": self.temp_mod_drop_chance})
        self.temp_item_name = ""
        self.temp_drop_chance = ""
        self.temp_mod_drop_chance = ""

    def clear_tags_and_headers(self):
        """
        A shortcut to wipe the temporary headers and item related variables.
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


class WarframeMaker:
    def __init__(self):
        self.ZERO_TO_30_TUPLE = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,
                                 24, 25, 26, 27, 28, 29, 30]
        self.ZERO_TO_8_TUPLE = [1, 2, 3, 4, 5, 6, 7, 8]
        self.ZERO_TO_3_TUPLE = [0, 1, 2, 3]
        self.EMPTY_ABILITY_DICT = {"name": "", "in_game_description": "", "player_made_description": "",
                                   "duration_effect": [{}, ],
                                   "efficiency_effect": [{}, ],
                                   "range_effect": [{}, ],
                                   "strength_effect": [{}, ],
                                   "misc_effect": [{}, ]}

        self.name: str = ""
        self.in_game_description: str = ""
        self.player_made_description: str = ""
        self.base_health: list = self.ZERO_TO_30_TUPLE
        self.base_armor: list = self.ZERO_TO_30_TUPLE
        self.base_shields: list = self.ZERO_TO_30_TUPLE
        self.base_energy: list = self.ZERO_TO_30_TUPLE
        self.base_sprint_speed: list = self.ZERO_TO_30_TUPLE
        self.in_game_passive: str = ""
        self.player_made_passive: str = ""
        self.abilities = [self.EMPTY_ABILITY_DICT, ]
        self.polarities = {"main": [], "aura": "", "exilus": ""}

    def to_dict(self) -> dict:
        return {"name": self.name, "in_game_description": self.in_game_description,
                "player_made_description": self.player_made_description, "base_health": self.base_health,
                "base_armor": self.base_armor, "base_shields": self.base_shields, "base_energy": self.base_energy,
                "base_sprint_speed": self.base_sprint_speed, "in_game_passive": self.in_game_passive,
                "player_made_passive": self.player_made_passive, "abilities": self.abilities,
                "polarities": self.polarities}

    def create(self):
        print("Series of questions to populate a warframe yaml file.")
        print("Don't enter anything to use the default in the brackets.")

        self.name = ask_question("Name of the Warframe", "")
        self.in_game_description = ask_question("In-game description", "")
        self.player_made_description = ask_question("Custom player made description", "")
        self.base_health = ask_question_for_length(31, "Set base health:", "    Rank")
        self.base_armor = ask_question_for_length(31, "Set base armor:", "    Rank")
        self.base_shields = ask_question_for_length(31, "Set base shields:", "    Rank")
        self.base_energy = ask_question_for_length(31, "Set base energy:", "    Rank")
        self.base_sprint_speed = ask_question_for_length(31, "Set base sprint speed:", "    Rank")
        self.in_game_passive = ask_question("In-game description of passive", "")
        self.player_made_passive = ask_question("Custom player made description of passive", "")
        # ability_count = int(ask_question("How many abilities", 4))
        ability_count = ask_question("How many abilities", 4, int)
        print(ability_count)
        self.abilities = []
        for i in range(ability_count):
            print("Ability #{}".format(i + 1))
            ability_ph = self.EMPTY_ABILITY_DICT.copy()
            ability_ph["name"] = ask_question("  Name of ability", "")
            ability_ph["in_game_description"] = ask_question("  In-game description", "")
            ability_ph["player_made_description"] = ask_question("  Custom player made description", "")
            ability_ph["duration_effect"] = ask_question_about_ability("Duration")
            ability_ph["efficiency_effect"] = ask_question_about_ability("Efficiency")
            ability_ph["range_effect"] = ask_question_about_ability("Range")
            ability_ph["strength_effect"] = ask_question_about_ability("Strength")
            ability_ph["misc_effect"] = ask_question_about_ability("Misc")
            self.abilities.append(ability_ph)

    def export_to_file(self, file_name: str):
        file = open("data/warframes/{}".format(file_name), "w")
        yaml.dump(self.to_dict(), file, default_flow_style=None)


"""
from class_logic import WarframeMaker
test = WarframeMaker()
test.create()
"""


class BasicObject(dict):
    def __init__(self):
        dict.__init__(self)
        self.update(DEFAULT_BASIC_OBJECT.copy())

    def load_from_file(self, file_path: str):
        file = open(file_path, "r")
        self.update(yaml.full_load(file))

    def save_to_file(self, file_name: str):
        file = open(file_name, "w")
        yaml.dump(self.copy(), file, default_flow_style=None)


def ask_question_about_ability(effect: str) -> list:
    # effects_int = int(ask_question("  How many different things does {} effect".format(effect), 1))
    effects_int = ask_question("  How many different things does {} affect".format(effect), 1, int)
    effect_list = []
    for x in range(effects_int):
        print("  {} Effect #{}".format(effect, x + 1))
        effect_name = ask_question("    {} Effect Name".format(effect), "PH")
        effect_stats = ask_question_for_length(4, "    {} Effect Stats".format(effect), "      Rank")
        effect_list.append({"effect_name": effect_name, "effect_stats": effect_stats})
    return effect_list


def ask_question_for_length(length: int, question_string: str, repeat_question_string: str) -> list:
    print(question_string)
    temp_list = []
    for i in range(length):
        if i != 0:
            temp_list.append(ask_question("{} {}".format(repeat_question_string, i), temp_list[i - 1]))
        else:
            temp_list.append(ask_question("{} {}".format(repeat_question_string, i), 0))
    return temp_list


def ask_question(question_string: str, default, returned_type: type = str):
    given = None
    while given is None:
        try:
            given = returned_type(input(question_string + " [{}]: ".format(default)))
        except ValueError:
            print("Value seemed to be an incorrect type, try again?")
    if given != "":
        return given
    else:
        return default
