import datetime
import calendar
import json
import os
import re
import urllib.request

USERNAME = os.environ.get('USER_NAME', 'DarulQutni-Q')
BIRTHDAY = datetime.date(2007, 10, 17)
SVG_PATH = os.path.join(os.path.dirname(__file__), 'profile.svg')

def calculate_uptime(birthday, today=None):
    if today is None:
        today = datetime.date.today()
        
    years = today.year - birthday.year
    months = today.month - birthday.month
    days = today.day - birthday.day

    if days < 0:
        prev_month = today.month - 1 if today.month > 1 else 12
        prev_year = today.year if today.month > 1 else today.year - 1
        _, num_days_prev = calendar.monthrange(prev_year, prev_month)
        days += num_days_prev
        months -= 1

    if months < 0:
        months += 12
        years -= 1

    def plural(n, word):
        return f"{n} {word}" if n == 1 else f"{n} {word}s"

    return f"{plural(years, 'year')}, {plural(months, 'month')}, {plural(days, 'day')}"

def fetch_github_stats(username):
    token = os.environ.get('GITHUB_TOKEN') or os.environ.get('ACCESS_TOKEN')
    headers = {'User-Agent': 'Profile-Updater'}
    if token:
        headers['Authorization'] = f'Bearer {token}'

    stats = {}
    try:
        # User profile
        req = urllib.request.Request(f'https://api.github.com/users/{username}', headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            stats['repos'] = data.get('public_repos', 0)
            stats['followers'] = data.get('followers', 0)
            stats['following'] = data.get('following', 0)
            
        # Total stars
        req_repos = urllib.request.Request(f'https://api.github.com/users/{username}/repos?per_page=100', headers=headers)
        with urllib.request.urlopen(req_repos, timeout=15) as resp:
            repos_data = json.loads(resp.read().decode())
            stats['stars'] = sum(repo.get('stargazers_count', 0) for repo in repos_data)
    except Exception as e:
        print(f"Warning: Could not fetch stats from GitHub API: {e}")
        return None

    return stats

def update_svg():
    if not os.path.exists(SVG_PATH):
        print(f"Error: {SVG_PATH} not found.")
        return

    with open(SVG_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    uptime = calculate_uptime(BIRTHDAY)
    print(f"Current uptime calculated: {uptime}")

    # Replace Uptime
    uptime_pattern = r'(<tspan[^>]*class="key">Uptime</tspan><tspan[^>]*>[^<]*</tspan><tspan class="value">)(.*?)(</tspan>)'
    content = re.sub(uptime_pattern, rf'\g<1>{uptime}\g<3>', content)

    # Fetch and replace GitHub Stats if available
    stats = fetch_github_stats(USERNAME)
    if stats:
        print(f"Fetched stats: {stats}")
        stats_pattern = (
            r'(<tspan[^>]*class="key">Repos</tspan><tspan[^>]*>: </tspan><tspan class="value">)\d+(</tspan>.*?'
            r'<tspan[^>]*class="key">Stars</tspan><tspan[^>]*>: </tspan><tspan class="value">)\d+(</tspan>.*?'
            r'<tspan[^>]*class="key">Followers</tspan><tspan[^>]*>: </tspan><tspan class="value">)\d+(</tspan>.*?'
            r'<tspan[^>]*class="key">Following</tspan><tspan[^>]*>: </tspan><tspan class="value">)\d+(</tspan>)'
        )
        replacement = (
            rf'\g<1>{stats["repos"]}\g<2>'
            rf'{stats["stars"]}\g<3>'
            rf'{stats["followers"]}\g<4>'
            rf'{stats["following"]}\g<5>'
        )
        content = re.sub(stats_pattern, replacement, content)

    with open(SVG_PATH, 'w', encoding='utf-8') as f:
        f.write(content)

    print("profile.svg successfully updated!")

if __name__ == '__main__':
    update_svg()
