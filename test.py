import requests
from bs4 import BeautifulSoup


url = 'https://www.andersenstories.com/da/andersen_fortaellinger/list'
soup = BeautifulSoup(requests.get(url).text, "html.parser")
index = {}
#print(soup)
#list = soup.find_all("ul", {'class': ['list_link']})[0]
#print(list)
#for link in soup.find_all("a"):
#print(list)
#index = {}
#for link in list.find_all("a"):
#    print(link.get("href"))
#    print(link.text)
#    index.update({link.text: link.get("href")})
#print(index)

#for link in list :
#    print(link.get('href'))
#    print(link.text)
#    index.update({link.text: link.get("href")})
#print(index)


#url = 'https://www.andersenstories.com/da/andersen_fortaellinger/fyrtojet'
#r = requests.get(url)
#r.encoding = r.apparent_encoding
#soup = BeautifulSoup(r.text, "html.parser")


#lines = [a.text.strip() for a in soup.find_all("div", {'itemprop': ['text']})][0]
#print(lines)

#title = [a.text.strip() for a in soup.find_all("h2", {'itemprop': ['name']})][0]
#print(title)

#genre = [a.text.strip() for a in soup.find_all("span", {'itemprop': ['genre']})][0]
#print(genre)

#title = title.replace(genre, '')
#ondertitle = [a.text.strip() for a in soup.find_all("div", {'class': ['subtitle']})][0]
#print(ondertitle)

def get_soup(url):
    try:
        r = requests.get(url)
        r.encoding = r.apparent_encoding
        soup = BeautifulSoup(r.text, "html.parser")
        return soup
    except Exception as SockException:
        self.log.error(SockException)

def get_index(url):
    soup = get_soup(url)
    index = {}
    list = soup.find_all("ul", {'class': ['list_link']})[0]
    for link in list.find_all("a"):
        index.update({link.text: link.get("href")})
    return index

#url = 'https://www.andersenstories.com/da/andersen_fortaellinger/list'
#index = {}
#index.update(get_index("https://www.andersenstories.com/da/andersen_fortaellinger/list")) 
#index.update(get_index("https://www.grimmstories.com/en/grimm_fairy-tales/list"))

url = 'https://fairytalez.com/fairy-tales/'
r = requests.get(url)
r.encoding = r.apparent_encoding
soup = BeautifulSoup(r.text, "html.parser")

#lines = [a.text.strip() for a in soup.find_all("div", {'itemprop': ['text']})][0]
#lines = [a.text.strip() for a in soup.find_all("div", {'id': ['azindex-1']})[0]
#lines = soup.find("div", {"id": ["wrapper"], "class": ["box-story"]})
#lines = soup.find_all("div", {"id": ["main"]})
lines = soup.find_all()
 
#.findAll("a")
print(lines)

#title = [a.text.strip() for a in soup.find_all("h2", {'itemprop': ['name']})][0]
#print(title)

#genre = [a.text.strip() for a in soup.find_all("span", {'itemprop': ['genre']})][0]
#print(genre)

#title = title.replace(genre, '')
#ondertitle = [a.text.strip() for a in soup.find_all("div", {'class': ['subtitle']})][0]
#print(ondertitle)

print(index)