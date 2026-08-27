import urllib.request
import urllib.error
import json
import os
from datetime import datetime, timezone

def get_stats(username):
    token = os.environ.get('GITHUB_TOKEN')
    
    # We will still get today's commits via the search API to be accurate to the minute 
    # without relying on timezone offsets in the calendar
    today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    search_url = f"https://api.github.com/search/commits?q=author:{username}+committer-date:{today_str}"
    
    headers = {
        'Accept': 'application/vnd.github.cloak-preview',
        'User-Agent': 'commit-counter-script'
    }
    
    if token:
        headers['Authorization'] = f'token {token}'
        
    todays_commits = 0
    try:
        req = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            todays_commits = data.get('total_count', 0)
    except Exception as e:
        print(f"Error fetching today's commits: {e}")

    # For Streak and Total, we scrape the public contributions graph
    # This avoids GITHUB_TOKEN permission issues entirely
    streak = 0
    total_commits = 0
    
    try:
        import re
        url = f"https://github.com/users/{username}/contributions"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            
        # 1. Parse total contributions
        total_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s+contributions\s+in\s+the\s+last\s+year', html)
        if total_match:
            total_commits = int(total_match.group(1).replace(',', ''))
            
        # 2. Parse daily contributions for streak
        td_pattern = re.compile(r'<td[^>]*id="([^"]+)"[^>]*data-date="([^"]+)"')
        tds = td_pattern.findall(html)
        date_by_id = {tid: date for tid, date in tds}
        
        tooltip_pattern = re.compile(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]+)</tool-tip>')
        tooltips = tooltip_pattern.findall(html)
        
        contributions = {}
        for tid, text in tooltips:
            if tid in date_by_id:
                count_match = re.search(r'^(\d+|No)\s+contribution', text.strip())
                if count_match:
                    count_str = count_match.group(1)
                    count = 0 if count_str == 'No' else int(count_str)
                    contributions[date_by_id[tid]] = count
                    
        # Calculate streak
        sorted_dates = sorted(contributions.keys(), reverse=True)
        current_streak = 0
        for date in sorted_dates:
            count = contributions[date]
            if count > 0:
                current_streak += 1
            elif date == today_str:
                continue # 0 commits today doesn't break yesterday's streak yet
            else:
                break
                
        streak = current_streak

    except Exception as e:
        print(f"Error scraping GitHub contributions: {e}")
        
    return todays_commits, streak, total_commits

def update_counter_svg(title, value, output_filename):
    template_path = 'web-counter.template.svg'
    try:
        with open(template_path, 'r') as f:
            svg_content = f.read()
            
        updated = svg_content.replace('{{TITLE}}', title).replace('{{VALUE}}', str(value))
        
        with open(output_filename, 'w') as f:
            f.write(updated)
        print(f"Generated {output_filename} with {title}: {value}")
    except Exception as e:
        print(f"Error updating counter SVG {output_filename}: {e}")

def update_swing_svg(commits_count):
    template_path = 'spiderman-swing.template.svg'
    output_path = 'spiderman-swing.svg'
    try:
        with open(template_path, 'r') as f:
            svg_content = f.read()
            
        updated_content = svg_content.replace('{{TODAYS_COMMITS}}', str(commits_count))
        
        with open(output_path, 'w') as f:
            f.write(updated_content)
            
        print(f"Successfully updated {output_path} with {commits_count} commits.")
    except Exception as e:
        print(f"Error updating SVG: {e}")

if __name__ == "__main__":
    username = "suchirreddy"
    print(f"Fetching stats for {username}...")
    t_commits, streak, tot_commits = get_stats(username)
    print(f"Today: {t_commits}, Streak: {streak}, Total: {tot_commits}")
    
    update_swing_svg(t_commits)
    
    update_counter_svg("TODAY", t_commits, "web-today.svg")
    update_counter_svg("STREAK", streak, "web-streak.svg")
    update_counter_svg("TOTAL", tot_commits, "web-total.svg")
