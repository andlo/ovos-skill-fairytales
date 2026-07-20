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
import json


class StoryFetchError(Exception):
    """Raised when a story/index page could not be fetched or parsed
    from andersenstories.com / grimmstories.com."""


class Tales(OVOSSkill):

    # how long a cached story index is considered fresh before we try to
    # re-scrape it (the story lists rarely change)
    INDEX_CACHE_TTL = 60 * 60 * 24 * 7  # 7 days

    @classproperty
    def runtime_requirements(self):
        # the story index and every story text are scraped live, so we
        # still want internet before the *first* load. Once loaded, a
        # cached index (see _refresh_index) and per-session story text
        # cache (see get_story) let the skill keep working through brief
        # connectivity blips, so we don't need to be unloaded when
        # internet drops - failed live fetches are handled gracefully
        # (StoryFetchError -> 'story_unavailable' dialog) instead.
        return RuntimeRequirements(
            internet_before_load=True,
            network_before_load=True,
            requires_internet=True,
            requires_network=True,
            no_internet_fallback=True,
            no_network_fallback=True,
        )

    def initialize(self):
        self.is_reading = False
        # make sure settings are initialized
        self.settings['bookmark'] = 0
        self.settings['story'] = None
        self.index = {}
        # in-memory cache of already-fetched story text, keyed by URL, so
        # 'continue' (and repeat requests for the same story) don't need a
        # fresh scrape every time
        self._story_text_cache = {}
        self.refresh_index()

    def _index_cache_filename(self):
        lang = self.lang.split("-")[0]
        return f"index_{lang}.json"

    def _read_index_cache(self):
        cache_file = self._index_cache_filename()
        if not self.file_system.exists(cache_file):
            return None
        try:
            with self.file_system.open(cache_file, "r") as f:
                return json.load(f)
        except (OSError, ValueError) as e:
            self.log.warning(f"could not read story index cache: {e}")
            return None

    def _write_index_cache(self):
        cache_file = self._index_cache_filename()
        try:
            with self.file_system.open(cache_file, "w") as f:
                json.dump({"timestamp": time.time(), "index": self.index}, f)
        except OSError as e:
            self.log.warning(f"could not write story index cache: {e}")

    def refresh_index(self, force=False):
        """(Re)build self.index.

        Uses a fresh on-disk cache if available, otherwise scrapes live and
        updates the cache. If scraping fails, falls back to a stale cache
        (better an old index than none) instead of leaving self.index empty.
        """
        cached = self._read_index_cache()
        if not force and cached and (time.time() - cached.get("timestamp", 0)) < self.INDEX_CACHE_TTL:
            self.index = cached.get("index", {})
            return
        try:
            self.update_index()
            self._write_index_cache()
        except StoryFetchError as e:
            # don't let a scraping failure prevent the skill from loading -
            # intents will still register, and we can fall back to a stale
            # cache if we have one instead of ending up with no stories
            self.log.error(f"Could not refresh story index: {e}")
            if cached:
                self.log.warning("Falling back to previously cached (possibly stale) story index")
                self.index = cached.get("index", {})

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
        self.speak_dialog('i_know_that', data={"story": result[0]}, wait=True)
        self.settings['story'] = result[0]
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
        if self.is_reading is True:
            self.is_reading = False
            self.settings['bookmark'] = 0
            self.settings['story'] = None
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
        if url in self._story_text_cache:
            return self._story_text_cache[url]
        soup = self.get_soup(url)
        elements = soup.find_all("div", {'itemprop': ['text']})
        if not elements:
            raise StoryFetchError(f"story text not found at {url}")
        text = elements[0].text.strip()
        self._story_text_cache[url] = text
        return text

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
         
