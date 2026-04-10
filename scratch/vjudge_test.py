import requests
import re
import time

def test_vjudge(cf_id):
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    
    # Step 1: Get problem page to find internal ID
    url = f"https://vjudge.net/problem/Codeforces-{cf_id}"
    print(f"Fetching: {url}")
    r = session.get(url)
    if r.status_code != 200:
        print(f"Failed to fetch VJudge page: {r.status_code}")
        return

    # Find ID in JSON-like data in HTML
    match = re.search(r'"id":(\d+)', r.text)
    if not match:
        print("Could not find internal ID in HTML")
        # Try finding it in description URL if available
        return
    
    internal_id = match.group(1)
    print(f"Found internal ID: {internal_id}")

    # Step 2: Fetch description via AJAX
    # VJudge uses this endpoint for description
    desc_url = f"https://vjudge.net/problem/viewProblemDes/{internal_id}"
    print(f"Fetching description: {desc_url}")
    r = session.get(desc_url)
    if r.status_code == 200:
        print("SUCCESS! Description fetched.")
        print(r.text[:5000])
    else:
        print(f"Failed to fetch description: {r.status_code}")

def test_vjudge_with_id(internal_id):
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    desc_url = f"https://vjudge.net/problem/viewProblemDes/{internal_id}"
    print(f"Fetching description: {desc_url}")
    r = session.get(desc_url)
    if r.status_code == 200:
        print("SUCCESS! Description fetched.")
        print(r.text[:5000])
    else:
        print(f"Failed to fetch description: {r.status_code}")

if __name__ == "__main__":
    # Test with known ID for 4A
    test_vjudge_with_id("19984")
