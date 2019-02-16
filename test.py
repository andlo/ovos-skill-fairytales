import requests
from bs4 import BeautifulSoup


url = 'https://www.andersenstories.com/da/andersen_fortaellinger/list'
soup = BeautifulSoup(requests.get(url).text, "html.parser")
index = {}
#print(soup)

for link in soup.find_all("a"):
    #print(link.get('href'))
    #print(link.text)
    index.update({link.text: link.get("href")})
#print(index)


url = 'https://www.andersenstories.com/da/andersen_fortaellinger/fyrtojet'
r = requests.get(url)
r.encoding = r.apparent_encoding
soup = BeautifulSoup(r.text, "html.parser")

lines = [a.text.strip() for a in soup.find_all('div', {'class': ['text']})][0]

#lines = [l for l in lines if not l.startswith("{") and not l.endswith("}")]
#print(lines)

title = [a.text.strip() for a in soup.findAll("h1", {'itemprop': ['name']})][0]
genre = [a.text.strip() for a in soup.findAll("span", {'itemprop': ['genre']})][0]
title = title.replace(genre, '')
ondertitle = [a.text.strip() for a in soup.find_all('span', {'itemprop': ['headline']})][0]

print(title)
print(genre)
print(ondertitle)
