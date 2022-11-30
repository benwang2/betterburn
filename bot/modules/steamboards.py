import collections.abc
from indexed import IndexedOrderedDict as odict
import requests, time
from lxml import etree

class SteamLeaderboard:
    def __init__(self, app_id, leaderboard_id, api_key, mute=True):
        self.__app_id__ = app_id
        self.__leaderboard_id__ = leaderboard_id
        self.__api_key__ = api_key
        self.__data__ = odict()
        self.__mute__ = mute

    def __getPlayerPersonas__(self, steam_ids): # max steam_id in one query is 100
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
            return {"exception":e}

    def index(self, i):
        return (self.__data__.keys()[i], self.__data__.values()[i])

    def get(self, key):
        return (self.__data__[key])
    
    def update(self, start=1, limit=None):
        global numRequests
        numRequests = 0
        url = f"https://steamcommunity.com/stats/{self.__app_id__}/leaderboards/{self.__leaderboard_id__}?xml=1&start={start}"
        xml, data, personas = [[],[],[]], odict(), {}
        page_num = (start // 15) + 1
        if limit != None:
            url += "&end="+str(start+(limit-1))
        try:
            t_start = time.time()
            for x in range(0, 5):
                t_start2 = time.time()
                with requests.get(url=url) as page:
                    numRequests += 1
                    root = etree.fromstring(page.content)
                    xml[0].extend(root.xpath("/response/entries/entry/steamid"))
                    xml[1].extend(root.xpath("/response/entries/entry/score"))
                    xml[2].extend(root.xpath("/response/entries/entry/rank"))
                    if (not self.__mute__):  print("Got leaderboard data["+str(root.xpath("/response/entryStart")[0].text)+":"+str(root.xpath("/response/entryEnd")[0].text)+"] in "+str(time.time()-t_start2)+" seconds.")
                    if limit >= 5000 or limit == None:
                        nextURL = root.xpath("/response/nextRequestURL")
                        if (len(nextURL)==0 or nextURL[0].text==url): break
                        url = nextURL[0].text
                    else: break

            if xml[2][0].text != str(start):
                page_num = eval(xml[2][0].text) // 15 + 1

            if (not self.__mute__): print("Took "+str(time.time()-t_start)+" seconds to get all leaderboard entries.")
            t_start = time.time()
            steam_ids = []
            # Add data into an OrderedDict and get Steam display names
            for i in range(0,len(xml[0])):
                elmt = xml[0][i]
                steam_ids.append(elmt.text)
                data[elmt.text] = {"rank":xml[2][i].text, "score":xml[1][i].text}
                if (len(steam_ids) == len(xml[0]) or i%100==99):
                    usersSlice = steam_ids[i-99:i+1] if i%100 == 99 else steam_ids[:]
                    tmp = self.__getPlayerPersonas__(usersSlice)
                    while(tmp.get("exception")):
                        if (not self.__mute__):  print("Rate-limited, sleeping...")
                        time.sleep(10)
                        tmp = self.__getPlayerPersonas__(usersSlice)
                    personas.update(tmp)
            t_end = time.time()
            if (not self.__mute__):  print(f"Took {str(t_end-t_start)} seconds to get personas for all users. avg:"+str((t_end-t_start)/(len(xml[0])/100))+"s per 100 users.")
            t_start = time.time()
            # Combine persona data dict and existing data so it's easy to access
            for key in data:
                if personas.get(key):
                    data[key]["persona"] = personas[key]
                    
            if (not self.__mute__):  print("Took "+str(time.time()-t_start)+" seconds to combine data sets.")
            self.__data__ = data
            return {"data":data,"page":page_num}
        except Exception as e:
            return {"exception":e}

    def csv(self, file = False):
        csv = f"{str(time.gmtime())},{self.__app_id__},{self.__leaderboard_id__},{str(len(self.__data__)-1)}\n"
        for i in range(0, len(self.__data__)): #
            steamid, userdata = self.__data__.keys()[i], self.__data__.values()[i]
            csv += f"{steamid},{userdata['score']},{userdata['persona']}\n"
        return csv