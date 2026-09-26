#!/usr/bin/env python3
"""
Recipe Extractor - Extract recipes from websites and YouTube videos
for the Hugo-based recipe blog.

Usage:
    python extract_recipe.py <url_or_video_id> [options]
    
Examples:
    # From a website (auto-detects JSON-LD, falls back to HTML parsing)
    python extract_recipe.py https://example.com/recipe-page
    
    # From YouTube video
    python extract_recipe.py https://www.youtube.com/watch?v=VIDEO_ID
    
    # Specify source type explicitly
    python extract_recipe.py VIDEO_ID --source youtube
    
    # Custom output directory
    python extract_recipe.py https://example.com/recipe --output-dir ../content/recipes

Output:
    Creates a draft recipe file at content/recipes/<slug>.md ready for review.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime


# ============================================================================
# HTML Fetching
# ============================================================================

def fetch_webpage(url: str) -> str:
    """Fetch and return the HTML content of a webpage.
    
    Uses multiple strategies to bypass anti-bot protection:
    1. Realistic browser headers with retry logic
    2. Headless browser fallback (Playwright) if requests fails
    """
    import time
    
    # Strategy 1: Requests with realistic headers and retries
    try:
        import requests
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        
        # Try up to 3 times with exponential backoff
        for attempt in range(3):
            try:
                response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
                
                # Check if we got blocked (403/429)
                if response.status_code in [403, 429]:
                    wait_time = (2 ** attempt) + 1  # 2s, 5s, 11s
                    print(f"  Site returned {response.status_code}. Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                
                # Try to detect encoding
                if response.encoding == 'ISO-8859-1':
                    response.encoding = response.apparent_encoding
                    
                print(f"  ✓ Fetched successfully ({len(response.text)} bytes)")
                return response.text
                
            except requests.exceptions.Timeout:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                raise
                
    except ImportError:
        pass
    
    # Strategy 2: Headless browser with Playwright (if available)
    print("  Requests failed. Trying headless browser...")
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
            )
            page = context.new_page()
            
            # Navigate with timeout
            response = page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            if response and response.status == 200:
                html = page.content()
                print(f"  ✓ Fetched via Playwright ({len(html)} bytes)")
                browser.close()
                return html
            
            browser.close()
            
    except ImportError:
        print("  ⚠ Playwright not installed. Install with: pip install playwright && playwright install")
    except Exception as e:
        print(f"  ⚠ Playwright failed: {e}")
    
    # All strategies failed
    raise Exception(
        f"Failed to fetch {url}. The site may be blocking automated requests.\n\n"
        "Solutions:\n"
        "1. Copy the page content manually and paste it when prompted\n"
        "2. Install Playwright for headless browser support: pip install playwright && playwright install\n"
        "3. Use a different recipe source that doesn't block scraping"
    )


# ============================================================================
# JSON-LD Extraction (Primary Method - Most Accurate)
# ============================================================================

def extract_json_ld(html: str) -> Optional[dict]:
    """Extract Schema.org Recipe JSON-LD from HTML.
    
    This is the most reliable method when websites use structured data.
    """
    # Find all script tags with application/ld+json
    pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
    matches = re.findall(pattern, html, re.DOTALL)
    
    for match in matches:
        try:
            data = json.loads(match)
            # Handle both single object and array of objects
            if isinstance(data, list):
                for item in data:
                    if item.get('@type') == 'Recipe':
                        return item
            elif data.get('@type') == 'Recipe':
                return data
        except json.JSONDecodeError:
            continue
    
    return None


def parse_json_ld_recipe(json_data: dict) -> dict:
    """Parse JSON-LD recipe data into our blog format."""
    recipe = {
        'title': json_data.get('name', ''),
        'description': json_data.get('description', ''),
        'prep_time': _parse_duration(json_data.get('prepTime')),
        'cook_time': _parse_duration(json_data.get('cookTime')),
        'total_time': _parse_duration(json_data.get('totalTime')),
        'servings': _parse_servings(json_data.get('recipeYield')),
        'ingredients': _extract_ingredients(json_data),
        'instructions': _extract_instructions(json_data),
    }
    
    # Extract cuisine from tags or category
    tags = json_data.get('recipeCategory', [])
    if isinstance(tags, list):
        recipe['cuisine'] = tags[0] if tags else ''
    elif isinstance(tags, str):
        recipe['cuisine'] = tags
    
    return recipe


def _parse_duration(duration_str: Optional[str]) -> str:
    """Parse ISO 8601 duration (PT1H30M) to human-readable format."""
    if not duration_str:
        return ''
    
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', str(duration_str))
    if not match:
        return str(duration_str)
    
    hours, minutes, seconds = match.groups()
    parts = []
    if hours:
        parts.append(f"{hours} hour{'s' if int(hours) > 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if int(minutes) > 1 else ''}")
    if seconds:
        parts.append(f"{seconds} second{'s' if int(seconds) > 1 else ''}")
    
    return ' and '.join(parts) if parts else ''


def _parse_servings(yield_value) -> str:
    """Extract servings from recipeYield field."""
    if not yield_value:
        return ''
    
    if isinstance(yield_value, (int, float)):
        return f"{yield_value} servings"
    
    if isinstance(yield_value, list):
        for item in yield_value:
            if isinstance(item, str) and ('serving' in item.lower() or 'makes' in item.lower()):
                return item
    
    if isinstance(yield_value, str):
        match = re.search(r'(\d+)', yield_value)
        if match:
            return f"{match.group(1)} servings"
        return yield_value
    
    return str(yield_value)


def _extract_ingredients(json_data: dict) -> list:
    """Extract ingredients from JSON-LD."""
    ingredient_list = json_data.get('recipeIngredient', [])
    if isinstance(ingredient_list, list):
        return [item.strip() for item in ingredient_list if item]
    return []


def _extract_instructions(json_data: dict) -> list:
    """Extract instructions from JSON-LD."""
    instruction_list = json_data.get('recipeInstructions', [])
    if not isinstance(instruction_list, list):
        return []
    
    instructions = []
    for item in instruction_list:
        if isinstance(item, str):
            instructions.append(item.strip())
        elif isinstance(item, dict):
            text = item.get('text', '') or item.get('name', '')
            if text:
                instructions.append(text.strip())
    
    return instructions


# ============================================================================
# HTML Fallback Extraction (When JSON-LD is not available)
# ============================================================================

def extract_from_html(html: str, url: str = '') -> dict:
    """Fallback HTML parsing when JSON-LD is not available.
    
    Uses BeautifulSoup for robust HTML parsing.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("Error: 'beautifulsoup4' library not installed.")
        print("Install with: pip install beautifulsoup4")
        sys.exit(1)
    
    soup = BeautifulSoup(html, 'lxml')
    
    recipe = {
        'title': '',
        'description': '',
        'prep_time': '',
        'cook_time': '',
        'total_time': '',
        'servings': '',
        'ingredients': [],
        'instructions': [],
        'cuisine': '',
    }
    
    # Extract title
    title_tag = soup.find('h1')
    if title_tag:
        recipe['title'] = title_tag.get_text(strip=True)
    
    # Try to find meta description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc:
        recipe['description'] = meta_desc.get('content', '')
    
    # Find ingredients section
    recipe['ingredients'] = _find_section_text(soup, ['ingredients', 'ingredient list'])
    
    # Find instructions section
    recipe['instructions'] = _find_section_text(soup, ['instructions', 'directions', 'method', 'steps'])
    
    return recipe


