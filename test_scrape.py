import urllib.request
import re

url = "https://github.com/users/suchirreddy/contributions"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as response:
    html = response.read().decode('utf-8')

print("TDs:")
for match in list(re.finditer(r'<td[^>]*class="[^"]*ContributionCalendar-day[^"]*"[^>]*>', html))[:5]:
    print(match.group(0))
    
print("\nTooltips:")
for match in list(re.finditer(r'<tool-tip[^>]*>(.*?)</tool-tip>', html))[:5]:
    print(match.group(0))

