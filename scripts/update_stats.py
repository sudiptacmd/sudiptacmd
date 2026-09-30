"""Refresh profile assets from public GitHub endpoints, using only the standard library."""
import datetime
import html
import json
import os
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
USER = 'sudiptacmd'


def fetch(path):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'sudiptacmd-profile'}
    if os.environ.get('GH_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GH_TOKEN']
    request = urllib.request.Request('https://api.github.com/' + path, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def main():
    user = fetch(f'users/{USER}')
    repos = []
    page = 1
    while True:
        batch = fetch(f'users/{USER}/repos?type=owner&per_page=100&page={page}')
        repos.extend(r for r in batch if not r.get('private', False))
        if len(batch) < 100:
            break
        page += 1
    originals = [r for r in repos if not r['fork']]
    stars = sum(r['stargazers_count'] for r in originals)
    since = datetime.datetime.fromisoformat(user['created_at'].replace('Z', '+00:00')).date()
    today = datetime.datetime.now(datetime.timezone.utc).date()
    days = (today - since).days
    stats = [(f'{days:,}', 'DAYS ON GITHUB'), (str(len(repos)), 'PUBLIC REPOS'),
             (str(stars), 'STARS EARNED'), (str(user['followers']), 'FOLLOWERS')]
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="200" viewBox="0 0 1200 200" role="img" aria-labelledby="title">',
           '<title id="title">Public GitHub stats, updated ' + str(today) + '</title>',
           '<rect x="1" y="1" width="1198" height="198" rx="16" fill="#0c191e" stroke="#28454c"/>']
    for i, (value, label) in enumerate(stats):
        x = 38 + i * 295
        if i:
            svg.append(f'<path d="M{x-20} 35V137" stroke="#28454c"/>')
        svg.append(f'<text x="{x}" y="87" fill="#75f5bd" font-family="monospace" font-size="44">{html.escape(value)}</text>')
        svg.append(f'<text x="{x}" y="121" fill="#b1c8cd" font-family="monospace" font-size="13">{label}</text>')
    svg.append(f'<text x="38" y="173" fill="#819ea5" font-family="monospace" font-size="12">PUBLIC DATA / {today} UTC / STARS EXCLUDE FORKS</text></svg>')
    (ROOT / 'assets/stats.svg').write_text('\n'.join(svg) + '\n')
    summary = f'Updated {today} (UTC). Public data only.\n\n'
    summary += '\n'.join(f'- {label.title()}: **{value}**' for value, label in stats)
    summary += f'\n\nJoined {since}. Stars count owned public repositories, excluding forks.'
    readme = ROOT / 'README.md'
    before, rest = readme.read_text().split('<!-- STATS:START -->', 1)
    _, after = rest.split('<!-- STATS:END -->', 1)
    readme.write_text(before + '<!-- STATS:START -->\n' + summary + '\n<!-- STATS:END -->' + after)


if __name__ == '__main__':
    main()