def _find_section_text(soup, section_names: list) -> list:
    """Find a section by heading text and extract its content as a list."""
    for name in section_names:
        # Find headings containing the section name
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4'], string=re.compile(name, re.IGNORECASE))
        
        for heading in headings:
            # Get the parent container
            parent = heading.find_parent(['div', 'section', 'article'])
            if not parent:
                continue
            
            # Try to find lists within this section
            lists = parent.find_all('ul')
            if lists:
                items = []
                for li in lists[0].find_all('li'):
                    text = li.get_text(strip=True)
                    if text:
                        items.append(text)
                if items:
                    return items
            
            # Try to find ordered lists
            olists = parent.find_all('ol')
            if olists:
                items = []
                for li in olists[0].find_all('li'):
                    text = li.get_text(strip=True)
                    if text:
                        items.append(text)
                if items:
                    return items
    
    return []


# ============================================================================
# YouTube Transcript Extraction
# ============================================================================

def extract_youtube_transcript(video_id: str) -> Tuple[str, str]:
    """Extract transcript and description from a YouTube video.
    
    Returns:
        Tuple of (transcript_text, video_description)
    """
    try:
        import yt_dlp
    except ImportError:
        print("Error: 'yt-dlp' library not installed.")
        print("Install with: pip install yt-dlp")
        sys.exit(1)
    
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    # Extract transcript
    transcript_text = ''
    try:
        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitles': ['en'],
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Get subtitles/transcripts
            if 'automatic_captions' in info and 'en' in info['automatic_captions']:
                transcript_data = info['automatic_captions']['en']
                if transcript_data:
                    transcript_text = ' '.join([
                        entry.get('text', '') for entry in transcript_data
                    ])
            elif 'subtitles' in info and 'en' in info['subtitles']:
                transcript_data = info['subtitles']['en']
                if transcript_data:
                    transcript_text = ' '.join([
                        entry.get('text', '') for entry in transcript_data
                    ])
    except Exception as e:
        print(f"Warning: Could not extract transcript: {e}")
    
    # Get video description
    description = ''
    try:
        ydl_opts_desc = {
            'skip_download': True,
            'quiet': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts_desc) as ydl:
            info = ydl.extract_info(url, download=False)
            description = info.get('description', '')
    except Exception:
        pass
    
    return transcript_text, description


