"""
skill OVOS Fairy tales
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

from ovos_bus_client.message import Message 
from ovos_workshop.decorators import intent_handler  
from ovos_workshop.intents import IntentBuilder  
from ovos_workshop.skills import OVOSSkill 
from ovos_utils.parse import match_one
from ovos_utils import classproperty
from ovos_utils.process_utils import RuntimeRequirements


import requests
from bs4 import BeautifulSoup
import time


class StoryFetchError(Exception):
    """Raised when a story/index page could not be fetched or parsed
    from andersenstories.com / grimmstories.com."""


class Tales(OVOSSkill):

    @classproperty
    def runtime_requirements(self):
        # the story index and every story text are scraped live, so this
        # skill is useless without internet, both at load time and at
        # runtime. Once #8/#9 (caching) land, no_internet_fallback can be
        # set to True so the skill isn't unloaded just because the
        # connection blips mid-story.
        return RuntimeRequirements(
            internet_before_load=True,
            network_before_load=True,
            requires_internet=True,
            requires_network=True,
            no_internet_fallback=False,
            no_network_fallback=False,
        )

    def initialize(self):
        self.is_reading = False
        # make sure settings are initialized
        self.settings['bookmark'] = 0
        self.settings['story'] = None
        self.index = {}
        try:
            self.update_index()
        except StoryFetchError as e:
            # don't let a scraping failure prevent the skill from loading -
            # intents will still register, we just won't have stories until
            # the source sites are reachable again (see #8 for caching)
            self.log.error(f"Could not build story index on startup: {e}")

    @intent_handler('Tales.intent')
    def handle_Tales(self, message: Message):
        if not self.index:
            self.speak_dialog('story_unavailable')
            return
        if message.data.get("tale", "") is None:
            response = self.get_response('Tales', num_retries=1)
            if not response:
                return
        else:
            response = message.data.get("tale")
        result = match_one(response, list(self.index.keys()))
        if result[1] < 0.8:
            self.speak_dialog('that_would_be', data={"story": result[0]})
            response = self.ask_yesno('is_it_that')
            if not response or response == 'no':
                self.speak_dialog('no_story')
                return
        self.speak_dialog('i_know_that', data={"story": result[0]})
        self.settings['story'] = result[0]
        time.sleep(3)
        try:
            self.tell_story(self.index[result[0]], 0)
        except StoryFetchError as e:
            self.log.error(f"Could not fetch story: {e}")
            self.is_reading = False
            self.speak_dialog('story_unavailable')

    @intent_handler('continue.intent')
    def handle_continue(self, message: Message):
        if self.settings.get('story') is None:
            self.speak_dialog('no_story_to_continue')
        else:
            story = self.settings.get('story')
            self.speak_dialog('continue', data={"story": story})
            try:
                self.tell_story(self.index.get(story), self.settings.get('bookmark') - 1)
            except StoryFetchError as e:
                self.log.error(f"Could not fetch story: {e}")
                self.is_reading = False
                self.speak_dialog('story_unavailable')

    def tell_story(self, url, bookmark):
        self.is_reading = True
        title = self.get_title(url)
        subtitle = self.get_subtitle(url)
        self.speak_dialog('title_by_author', data={'title': title, 'subtitle': subtitle}, wait=True)
        self.log.info(url)
        lines = self.get_story(url).split('\n\n')
        for line in lines[bookmark:]:
            self.settings['bookmark'] += 1
            if self.is_reading is False:
                break
            sentenses = line.split('. ')
            for sentens in sentenses:
                if self.is_reading is False:
                    sentens = ""
                    break
                else:
                    self.speak_dialog(sentens, wait=True)
                    time.sleep(1)
        if self.is_reading is True:
            self.is_reading = False
            self.settings['bookmark'] = 0
            self.settings['story'] = None
            time.sleep(2)
            self.speak_dialog('from_Tales')

    def stop(self):
        self.log.info('stop is called')
        if self.is_reading is True:
            self.speak_dialog('stop_telling_tales')
            self.speak_dialog('from_Tales')
            self.is_reading = False
            return True
        else:
            return False

    def get_soup(self, url):
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            r.encoding = r.apparent_encoding
            return BeautifulSoup(r.text, "html.parser")
        except requests.RequestException as e:
            raise StoryFetchError(f"failed to fetch {url}: {e}") from e

    def get_story(self, url):
        soup = self.get_soup(url)
        elements = soup.find_all("div", {'itemprop': ['text']})
        if not elements:
            raise StoryFetchError(f"story text not found at {url}")
        return elements[0].text.strip()

    def get_title(self, url):
        soup = self.get_soup(url)
        elements = soup.find_all("h2", {'itemprop': ['name']})
        if not elements:
            raise StoryFetchError(f"title not found at {url}")
        # genre = [a.text.strip() for a in soup.find_all("span", {'itemprop': ['genre']})][0]
        # title = title.replace(genre, '')
        return elements[0].text.strip()

    def get_subtitle(self, url):
        soup = self.get_soup(url)
        elements = soup.find_all("div", {'class': ['subtitle']})
        if not elements:
            raise StoryFetchError(f"subtitle not found at {url}")
        return elements[0].text.strip()

    def get_index(self, url):
        soup = self.get_soup(url)
        lists = soup.find_all("ul", {'class': ['list_link']})
        if not lists:
            raise StoryFetchError(f"story index not found at {url}")
        index = {}
        for link in lists[0].find_all("a"):
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
        lang = self.lang.split("-")[0]
        if lang not in url_andersen:
            lang = "en"
        self.index = {}
        self.index.update(self.get_index(url_andersen[lang] + "list"))
        self.index.update(self.get_index(url_grimm[lang] + "list"))
         
