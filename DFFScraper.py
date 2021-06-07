import requests
from bs4 import BeautifulSoup

class DFFScraper():
    def __init__(self, url, params):
        self.url = url
        self.params = params

    def scrape(self):
        rows = []
        page = requests.get(self.url)
        soup = BeautifulSoup(page.content, 'html.parser')
        for tr in soup.findAll("tr", class_="projections-listing"):
            rows.append(tr.attrs)
        return rows
    
    def toPlayerObject(self, n):
        player = {}
        player["date"] = n["data-start_date"]
        player["name"] = n["data-name"]
        player["fn"] = n["data-fn"]
        player["ln"] = n["data-ln"]
        player["pos"] = n["data-pos"]
        player["inj"] = n["data-inj"]
        player["team"] = n["data-team"]
        player["salary"] = n["data-salary"]
        player["ppg_proj"] = n["data-ppg_proj"]
        player["value_proj"] = n["data-value_proj"]
        return player
    
    def toPlayerList(self, raw): 
        return list(map(self.toPlayerObject, raw))