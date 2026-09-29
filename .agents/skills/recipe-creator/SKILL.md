# Recipe Creator Skill

A skill for creating new recipe markdown files for this Hugo-based recipe blog by extracting content from websites, YouTube videos, or text descriptions — matching the existing recipe style.

## Project Context

- **Static site generator:** Hugo (Blowfish theme)
- **Recipe format:** Plain Markdown with YAML front matter
- **Location:** `content/recipes/<recipe-slug>.md` (or `content/recipes/<recipe-slug>/index.md` for multi-file recipes)
- **No custom content type** — uses generic Blowfish single.html template
- **16 existing recipes** as reference examples

## Recipe Front Matter Pattern

```yaml
+++
date = 'YYYY-MM-DDTHH:MM:SS-05:00'
draft = false
title = 'Recipe Title'
cuisine = 'CuisineType'        # optional, e.g. Italian, Japanese, American
categories = ['Category1']     # required, e.g. Dinner, Appetizer, Cocktail
method = 'Method'              # required, e.g. Baking, Sous Vide, Stir Fry
tags = ['Tag1', 'Tag2']        # optional, e.g. Pizza, Ramen, Easy
+++
```

## Recipe Body Sections (in order)

### 1. Timing (required)

```markdown
## Timing

- **Prep Time:** X minutes/hours
- **Cook Time:** X minutes/hours
- **Total Time:** X minutes/hours
- **Servings:** Y servings/portions
```

### 2. Ingredients (required)

```markdown
## Ingredients

- 1 item with quantity and optional notes in parens
- ½ cup butter
- 2 cups parmesan cheese (freshly grated)
- Kosher salt
```

**Notes:**

- Use fractions (½, ¼, ⅓, etc.) not decimals
- Grouping by category is optional (e.g., Produce/Pantry/Dairy/Meat in oregano-chicken-skewers)
- Cross-reference other recipes using `{{< ref "recipes/slug" >}}`

### 3. Instructions (required)

```markdown
## Instructions

1. Step one with action verb
2. Step two
   > Optional blockquote for tips within a step
```

**Notes:**

- Numbered steps, starting at 1
- Sub-sections use `###` headers (e.g., `### Dough Prep`, `### Sauce`)
- Tips/notes within steps use blockquotes (`> text`)
- General notes go in a separate `## Notes/Tips` section

### 4. Optional Sections

**Notes/Tips:**

```markdown
## Notes/Tips

General tips for the recipe.

{{< alert >}}
Important note or warning.
{{< /alert >}}
```

**Source (for YouTube/website attribution):**

```markdown
## Source

{{< youtubeLite id="VIDEO_ID" label="Video Title" >}}

https://example.com/original-recipe-url
```

**Gallery (for photos):**

```markdown
{{< gallery >}}
<img src="img/filename.png" class="grid-w50" />
{{< /gallery >}}
```

## Automation Tools

Scripts are available in `scripts/` to automate recipe extraction:

```bash
# Install dependencies
pip install -r scripts/requirements.txt

# Extract from a website
python scripts/extract_recipe.py https://example.com/recipe-page

# Extract from YouTube video
python scripts/extract_recipe.py VIDEO_ID --source youtube

# Custom output directory
python scripts/extract_recipe.py URL --output-dir content/recipes
```

See `scripts/README.md` for full documentation.

## Workflow: Creating a New Recipe

### Source 1: Website Recipe

**Automated approach (preferred):**

1. Run `python scripts/extract_recipe.py <URL>` — extracts JSON-LD or HTML-parsed data
2. Review the generated draft file in `content/recipes/<slug>.md`
3. Refine formatting to match blog style (ingredients, instructions)
4. Fill in any missing metadata (cuisine, timing, servings)

**Manual approach (when automation fails):**

1. Fetch the webpage content — extract HTML from the URL
2. Try JSON-LD first — look for `application/ld+json` with `@type: "Recipe"` schema
3. Fallback to HTML parsing — find ingredient lists, instruction steps, timing info
4. AI extraction — parse the raw content into structured recipe data
5. Fill missing metadata — cuisine, categories, method, tags (ask user if unclear)
6. Generate markdown — format using the exact pattern above
7. Create file — write to `content/recipes/<slug>.md`

### Source 2: YouTube Video Recipe

**Automated approach (preferred):**

1. Run `python scripts/extract_recipe.py <VIDEO_ID> --source youtube` — extracts transcript + description
2. Review the generated draft file in `content/recipes/<slug>.md`
3. Refine formatting to match blog style (transcripts are unstructured)
4. Add YouTube embed via `{{< youtubeLite >}}` shortcode if not auto-added

**Manual approach:**

1. Get transcript — use yt-dlp or YouTube's auto-generated captions
2. AI parse transcript — extract ingredients, steps, timing from spoken content
3. Cross-reference video description — often contains measurements and links
4. Fill metadata — cuisine, categories, method, tags
5. Generate markdown — format using the exact pattern above
6. Add Source section — include `{{< youtubeLite >}}` with video ID
7. Create file — write to `content/recipes/<slug>.md`

### Source 3: Text Description / Notes

1. Parse provided text — extract what recipe information is available
2. Ask user for missing info — timing, servings, specific measurements
3. Generate markdown — format using the exact pattern above
4. Create file — write to `content/recipes/<slug>.md`

## Key Conventions to Match

- **Ingredient formatting:** quantity first, then item, optional notes in `(parens)`
- **Step numbering:** always restart at 1 for each instruction subsection
- **Blockquotes:** use `>` for inline tips within steps
- **Cross-references:** use Hugo shortcode `{{< ref "recipes/slug" >}}`
- **Titles:** Title Case (not sentence case)
- **Slugs:** kebab-case, descriptive but concise
- **Draft mode:** create as `draft = true` initially for review

## Useful Hugo Shortcodes in Recipes

| Shortcode     | Purpose             | Example                                                      |
| ------------- | ------------------- | ------------------------------------------------------------ |
| `youtubeLite` | Embed YouTube video | `{{< youtubeLite id="VIDEO_ID" label="Title" >}}`            |
| `gallery`     | Photo gallery       | `{{< gallery >}}<img src="img/photo.png" />{{< /gallery >}}` |
| `alert`       | Callout/note box    | `{{< alert >}}Tip text{{< /alert >}}`                        |
| `ref`         | Internal link       | `{{< ref "recipes/slug" >}}`                                 |

## Common Method Values (from existing recipes)

Baking, Boiling, Braising, Dough, Drink, Frying, Grilling, Pan-Frying, Sauce, Soup, Sous Vide, Stir Fry, Stovetop

## Common Categories (from existing recipes)

Dinner, Appetizer, Cocktail, Breakfast, Lunch, Dessert, Snack