def parse_transcript_for_recipe(transcript: str, description: str = '') -> dict:
    """Parse YouTube transcript and description to extract recipe data.
    
    This uses pattern matching and heuristics since transcripts are unstructured.
    The AI/LLM will refine this further.
    """
    combined_text = f"{transcript}\n\n{description}".lower()
    
    recipe = {
        'title': '',
        'description': '',
        'prep_time': '',
        'cook_time': '',
        'total_time': '',
        'servings': '',
        'ingredients': [],
        'instructions': [],
        'cuisine': '',
    }
    
    # Try to extract title from description
    if description:
        lines = description.strip().split('\n')
        if lines:
            recipe['title'] = lines[0].strip()
    
    return recipe


# ============================================================================
# Metadata Inference
# ============================================================================

def _infer_categories(recipe: dict) -> list:
    """Infer categories from recipe data."""
    title_lower = recipe.get('title', '').lower()
    description = recipe.get('description', '').lower()
    combined = title_lower + ' ' + description
    
    if any(word in combined for word in ['cocktail', 'drink', 'beer', 'wine', 'margarita', 'whiskey']):
        return ['Cocktail']
    elif any(word in combined for word in ['appetizer', 'starter', 'dip', 'snack', "hors d'oeuvre"]):
        return ['Appetizer']
    elif any(word in combined for word in ['dessert', 'cake', 'cookie', 'pie', 'brownie', 'ice cream', 'pastry']):
        return ['Dessert']
    elif any(word in combined for word in ['breakfast', 'brunch', 'pancake', 'eggs', 'oatmeal']):
        return ['Breakfast']
    else:
        return ['Dinner']


def _infer_method(recipe: dict) -> str:
    """Infer cooking method from recipe data."""
    instructions = ' '.join(recipe.get('instructions', [])).lower()
    description = recipe.get('description', '').lower()
    combined = instructions + ' ' + description
    
    if any(word in combined for word in ['sous vide', 'vacuum seal']):
        return 'Sous Vide'
    elif any(word in combined for word in ['bake', 'oven', 'preheat']):
        return 'Baking'
    elif any(word in combined for word in ['grill', 'bbq', 'smoke', 'smoked']):
        return 'Grilling'
    elif any(word in combined for word in ['fry', 'pan ', 'wok', 'sauté']):
        return 'Pan-Frying'
    elif any(word in combined for word in ['boil', 'simmer', 'soup', 'stew']):
        return 'Soup'
    elif any(word in combined for word in ['stir fry', 'wok']):
        return 'Stir Fry'
    elif any(word in combined for word in ['braise', 'slow cook', 'crockpot']):
        return 'Braising'
    elif any(word in combined for word in ['drink', 'mix', 'shake', 'blend']):
        return 'Drink'
    else:
        return 'Other'


