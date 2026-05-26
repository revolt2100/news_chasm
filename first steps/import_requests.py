import requests
from bs4 import BeautifulSoup
import re
import time

print("--- Script Initialized ---")

def get_holod_articles_hybrid():
    # Configuration
    base_url = "https://holod.media/obshhestvo/"
    api_url = "https://holod.media/wp-json/wp/v2"
    category_slug = "obshhestvo"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # Storage for results
    all_links = []
    seen_urls = set()

    # ==========================================
    # METHOD 1: Try WordPress REST API (Fast)
    # ==========================================
    print(f"\n[Method 1] Attempting API connection to find category '{category_slug}'...")

    try:
        # Step 1: Get Category ID
        cat_req = requests.get(f"{api_url}/categories", params={"slug": category_slug}, headers=headers, timeout=10)

        if cat_req.status_code == 200 and cat_req.json():
            cat_data = cat_req.json()[0]
            cat_id = cat_data['id']
            cat_name = cat_data['name']
            print(f"   -> Success! Found Category ID: {cat_id} ({cat_name})")

            # Step 2: Loop through API pages
            page = 1
            print("   -> Downloading article lists from API...")
            while True:
                # Fetch 50 posts at a time
                posts_req = requests.get(
                    f"{api_url}/posts",
                    params={"categories": cat_id, "per_page": 50, "page": page},
                    headers=headers,
                    timeout=15
                )

                if posts_req.status_code != 200:
                    print(f"   -> API Page {page} returned status {posts_req.status_code}. Stopping API.")
                    break

                posts = posts_req.json()
                if not posts:
                    print("   -> No more posts found (API finished).")
                    break

                new_count = 0
                for post in posts:
                    link = post.get('link')
                    if link and link not in seen_urls:
                        seen_urls.add(link)
                        all_links.append(link)
                        new_count += 1

                print(f"      Page {page}: Found {new_count} new articles.")

                # Safety break if we aren't finding anything new (prevents infinite loop)
                if new_count == 0:
                    break

                page += 1
                time.sleep(0.5)

            return all_links # Return immediately if API worked

        else:
            print("   -> API Category check failed (Status not 200 or empty). Switching to HTML.")

    except Exception as e:
        print(f"   -> API Method failed with error: {e}")
        print("   -> Switching to Method 2 (HTML Scraping)...")


    # ==========================================
    # METHOD 2: HTML Page Iteration (Fallback)
    # ==========================================
    print(f"\n[Method 2] Starting HTML Page Scrape for {base_url}")

    page = 1
    consecutive_empty_pages = 0

    while True:
        # Build URL: Page 1 is base_url, Page 2 is /page/2/
        if page == 1:
            target_url = base_url
        else:
            target_url = f"{base_url}page/{page}/"

        print(f"   -> Scanning Page {page}...", end=" ")

        try:
            r = requests.get(target_url, headers=headers, timeout=15)

            # Stop on 404 or redirects (usually means end of content)
            if r.status_code == 404:
                print("Status 404 (End of content).")
                break
            if r.url != target_url and page > 1:
                print("Redirected (End of content).")
                break
            if r.status_code != 200:
                print(f"Status {r.status_code}. Skipping.")
                page += 1
                continue

            soup = BeautifulSoup(r.text, 'html.parser')

            # --- CRITICAL: Remove "Most Read" Section ---
            # We look for the header "Самое читаемое" and remove its parent container
            ignored_count = 0
            most_read_header = soup.find(string=re.compile("Самое читаемое"))
            if most_read_header:
                # Traverse up to find the wrapper (usually a div or section)
                # We try to find a parent that looks like a sidebar or widget
                parent = most_read_header.find_parent(['div', 'aside', 'section'])
                if parent:
                    # Count how many links we are about to delete (for debug)
                    ignored_count = len(parent.find_all('a'))
                    # Remove it from the soup completely
                    parent.decompose()

            # --- Extract Links ---
            found_on_page = 0
            # Use 'main' tag if available to avoid footer/header links
            content_area = soup.find('main') or soup

            for a in content_area.find_all('a', href=True):
                href = a['href']

                # Normalize URL
                if href.startswith('/'):
                    href = "https://holod.media" + href

                # Filter Logic
                if "holod.media" not in href: continue

                # Skip nav/tag/category links
                if any(x in href for x in ['/tag/', '/category/', '/author/', '/page/', '#']):
                    continue

                # Skip the main page itself
                if href.strip('/') == base_url.strip('/'): continue

                # Heuristic: Articles usually have a date or long slug
                # e.g., /2024/01/01/slug or /slug-is-long
                path = href.replace("https://holod.media", "")

                # Check for year in path OR sufficient length
                has_year = bool(re.search(r'/\d{4}/', path))
                is_long_slug = len(path) > 15

                if (has_year or is_long_slug) and href not in seen_urls:
                    seen_urls.add(href)
                    all_links.append(href)
                    found_on_page += 1

            print(f"Added {found_on_page} articles. (Ignored {ignored_count} in 'Most Read')")

            # Stop condition for HTML loop
            if found_on_page == 0:
                consecutive_empty_pages += 1
                if consecutive_empty_pages >= 2:
                    print("   -> No articles found on 2 consecutive pages. Stopping.")
                    break
            else:
                consecutive_empty_pages = 0

            page += 1
            time.sleep(1) # Polite delay

        except Exception as e:
            print(f"\nError on page {page}: {e}")
            break

    return all_links

