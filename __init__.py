"""
skill Andersen's Fairy Tales
Copyright (C) 2018  Andreas Lorensen

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from mycroft import MycroftSkill, intent_file_handler
from mycroft.util.parse import match_one
from mycroft.audio import wait_while_speaking
import requests
from bs4 import BeautifulSoup
import time


class AndersensTales(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    def initialize(self):
        self.is_reading = False
        self.lang_url = {'da': 'https://www.andersenstories.com/da/andersen_fortaellinger/',
                         'en': 'https://www.andersenstories.com/en/andersen_fairy-tales/',
                         'de': 'https://www.andersenstories.com/de/andersen_maerchen/',
                         'es': 'https://www.andersenstories.com/es/andersen_cuentos/',
                         'fr': 'https://www.andersenstories.com/fr/andersen_contes/',
                         'it': 'https://www.andersenstories.com/it/andersen_fiabe/',
                         'nl': 'https://www.andersenstories.com/nl/andersen_sprookjes/'}
        self.url = self.lang_url[self.lang[:2]]

    @intent_file_handler('AndersensTales.intent')
    def handle_AndersensTales(self, message):
        if message.data.get("tale") is None:
            response = self.get_response('AndersensTales', num_retries=0)
            if response is None:
                return
        else:
            response = message.data.get("tale")
        index = self.get_index(self.url + "list")
        self.log.info(index)
        result = match_one(response, list(index.keys()))

        if result[1] < 0.8:
            self.speak_dialog('that_would_be', data={"story": result[0]})
            response = self.ask_yesno('is_it_that')
            if not response or response is 'no':
                self.speak_dialog('no_story')
                return
        self.speak_dialog('i_know_that', data={"story": result[0]})
        self.settings['story'] = result[0]
        time.sleep(3)
        self.tell_story(index.get(result[0]), 0)

    @intent_file_handler('continue.intent')
    def handle_continue(self, message):
        if self.settings.get('story') is None:
            self.speak_dialog('no_story_to_continue')
        else:
            story = self.settings.get('story')
            self.speak_dialog('continue', data={"story": story})
            index = self.get_index(self.url + "list")
            self.tell_story(index.get(story), self.settings.get('bookmark') - 1)

    def tell_story(self, url, bookmark):
        self.is_reading = True
        title = self.get_title(url)
        subtitle = self.get_subtitle(url)
        self.speak_dialog('title_by_author', data={'title': title, 'subtitle': subtitle})
        time.sleep(1)
        self.log.info(url)
        lines = self.get_story(url).split('\n\n')
        for line in lines[bookmark:]:
            self.settings['bookmark'] += 1
            time.sleep(.5)
            if self.is_reading is False:
                break
            sentenses = line.split('. ')
            for sentens in sentenses:
                if self.is_reading is False:
                    break
                else:
                    wait_while_speaking()
                    self.speak(sentens, wait=True)
        if self.is_reading is True:
            self.is_reading = False
            self.settings['bookmark'] = 0
            self.settings['story'] = None
            time.sleep(2)
            self.speak_dialog('from_AndersensTales')

    def stop(self):
        self.log.info('stop is called')
        if self.is_reading is True:
            self.is_reading = False
            return True
        else:
            return False

    def get_soup(self, url):
        try:
            r = requests.get(url)
            r.encoding = r.apparent_encoding
            soup = BeautifulSoup(r.text, "html.parser")
            return soup
        except Exception as SockException:
            self.log.error(SockException)

    def get_story(self, url):
        soup = self.get_soup(url)
        lines = [a.text.strip() for a in soup.find_all('div', {'class': ['text']})][0]
        return lines

    def get_title(self, url):
        soup = self.get_soup(url)
        title = [a.text.strip() for a in soup.findAll("h1", {'itemprop': ['name']})][0]
        genre = [a.text.strip() for a in soup.findAll("span", {'itemprop': ['genre']})][0]
        title = title.replace(genre, '')
        return title

    def get_subtitle(self, url):
        soup = self.get_soup(url)
        subtitle = [a.text.strip() for a in soup.find_all('span', {'itemprop': ['headline']})][0]
        return subtitle

    def get_index(self, url):
        soup = self.get_soup(url)
        index = {}
        for link in soup.find_all("a"):
            index.update({link.text: self.url + link.get("href")})
        return index


def create_skill():
    return AndersensTales()