def _infer_tags(recipe: dict) -> list:
    """Infer tags from recipe data."""
    tags = []
    title_lower = recipe.get('title', '').lower()
    instructions = ' '.join(recipe.get('instructions', [])).lower()
    
    # Extract key ingredients from title
    common_ingredients = ['chicken', 'pork', 'beef', 'fish', 'shrimp', 'pasta', 'rice', 'pizza', 'bread']
    for ingredient in common_ingredients:
        if ingredient in title_lower:
            tags.append(ingredient.title())
    
    # Add method-based tags
    if any(word in instructions for word in ['easy', 'simple', 'quick']):
        tags.append('Easy')
    if any(word in instructions for word in ['fast', '30 minutes', 'under an hour']):
        tags.append('Fast')
    
    return tags if tags else ['Recipe']


# ============================================================================
# Markdown Generation (Matches Blog Format Exactly)
# ============================================================================

def generate_recipe_markdown(recipe: dict, source_url: str = '', youtube_id: str = '') -> str:
    """Generate Hugo recipe markdown from extracted data.
    
    Matches the exact format used by existing recipes in the blog.
    """
    lines = []
    
    # Front matter
    lines.append('+++')
    lines.append(f"date = '{_get_current_timestamp()}'")
    lines.append('draft = true')  # Start as draft for review
    lines.append(f"title = '{recipe['title']}'")
    
    if recipe.get('cuisine'):
        lines.append(f"cuisine = '{recipe['cuisine']}'")
    
    categories = _infer_categories(recipe)
    lines.append(f"categories = {json.dumps(categories)}")
    
    method = _infer_method(recipe)
    lines.append(f"method = '{method}'")
    
    tags = _infer_tags(recipe)
    lines.append(f"tags = {json.dumps(tags)}")
    
    lines.append('+++')
    lines.append('')
    
    # Timing section
    lines.append('## Timing')
    lines.append('')
    if recipe.get('prep_time'):
        lines.append(f"- **Prep Time:** {recipe['prep_time']}")
    if recipe.get('cook_time'):
        lines.append(f"- **Cook Time:** {recipe['cook_time']}")
    if recipe.get('total_time'):
        lines.append(f"- **Total Time:** {recipe['total_time']}")
    if recipe.get('servings'):
        lines.append(f"- **Servings:** {recipe['servings']}")
    lines.append('')
    
    # Ingredients section
    lines.append('## Ingredients')
    lines.append('')
    for ingredient in recipe.get('ingredients', []):
        lines.append(f"- {ingredient}")
    if not recipe.get('ingredients'):
        lines.append('- TODO: Add ingredients')
    lines.append('')
    
    # Instructions section
    lines.append('## Instructions')
    lines.append('')
    for i, instruction in enumerate(recipe.get('instructions', []), 1):
        lines.append(f"{i}. {instruction}")
    if not recipe.get('instructions'):
        lines.append('1. TODO: Add instructions')
    lines.append('')
    
    # Source section (if applicable)
    if youtube_id:
        lines.append('## Source')
        lines.append('')
        lines.append(f'{{{{< youtubeLite id="{youtube_id}" label="Recipe Video" >}}}}')
        lines.append('')
    elif source_url:
        lines.append('## Source')
        lines.append('')
        lines.append(source_url)
        lines.append('')
    
    return '\n'.join(lines)


def _get_current_timestamp() -> str:
    """Get current timestamp in Hugo format."""
    now = datetime.now()
    return now.strftime('%Y-%m-%dT%H:%M:%S') + '-05:00'