# --- Run the function ---
final_links = get_holod_articles_hybrid()

print("\n" + "="*40)
print(f"DONE. Total unique articles found: {len(final_links)}")
print("="*40)

# Print first 20 links as a preview
for i, link in enumerate(final_links[:20], 1):
    print(f"{i}. {link}")

    import requests
from bs4 import BeautifulSoup
import json
import time

# ==============================================================================
# 1. PASTE YOUR LIST OF URLS HERE
# ==============================================================================
article_urls = final_links

# ==============================================================================
# 2. CONFIGURATION
# ==============================================================================
OUTPUT_FILE = "holod_society_articles.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def extract_article_data(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            print(f"Error {response.status_code}: {url}")
            return None

        soup = BeautifulSoup(response.content, 'html.parser')

        # --- STEP 1: CHECK FOR 'ОБЩЕСТВО' TAG ---
        # We use three checks to be absolutely sure we don't skip valid articles.
        is_society = False
        
        # Check A: Body/Article Classes (The most reliable WordPress method)
        # WordPress usually adds 'category-obshhestvo' or 'category-society' to the body tag
        body_classes = " ".join(soup.body.get('class', [])) if soup.body else ""
        article_classes = ""
        article_tag = soup.find('article')
        if article_tag:
            article_classes = " ".join(article_tag.get('class', []))
            
        if "obshhestvo" in body_classes or "obshhestvo" in article_classes:
            is_society = True
        
        # Check B: Look for the text "Общество" specifically ABOVE the title (visual check)
        if not is_society:
            h1 = soup.find('h1')
            if h1:
                # We traverse up 3 levels and check text of previous siblings
                # This catches breadcrumbs or "Kickers" sitting above the headline
                search_zone = h1.find_all_previous(string=True, limit=50)
                # Join the closest 50 strings found before the title
                header_text = " ".join(search_zone)
                if "Общество" in header_text:
                    is_society = True

        # Check C: Check metadata JSON (Google/SEO data)
        if not is_society:
            for script in soup.find_all('script', type='application/ld+json'):
                if script.string and ('"articleSection":"Общество"' in script.string or '"articleSection":["Общество"]' in script.string):
                    is_society = True
                    break

        # Check D: Loose link check (Final Fallback)
        # Look for any link with text "Общество" that isn't in the footer/sidebar
        if not is_society:
            for a in soup.find_all('a', href=True):
                if "Общество" in a.get_text(strip=True):
                    # Exclude if it's likely a menu item or footer
                    parent_cls = " ".join(a.parent.get('class', []))
                    if "menu" not in parent_cls and "footer" not in parent_cls:
                        # Check if it's in the top half of the HTML
                        if str(a) in str(soup)[:len(str(soup))//2]:
                            is_society = True
                            break

        if not is_society:
            print(f"Skipping (Not 'Общество'): {url}")
            return None


        # --- STEP 2: EXTRACT DATA ---
        
        # 1. Title
        h1 = soup.find('h1')
        title = h1.get_text(strip=True) if h1 else ""

        # 2. Date
        date = ""
        # Try meta tag first (ISO format)
        meta_date = soup.find('meta', property='article:published_time')
        if meta_date:
            date = meta_date.get('content')
        else:
            # Fallback to visual time tag
            time_tag = soup.find('time')
            if time_tag:
                date = time_tag.get('datetime') or time_tag.get_text(strip=True)

        # 3. Images
        images = []
        # Main Social Image
        og_img = soup.find('meta', property='og:image')
        if og_img:
            images.append(og_img.get('content'))

        # 4. Text Content (Apart from title)
        text_content = ""
        # Find the main content container
        content_div = soup.find('div', class_='entry-content') or \
                      soup.find('div', class_='post-content') or \
                      soup.find('article')
        
        if content_div:
            # Get images from content before we clean it
            for img in content_div.find_all('img'):
                src = img.get('src')
                if src and src.startswith('http') and src not in images:
                    images.append(src)
            
            # Create a clean copy for text extraction
            clean_div = BeautifulSoup(str(content_div), 'html.parser')
            
            # Remove H1 (Title)
            if clean_div.find('h1'):
                clean_div.find('h1').decompose()
            
            # Remove unwanted elements (scripts, ads, "read also" blocks)
            for junk in clean_div(['script', 'style', 'iframe', 'aside', 'button']):
                junk.decompose()
                
            # Remove "Read Also" links that might be inserted in text
            for div in clean_div.find_all('div', class_=lambda x: x and 'read-also' in x):
                div.decompose()

            # Extract text with spacing
            text_content = clean_div.get_text(separator='\n\n', strip=True)

        # Build Dictionary
        entry = {
            "URL": url,
            "Title": title,
            "Text": text_content,
            "Images": images,
            "Date": date,
            "Language": "RU",
            "Newspaper": "Holod"
        }
        
        print(f"Processed: {title[:40]}...")
        return entry

    except Exception as e:
        print(f"Error processing {url}: {e}")
        return None

# ==============================================================================
# 3. RUNNER
# ==============================================================================
if __name__ == "__main__":
    final_data = []
    
    print(f"Starting processing of {len(article_urls)} articles...")
    
    for url in article_urls:
        data = extract_article_data(url)
        if data:
            final_data.append(data)
        time.sleep(0.5) # Polite delay
        
    # Save to JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)
        
    print(f"\nCompleted. Saved {len(final_data)} articles to '{OUTPUT_FILE}'.")