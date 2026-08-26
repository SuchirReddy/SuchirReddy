import urllib.request
import urllib.error
import json
import os
from datetime import datetime, timezone

def get_todays_commits(username):
    # Get today's date in YYYY-MM-DD format
    today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    url = f"https://api.github.com/search/commits?q=author:{username}+committer-date:{today_str}"
    
    headers = {
        'Accept': 'application/vnd.github.cloak-preview',
        'User-Agent': 'commit-counter-script'
    }
    
    token = os.environ.get('GITHUB_TOKEN')
    if token:
        headers['Authorization'] = f'token {token}'
        
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data.get('total_count', 0)
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}")
        if e.code == 422:
            print("Validation failed, query might be incorrect.")
        elif e.code == 403:
            print("Rate limited or forbidden. Check GITHUB_TOKEN.")
        return 0
    except Exception as e:
        print(f"Error fetching commits: {e}")
        return 0

def update_svg(commits_count):
    template_path = 'spiderman-swing.template.svg'
    output_path = 'spiderman-swing.svg'
    
    try:
        with open(template_path, 'r') as f:
            svg_content = f.read()
            
        # Replace the placeholder with the actual commit count
        # If it's 0, we can still show 0 or something else, but 0 is fine
        updated_content = svg_content.replace('{{TODAYS_COMMITS}}', str(commits_count))
        
        with open(output_path, 'w') as f:
            f.write(updated_content)
            
        print(f"Successfully updated {output_path} with {commits_count} commits.")
    except Exception as e:
        print(f"Error updating SVG: {e}")

if __name__ == "__main__":
    username = "suchirreddy"
    print(f"Fetching today's commits for {username}...")
    commits = get_todays_commits(username)
    print(f"Found {commits} commits today.")
    update_svg(commits)
