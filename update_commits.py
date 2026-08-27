import urllib.request
import urllib.error
import json
import os
from datetime import datetime, timezone

def get_stats(username):
    # To get private commits, the user MUST provide a Personal Access Token (PAT)
    pat_token = os.environ.get('PAT_TOKEN')
    
    today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    # 1. Fetch Today's Commits (Real-time via Search API)
    # The GraphQL contributionCalendar is often heavily cached and delayed by hours.
    # The search API provides up-to-the-minute accuracy.
    todays_commits = 0
    search_url = f"https://api.github.com/search/commits?q=author:{username}+committer-date:{today_str}"
    headers = {
        'Accept': 'application/vnd.github.cloak-preview',
        'User-Agent': 'commit-counter-script'
    }
    
    if pat_token:
        # Pass the PAT token to search private repositories as well
        headers['Authorization'] = f'token {pat_token}'
        
    try:
        req = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            todays_commits = data.get('total_count', 0)
    except Exception as e:
        print(f"Error fetching real-time today's commits: {e}")

    # 2. Fetch Streak and Total Commits
    streak = 0
    total_commits = 0
    
    if pat_token:
        # Use GraphQL API with PAT to get private commits
        gql_headers = {
            'Authorization': f'Bearer {pat_token}',
            'Content-Type': 'application/json'
        }
        graphql_url = "https://api.github.com/graphql"
        query = """
        query($userName:String!) {
          user(login: $userName){
            contributionsCollection {
              contributionCalendar {
                totalContributions
                weeks {
                  contributionDays {
                    contributionCount
                    date
                  }
                }
              }
            }
          }
        }
        """
        payload = {
            "query": query,
            "variables": {"userName": username}
        }
        
        try:
            req = urllib.request.Request(graphql_url, data=json.dumps(payload).encode('utf-8'), headers=gql_headers)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                calendar = data['data']['user']['contributionsCollection']['contributionCalendar']
                
                total_commits = calendar['totalContributions']
                
                days = []
                for week in calendar['weeks']:
                    days.extend(week['contributionDays'])
                
                # Calculate streak
                days.reverse()
                current_streak = 0
                for day in days:
                    count = day['contributionCount']
                    date = day['date']
                    if count > 0:
                        current_streak += 1
                    elif date == today_str:
                        continue
                    elif date > today_str:
                        continue
                    else:
                        break
                        
                streak = current_streak
                return todays_commits, streak, total_commits
        except Exception as e:
            print(f"Error fetching private stats with PAT: {e}")
            print("Falling back to public scraper...")

    # Fallback: Public Web Scraper (Public commits only)
    todays_commits = 0
    streak = 0
    total_commits = 0
    
    try:
        # Get today's commits via search (public only)
        search_url = f"https://api.github.com/search/commits?q=author:{username}+committer-date:{today_str}"
        headers = {'User-Agent': 'commit-counter-script'}
        req = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            todays_commits = data.get('total_count', 0)
    except Exception as e:
        print(f"Error fetching public today's commits: {e}")

    try:
        import re
        url = f"https://github.com/users/{username}/contributions"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            
        total_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s+contributions\s+in\s+the\s+last\s+year', html)
        if total_match:
            total_commits = int(total_match.group(1).replace(',', ''))
            
        td_tags = re.findall(r'<td[^>]*class="[^"]*ContributionCalendar-day[^"]*"[^>]*>', html)
        date_by_id = {}
        for td in td_tags:
            id_m = re.search(r'id="([^"]+)"', td)
            date_m = re.search(r'data-date="([^"]+)"', td)
            if id_m and date_m:
                date_by_id[id_m.group(1)] = date_m.group(1)
        
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
                    
        sorted_dates = sorted(contributions.keys(), reverse=True)
        current_streak = 0
        for date in sorted_dates:
            count = contributions[date]
            if count > 0:
                current_streak += 1
            elif date == today_str:
                continue
            elif date > today_str:
                continue
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
