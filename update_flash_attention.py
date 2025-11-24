#!/usr/bin/env python3
import requests
import re
from pathlib import Path
import sys

REPO = "mjun0812/flash-attention-prebuild-wheels"
OUTPUT_FILE = Path(__file__).parent / "flash_attention.txt"

def get_all_releases(repo):
    releases = []
    page = 1
    while True:
        url = f"https://api.github.com/repos/{repo}/releases?page={page}&per_page=100"
        print(f"Fetching page {page}...")
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            if not data:
                break
            releases.extend(data)
            page += 1
        except Exception as e:
            print(f"Error fetching releases: {e}")
            break
    return releases

def parse_wheel_filename(filename):
    # Example: flash_attn-2.8.1+cu128torch2.9-cp310-cp310-linux_x86_64.whl
    # Regex to capture python tag and platform tag
    # We look for -cp<ver>-cp<ver>-<platform>.whl
    match = re.search(r'-cp(\d{2,})-cp\d+-(.+)\.whl$', filename)
    if not match:
        return None, None
    
    py_tag = match.group(1) # e.g. 310
    platform_tag = match.group(2) # e.g. linux_x86_64, win_amd64
    
    # Convert py_tag to python_version
    # 310 -> 3.10, 38 -> 3.8
    if len(py_tag) >= 3:
        py_ver = f"{py_tag[0]}.{py_tag[1:]}"
    else:
        py_ver = f"{py_tag[0]}.{py_tag[1:]}" # This logic is same, but for 38 it becomes 3.8
        
    # Convert platform_tag to sys_platform
    if 'win' in platform_tag:
        sys_platform = 'win32'
    elif 'linux' in platform_tag:
        sys_platform = 'linux'
    elif 'macosx' in platform_tag:
        sys_platform = 'darwin'
    else:
        sys_platform = None
        
    return py_ver, sys_platform

def main():
    print(f"Fetching releases from {REPO}...")
    releases = get_all_releases(REPO)
    print(f"Found {len(releases)} releases.")
    
    lines = []
    lines.append(f"# Auto-generated from {REPO}")
    
    count = 0
    for release in releases:
        for asset in release.get('assets', []):
            name = asset['name']
            if not name.endswith('.whl'):
                continue
                
            url = asset['browser_download_url']
            py_ver, sys_platform = parse_wheel_filename(name)
            
            if py_ver and sys_platform:
                # Construct the line
                # flash-attn @ url ; sys_platform == '...' and python_version == '...'
                line = f"flash-attn @ {url} ; sys_platform == '{sys_platform}' and python_version == '{py_ver}'"
                lines.append(line)
                count += 1
            else:
                # print(f"Skipping {name} (could not parse tags)")
                pass

    print(f"Generated {count} entries.")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
        f.write('\n')
        
    print(f"Wrote to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
