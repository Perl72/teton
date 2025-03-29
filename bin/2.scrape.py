import requests
from bs4 import BeautifulSoup

def extract_editorial_content(url):
    """Fetch and extract the main editorial content from a webpage."""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return "Failed to fetch the webpage."

    soup = BeautifulSoup(response.text, "lxml")

    # Remove unwanted elements
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.extract()

    # Try to locate main article content
    main_content = soup.find("article") or soup.find("div", {"id": "main-content"}) or soup.find("div", {"class": "content"})

    if main_content:
        return main_content.get_text("\n", strip=True)

    # Fallback: Extract first 10 paragraphs
    paragraphs = soup.find_all("p")
    return "\n\n".join(p.get_text(strip=True) for p in paragraphs[:80])  # Get first 10 paragraphs

# Example usage 
#url = "https://www.deseret.com/2019/2/4/20664993/tim-ballard-i-ve-fought-sex-trafficking-at-the-border-this-is-why-we-need-a-wall/"
#url = "https://www.foxnews.com/opinion/ive-fought-sex-trafficking-as-a-dhs-special-agent-we-need-to-build-the-wall-for-the-children"

url = "https://www.presidency.ucsb.edu/documents/remarks-meeting-human-trafficking-the-mexico-united-states-border-and-exchange-with?utm_source=chatgpt.com"
content = extract_editorial_content(url)
print(content)

# Save to file
with open("2019.txt", "w", encoding="utf-8") as f:
    f.write(content)





