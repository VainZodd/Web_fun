from bs4 import BeautifulSoup

with open('Nexus_News.html', 'r') as f:
    soup = BeautifulSoup(f, 'html.parser')

viz = soup.find(id='archive-stats-viz')
filters = soup.find(id='archive-filters')
search = soup.find(id='archive-search')

if viz and filters and search:
    print("Archive elements found.")
else:
    print(f"Archive elements missing: viz={viz is not None}, filters={filters is not None}, search={search is not None}")

# Check JS presence of renderArchiveStats
with open('Nexus_News.html', 'r') as f:
    content = f.read()
    if 'renderArchiveStats' in content and 'filterArchive' in content:
        print("Archive JS logic found.")
    else:
        print("Archive JS logic missing.")
