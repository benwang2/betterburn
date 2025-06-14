import csv
import time

import requests
from indexed import IndexedOrderedDict as odict
from lxml import etree

from config import Config
from custom_logger import CustomLogger as Logger


class SteamLeaderboard:
    def __init__(self, app_id, leaderboard_id, api_key=None, mute=True):
        self.__app_id__ = app_id
        self.__leaderboard_id__ = leaderboard_id
        self.__api_key__ = api_key
        self.__data__ = odict()
        self.__mute__ = mute
        self.logger = Logger("steamboard")

    def __len__(self):
        return len(self.__data__)

    def __getPlayerPersonas__(self, steam_ids):  # max steam_id in one query is 100
        global numRequests
        url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={self.__api_key__}&format=json&steamids="
        for steam_id in steam_ids:
            url += str(steam_id) + ","
        url = url[:-1]
        try:
            with requests.get(url=url) as summaries:
                numRequests += 1
                players = summaries.json()["response"]["players"]
                personas = {}
                for player in players:
                    personas[player["steamid"]] = player["personaname"]
                return personas
        except Exception as e:
            self.logger.error(str(e))

    def index(self, i):
        return (self.__data__.keys()[i], self.__data__.values()[i])

    def get(self, key):
        return self.__data__[key]

    def update(self, start=1, limit=None):
        global numRequests
        numRequests = 0
        url = f"https://steamcommunity.com/stats/{self.__app_id__}/leaderboards/{self.__leaderboard_id__}?xml=1&start={start}"
        xml, data, personas = [[], []], odict(), {}
        if limit is not None:
            url += "&end=" + str(start + (limit - 1))
        try:
            t_start = time.time()
            while True:
                t_start2 = time.time()
                with requests.get(url=url) as page:
                    numRequests += 1
                    root = etree.fromstring(page.content)
                    xml[0].extend(root.xpath("/response/entries/entry/steamid"))
                    xml[1].extend(root.xpath("/response/entries/entry/score"))
                    if not self.__mute__:
                        print(
                            "Got leaderboard data["
                            + str(root.xpath("/response/entryStart")[0].text)
                            + ":"
                            + str(root.xpath("/response/entryEnd")[0].text)
                            + "] in "
                            + str(time.time() - t_start2)
                            + " seconds."
                        )
                    if limit is None or limit >= 5000:
                        nextURL = root.xpath("/response/nextRequestURL")
                        if len(nextURL) == 0 or nextURL[0].text == url:
                            break
                        url = nextURL[0].text
                    else:
                        break

            self.logger.info("Took " + str(time.time() - t_start) + " seconds to get all leaderboard entries.")
            t_start = time.time()
            steam_ids = []
            # Add data into an OrderedDict and get Steam display names
            for i in range(0, len(xml[0])):
                elmt = xml[0][i]
                steam_ids.append(elmt.text)
                data[elmt.text] = {"rank": str(i + 1), "score": xml[1][i].text}

            t_end = time.time()
            self.logger.info(
                f"Took {str(t_end - t_start)} seconds to get personas for all users. avg:"
                + str((t_end - t_start) / (len(xml[0]) / 100))
                + "s per 100 users."
            )

            t_start = time.time()
            # Combine persona data dict and existing data so it's easy to access
            for key in data:
                if personas.get(key):
                    data[key]["persona"] = personas[key]

            self.logger.info("Took " + str(time.time() - t_start) + " seconds to combine data sets.")

            self.__data__ = data
            return data
        except Exception as e:
            self.logger.info(str(e))

    def to_csv(self, csvfile):
        fieldnames = ["rank", "steam_id", "score"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for steam_id, userdata in self.__data__.items():
            row = {
                "steam_id": steam_id,
                "rank": userdata["rank"],
                "score": userdata["score"],
            }
            writer.writerow(row)

    def to_list(self):
        return self.__data__.items()


leaderboard = SteamLeaderboard(Config.app_id, Config.leaderboard_id, False)
leaderboard.update()

if __name__ == "__main__":
    board = SteamLeaderboard(2217000, 14800950, False)
    board.update()

    with open("./data.csv", "w", newline="") as f:
        board.to_csv(f)
