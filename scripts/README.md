# Recipe Extraction Scripts

Tools for extracting recipes from websites and YouTube videos into the Hugo recipe blog format.

## Setup

Install the required dependencies:

```bash
pip install -r requirements.txt
```

This installs:

- **requests** — Fetch webpages
- **beautifulsoup4 + lxml** — Parse HTML content
- **yt-dlp** — Extract YouTube transcripts and metadata

## Usage

### From a Website

Extracts recipe data using Schema.org JSON-LD (most accurate), with HTML parsing as fallback.

```bash
python extract_recipe.py https://example.com/recipe-page
```

Output: `content/recipes/<recipe-slug>.md` (draft mode)

### From YouTube

Extracts transcript and video description, then parses for recipe data.

```bash
# By URL
python extract_recipe.py https://www.youtube.com/watch?v=VIDEO_ID

# By video ID only
python extract_recipe.py VIDEO_ID

# Explicit source type
python extract_recipe.py VIDEO_ID --source youtube
```

Output: `content/recipes/<recipe-slug>.md` with YouTube embed in Source section

### Custom Output Directory

```bash
python extract_recipe.py URL --output-dir ../content/recipes
```

## How It Works

### Website Extraction (2-tier approach)

1. **JSON-LD extraction** — Looks for `application/ld+json` structured data with `@type: "Recipe"`. This is the gold standard when available, as it contains all recipe fields in a machine-readable format.

2. **HTML fallback** — Uses BeautifulSoup to find sections labeled "Ingredients" and "Instructions/Directions", extracting list items from those sections.

### YouTube Extraction

1. **Transcript extraction** — Uses yt-dlp to pull auto-generated captions or manual subtitles
2. **Description parsing** — Extracts video description which often contains measurements and links
3. **Heuristic parsing** — Looks for ingredient and instruction patterns in the combined text

### Metadata Inference

The script automatically infers:

- **Categories** — Based on title keywords (cocktail, appetizer, dessert, etc.)
- **Method** — Based on cooking technique keywords (baking, grilling, sous vide, etc.)
- **Tags** — Extracts key ingredients from title and adds method-based tags

### Output Format

Generated files match the exact format of existing recipes:

```markdown
+++
date = '2025-11-02T09:27:37-05:00'
draft = true
title = 'Recipe Title'
cuisine = 'Italian'
categories = ['Dinner']
method = 'Baking'
tags = ['Pizza', 'Easy']
+++

## Timing

- **Prep Time:** 15 minutes
- **Cook Time:** 30 minutes
- **Total Time:** 45 minutes
- **Servings:** 4

## Ingredients

- 2 cups flour
- 1 tsp salt

## Instructions

1. Mix ingredients together
2. Bake at 350°F for 30 minutes

## Source

https://example.com/original-recipe
```

## Next Steps After Extraction

The generated files are created as **drafts** (`draft = true`) for review:

1. **Review the file** — Check accuracy of extracted data
2. **Fill in missing info** — Timing, cuisine, servings may need manual entry
3. **Format ingredients** — Ensure consistent formatting (fractions, units)
4. **Add cross-references** — Use `{{< ref "recipes/slug" >}}` for related recipes
5. **Set draft = false** — When ready to publish
6. **Build site** — Run `hugo` to generate the static site

## Limitations

- **YouTube transcripts** are unstructured text — may need significant manual refinement
- **Websites without JSON-LD** — HTML parsing is less reliable than structured data
- **Images** — Not extracted (by design, per your preference)
- **Complex layouts** — Multi-column or JavaScript-rendered content may not parse correctly

## Troubleshooting

### "requests library not installed"

```bash
pip install requests beautifulsoup4
```

### "yt-dlp library not installed"

```bash
pip install yt-dlp
```

### YouTube transcript extraction fails

- Some videos don't have captions available
- Try specifying a different language: edit the `subtitles` option in the script
- You can manually add the YouTube embed after extraction

### JSON-LD not found

- Many recipe sites use JSON-LD, but some don't
- The HTML fallback will still extract basic structure
- You may need to manually fill in more fields