# ============================================================================
# Main Workflow
# ============================================================================

def extract_recipe_from_website(url: str) -> dict:
    """Main workflow for extracting a recipe from a website."""
    print(f"Fetching webpage: {url}")
    html = fetch_webpage(url)
    
    # Try JSON-LD first (most accurate)
    print("Checking for structured data (JSON-LD)...")
    json_ld = extract_json_ld(html)
    
    if json_ld:
        print("Found JSON-LD structured data!")
        recipe = parse_json_ld_recipe(json_ld)
    else:
        print("No JSON-LD found. Falling back to HTML parsing...")
        recipe = extract_from_html(html, url)
    
    return recipe


def extract_recipe_from_youtube(video_id: str) -> dict:
    """Main workflow for extracting a recipe from a YouTube video."""
    print(f"Extracting transcript from YouTube video: {video_id}")
    transcript, description = extract_youtube_transcript(video_id)
    
    if not transcript.strip():
        print("Warning: Could not extract transcript. Recipe will need manual completion.")
    
    recipe = parse_transcript_for_recipe(transcript, description)
    recipe['youtube_id'] = video_id
    
    return recipe


def create_recipe_file(recipe: dict, output_dir: str, source_url: str = '', youtube_id: str = '') -> Path:
    """Generate and save the recipe markdown file."""
    # Create slug from title
    slug = re.sub(r'[^a-z0-9\s-]', '', recipe['title'].lower())
    slug = re.sub(r'\s+', '-', slug.strip())
    slug = slug.replace('--', '-')  # Remove double hyphens
    
    output_path = Path(output_dir) / f"{slug}.md"
    
    # Generate markdown
    markdown = generate_recipe_markdown(recipe, source_url, youtube_id)
    
    # Write file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding='utf-8')
    
    print(f"\nRecipe file created: {output_path}")
    print("Note: File is marked as draft (draft = true). Review and edit before publishing.")
    
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description='Extract recipes from websites or YouTube videos for the Hugo recipe blog.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract from a website
  python extract_recipe.py https://example.com/recipe-page
  
  # Extract from YouTube video
  python extract_recipe.py dJ-sAEzw9Jc
  
  # Specify source type
  python extract_recipe.py https://youtube.com/watch?v=VIDEO --source youtube
  
  # Custom output directory
  python extract_recipe.py URL --output-dir ../content/recipes
        """
    )
    
    parser.add_argument('url_or_video_id', help='Website URL or YouTube video ID')
    parser.add_argument('--source', choices=['website', 'youtube'], 
                       help='Source type (auto-detected if not specified)')
    parser.add_argument('--output-dir', default='content/recipes',
                       help='Output directory for recipe files (default: content/recipes)')
    
    args = parser.parse_args()
    
    # Determine source type
    if not args.source:
        if 'youtube.com' in args.url_or_video_id or 'youtu.be' in args.url_or_video_id:
            args.source = 'youtube'
        elif args.url_or_video_id.startswith('http'):
            args.source = 'website'
        else:
            # Assume YouTube video ID
            args.source = 'youtube'
    
    print("=" * 60)
    print("Recipe Extractor for Hugo Recipe Blog")
    print("=" * 60)
    
    try:
        if args.source == 'website':
            recipe = extract_recipe_from_website(args.url_or_video_id)
            output_path = create_recipe_file(
                recipe, 
                args.output_dir, 
                source_url=args.url_or_video_id
            )
        else:  # youtube
            recipe = extract_recipe_from_youtube(args.url_or_video_id)
            output_path = create_recipe_file(
                recipe,
                args.output_dir,
                youtube_id=args.url_or_video_id
            )
        
        print("\n" + "=" * 60)
        print("Next Steps:")
        print("=" * 60)
        print(f"1. Review the generated file: {output_path}")
        print("2. Fill in any missing information (timing, cuisine, etc.)")
        print("3. Format ingredients and instructions to match blog style")
        print("4. Set draft = false when ready to publish")
        print("5. Run 'hugo' to build your site")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
