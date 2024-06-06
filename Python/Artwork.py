import json


class Artwork:
    """The artwork, its characteristics and history are the topic of the conversation"""

    def __init__(self, name: str):
        self.nickname = name
        artwork_dict = {
            'huguenot': ["A Huguenot on St. Bartholomew's Day", "a_huguenot_v2.json"],
            'starry': ["The Starry Night", "the_starry_night_v2.json"],
            'liberty': ["Liberty Leading the People", "liberte_guidant_le_peuple_v2.json"],
            'rose': ["The Roses of Heliogabalus", "the_rose_of_heliogabalus_v2.json"]
        }

        artwork_info = next((info for key, info in artwork_dict.items() if key in self.nickname), None)
        if artwork_info is None:
            print("Artwork not found")
        self.name, self.data_path = artwork_info
        self.data = json.load(open(".\\artworks\\" + self.data_path, encoding="utf8"))
        print("Artwork selected:", self.name)
