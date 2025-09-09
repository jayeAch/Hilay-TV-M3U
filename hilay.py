import requests
import json
import socket

CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)

def get_session():
    s = requests.Session()
    s.headers.update({"User-Agent": CHROME_UA})
    s.max_redirects = 5
    return s

def get_final_url(session, url):
    try:
        resp = session.head(url, allow_redirects=False, timeout=10)
        if 300 <= resp.status_code < 400 and 'Location' in resp.headers:
            return resp.headers['Location']
        return url
    except requests.exceptions.RequestException:
        return url

def generate_m3u_playlist():
    session = get_session()

    manifest_url = 'https://www.melakarnets.com/proxy/index.php?q=https://hilaytv.vercel.app/manifest.json'
    try:
        response = session.get(manifest_url, timeout=10)
        response.raise_for_status()
        manifest = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch manifest.json: {e}")
        return

    # ==================== FILTER CONFIGURATION ====================
    # Choose ONE of these filtering methods by uncommenting the desired lines
    
    # METHOD 1: Include ONLY these prefixes (whitelist)
    include_only = ["param", "USA", "wb", "usaeast", "Cartoonnetwork", "Boomerang", "HBOfamily", "HBO", "HBOComedy", "HBOZone", "HBOHits", "HBOSig", "HBO2"]
    
    # METHOD 2: Exclude these prefixes (blacklist)
    #exclude_prefixes = ["Sonyten", "SkySports", "dazn", "ESPN", "BeinSports", "SSc", "premiersp"]
    
    # METHOD 3: Filter by category keywords in channel names
    # category_keywords = ["news", "sport", "movie"]  # Channels containing these words will be included
    
    # METHOD 4: No filtering (process all channels)
    # include_only = []  # Empty list = no filtering
    # exclude_prefixes = []  # Empty list = no filtering
    # ==============================================================

    m3u_content = (
        "#EXTM3U\n"
        "# Generated from Hilay TV API\n"
        "# https://hilaytv.vercel.app/\n\n"
    )

    processed_count = 0
    skipped_count = 0
    prefixes = manifest.get('idPrefixes', [])
    total_prefixes = len(prefixes)
    
    print(f"Total prefixes found: {total_prefixes}")
    print("Starting filtering and processing...\n")

    for prefix in prefixes:
        # ==================== FILTERING LOGIC ====================
        # Apply include-only filter (whitelist)
        if 'include_only' in locals() and include_only and prefix not in include_only:
            skipped_count += 1
            continue
            
        # Apply exclude filter (blacklist)
        if 'exclude_prefixes' in locals() and exclude_prefixes:
            if any(excluded in prefix for excluded in exclude_prefixes):
                skipped_count += 1
                continue
        
        # Apply category keyword filter
        if 'category_keywords' in locals() and category_keywords:
            # We need to get the channel name first to check against keywords
            channel_url = f"https://www.melakarnets.com/proxy/index.php?q=https://hilaytv.vercel.app/stream/tv/{prefix}.mv.json"
            try:
                response = session.get(channel_url, timeout=10)
                response.raise_for_status()
                channel_data = response.json()
                
                if channel_data and channel_data.get('streams'):
                    stream = channel_data['streams'][0]
                    name = stream.get('name', prefix).lower()
                    
                    # Check if name contains any of the category keywords
                    if not any(keyword.lower() in name for keyword in category_keywords):
                        skipped_count += 1
                        continue
            except:
                # If we can't get the name, skip this channel for category filtering
                skipped_count += 1
                continue
        # =========================================================

        channel_url = f"https://www.melakarnets.com/proxy/index.php?q=https://hilaytv.vercel.app/stream/tv/{prefix}.mv.json"
        try:
            response = session.get(channel_url, timeout=10)
            response.raise_for_status()
            channel_data = response.json()

            if channel_data and channel_data.get('streams'):
                stream = channel_data['streams'][0]
                name = stream.get('name', prefix)
                original_url = stream.get('url', '')

                if not original_url:
                    print(f"Skipping {prefix}: No URL found")
                    skipped_count += 1
                    continue

                final_url = get_final_url(session, original_url)

                m3u_content += (
                    f"#EXTINF:-1 tvg-id=\"{prefix}\" tvg-name=\"{name}\" "
                    f"group-title=\"Hilay TV\",{name}\n"
                    f"{final_url}\n\n"
                )

                print(f"Processed: {name} - Original: {original_url} - Final: {final_url}")
                processed_count += 1

        except requests.exceptions.RequestException as e:
            print(f"Error processing {prefix}: {e}")
            skipped_count += 1
            continue
        except json.JSONDecodeError:
            print(f"Error decoding JSON for {prefix}")
            skipped_count += 1
            continue

    filename = 'hilaytv.m3u'
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(m3u_content)

    print(f"\nM3U playlist generated: {filename}")
    print(f"Total channels processed: {processed_count}/{total_prefixes}")
    print(f"Channels skipped by filter: {skipped_count}")
    print(f"Final playlist contains: {processed_count} channels")

if __name__ == "__main__":
    generate_m3u_playlist()
