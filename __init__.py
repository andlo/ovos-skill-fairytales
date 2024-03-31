"""
skill HC Andersen's Fairy Tales
Copyright (C) 2024  Andreas Lorensen

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

#from mycroft import MycroftSkill, intent_file_handler
#from mycroft.util.parse import match_one
#from mycroft.audio import wait_while_speaking

from ovos_bus_client.message import Message 
from ovos_workshop.decorators import intent_handler  
from ovos_workshop.intents import IntentBuilder  
from ovos_workshop.skills import OVOSSkill 
from ovos_utils.parse import match_one


import requests
from bs4 import BeautifulSoup
import time


class Tales(OVOSSkill):
    def initialize(self):
        self.is_reading = False
        # make sure settings are initialized
        self.settings['bookmark'] = 0
        self.settings['story'] = None
        self.index = {}
        self.update_index()

    @intent_handler('Tales.intent')
    def handle_Tales(self, message: Message):
        if message.data.get("tale", "") is None:
            response = self.get_response('Tales', num_retries=1)
            if not response:
                return
        else:
            response = message.data.get("tale")
        result = match_one(response, list(self.index.keys()))
        self.speak(result)
        if result[1] < 0.8:
            self.speak_dialog('that_would_be', data={"story": result[0]})
            response = self.ask_yesno('is_it_that')
            if not response or response is 'no':
                self.speak_dialog('no_story')
                return
        self.speak_dialog('i_know_that', data={"story": result[0]})
        self.settings['story'] = result[0]
        time.sleep(3)
        self.tell_story(self.index[result[0]], 0)

    @intent_handler('continue.intent')
    def handle_continue(self, message: Message):
        if self.settings.get('story') is None:
            self.speak_dialog('no_story_to_continue')
        else:
            story = self.settings.get('story')
            self.speak_dialog('continue', data={"story": story})
            self.tell_story(self.index.get(story), self.settings.get('bookmark') - 1)

    def tell_story(self, url, bookmark):
        self.is_reading = True
        title = self.get_title(url)
        subtitle = self.get_subtitle(url)
        self.speak_dialog('title_by_author', data={'title': title, 'subtitle': subtitle}, waite=True)
        self.log.info(url)
        lines = self.get_story(url).split('\n\n')
        for line in lines[bookmark:]:
            self.settings['bookmark'] += 1
            time.sleep(.5)
            if self.is_reading is False:
                lines = []
                break
            sentenses = line.split('. ')
            for sentens in sentenses:
                if self.is_reading is False:
                    sentens = ""
                    break
                else:
                    self.speak(sentens, wait=True)
        if self.is_reading is True:
            self.is_reading = False
            self.settings['bookmark'] = 0
            self.settings['story'] = None
            time.sleep(2)
            self.speak_dialog('from_Tales')

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
        lines = [a.text.strip() for a in soup.find_all("div", {'itemprop': ['text']})][0]
        return lines

    def get_title(self, url):
        soup = self.get_soup(url)
        title = [a.text.strip() for a in soup.find_all("h2", {'itemprop': ['name']})][0]
        # genre = [a.text.strip() for a in soup.find_all("span", {'itemprop': ['genre']})][0]
        # title = title.replace(genre, '')
        return title

    def get_subtitle(self, url):
        soup = self.get_soup(url)
        subtitle = [a.text.strip() for a in soup.find_all("div", {'class': ['subtitle']})][0]
        return subtitle

    def get_index(self, url):
        soup = self.get_soup(url)
        index = {}
        list = soup.find_all("ul", {'class': ['list_link']})[0]
        for link in list.find_all("a"):
            index.update({link.text: link.get("href")})
        return index
    
    def update_index(self):
        url_andersen = {'da': 'https://www.andersenstories.com/da/andersen_fortaellinger/',
                        'en': 'https://www.andersenstories.com/en/andersen_fairy-tales/',
                        'de': 'https://www.andersenstories.com/de/andersen_maerchen/',
                        'es': 'https://www.andersenstories.com/es/andersen_cuentos/',
                        'fr': 'https://www.andersenstories.com/fr/andersen_contes/',
                        'it': 'https://www.andersenstories.com/it/andersen_fiabe/',
                        'nl': 'https://www.andersenstories.com/nl/andersen_sprookjes/'}
        url_grimm = {'da': 'https://www.grimmstories.com/da/grimm_eventyr/',
                     'en': 'https://www.grimmstories.com/en/grimm_fairy-tales/',
                     'de': 'https://www.grimmstories.com/de/grimm_maerchen/',
                     'es': 'https://www.grimmstories.com/es/grimm_cuentos/',
                     'fr': 'https://www.grimmstories.com/fr/grimm_contes/',
                     'it': 'https://www.grimmstories.com/it/grimm_fiabe/',
                     'nl': 'https://www.grimmstories.com/nl/grimm_sprookjes/'}
        self.index = {}
        self.index.update(self.get_index(url_andersen[(self.lang.split("-")[-2] or "en")] + "list"))
        self.index.update(self.get_index(url_grimm[(self.lang.split("-")[-2] or "en")] + "list"))
         
