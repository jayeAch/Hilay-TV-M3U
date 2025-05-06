import requests

# Replace this with your actual M3U URL
m3u_url = 'https://hilaytvm3u.dhck.workers.dev/hilaytv.m3u'

try:
    response = requests.get(m3u_url)
    response.raise_for_status()
    m3u_content = response.text

    filename = 'hilaytv.m3u'
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(m3u_content)

    print(f"\nM3U playlist downloaded and saved as: {filename}")
    print(f"Total size: {len(m3u_content)} characters")

except requests.RequestException as e:
    print(f"Error fetching M3U playlist: {e}")
