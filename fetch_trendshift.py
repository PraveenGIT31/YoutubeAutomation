import os
import json
import urllib.request
from bs4 import BeautifulSoup

PROCESSED_REPOS_FILE = 'processed_repos.json'

def load_processed_repos():
    if not os.path.exists(PROCESSED_REPOS_FILE):
        return []
    with open(PROCESSED_REPOS_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_processed_repo(repo_url):
    repos = load_processed_repos()
    if repo_url not in repos:
        repos.append(repo_url)
        with open(PROCESSED_REPOS_FILE, 'w') as f:
            json.dump(repos, f, indent=4)

def get_repo_description(owner, repo):
    try:
        req = urllib.request.Request(
            f'https://api.github.com/repos/{owner}/{repo}',
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        response = urllib.request.urlopen(req).read()
        data = json.loads(response)
        return data.get('description', 'No description provided.')
    except Exception as e:
        print(f"Failed to fetch description for {owner}/{repo}: {e}")
        return "A trending GitHub repository."

def fetch_unprocessed_trending_repo():
    """
    Scrapes trendshift.io for trending repositories and returns the first one
    that hasn't been processed yet, along with its description.
    """
    print("Fetching trending repositories from trendshift.io...")
    req = urllib.request.Request(
        'https://trendshift.io/', 
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    
    try:
        html = urllib.request.urlopen(req).read()
    except Exception as e:
        print(f"Failed to fetch trendshift.io: {e}")
        return None, None, None

    soup = BeautifulSoup(html, 'html.parser')
    trending_repos = []
    
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/repositories/' in href:
            text = a.get_text(strip=True)
            if '/' in text and ' ' not in text:
                trending_repos.append(text)

    # Remove duplicates but preserve order (roughly trending order)
    seen = set()
    ordered_repos = []
    for r in trending_repos:
        if r not in seen:
            seen.add(r)
            ordered_repos.append(r)

    processed_repos = set(load_processed_repos())
    
    for repo in ordered_repos:
        repo_url = f"https://github.com/{repo}"
        if repo_url not in processed_repos:
            print(f"Found new trending repo: {repo}")
            owner, repo_name = repo.split('/')
            description = get_repo_description(owner, repo_name)
            return repo_url, repo, description
            
    print("No new trending repositories found.")
    return None, None, None

if __name__ == "__main__":
    url, name, desc = fetch_unprocessed_trending_repo()
    if url:
        print(f"URL: {url}")
        print(f"Name: {name}")
        print(f"Description: {desc}")
