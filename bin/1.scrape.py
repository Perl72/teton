import requests
from bs4 import BeautifulSoup

url = "https://www.deseret.com/2019/2/4/20664993/tim-ballard-i-ve-fought-sex-trafficking-at-the-border-this-is-why-we-need-a-wall/"

# Fetch the webpage
headers = {"User-Agent": "Mozilla/5.0"}
response = requests.get(url, headers=headers)

if response.status_code != 200:
    raise Exception(f"Failed to fetch page: {response.status_code}")

# Parse the HTML
soup = BeautifulSoup(response.text, "html.parser")

# Extract main content (assuming it's within <article>)
article = soup.find("article")
text = article.get_text("\n", strip=True) if article else "No article found"

# Save to file
with open("page.txt", "w", encoding="utf-8") as f:
    f.write(text)

print("Content saved to page.txt")
