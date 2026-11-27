# Recipe Manager

Create, add, update, and modify recipes for this Hugo-based recipe blog.

## Workflow Overview

1. **Gather the recipe** — from a URL, YouTube video, paste/copy of text, or verbal description
2. **Extract & format** — produce a properly structured Markdown file matching the blog's format
3. **Set metadata** — title, cuisine, categories, method, tags (auto-infer when possible)
4. **Create recipe** — write to `content/recipes/<recipe-slug>.md` with `draft = false` (published by default)
5. **Review & edit** — user reviews and edits if needed

## Recipe File Format

Recipes live in `content/recipes/`. Two layout options:

### Single file (most common)

```
content/recipes/butter-chicken.md
```

### Directory with images (when the recipe has photos)

```
content/recipes/bone-in-pork-chop/index.md
content/recipes/bone-in-pork-chop/img/bone-in-pork-chop-1.png
```

### Front Matter (TOML)

```toml
+++
date = '2026-11-27T00:00:00-04:00'
draft = false
title = 'Recipe Title'
cuisine = 'Indian'
categories = ['Dinner']
method = 'Braising'
tags = ['Chicken', 'Curry', 'Indian', 'Restaurant-style']
+++
```

| Field        | Description                               | Notes                                                                                             |
| ------------ | ----------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `date`       | Timestamp of creation                     | Use current date/time with `-04:00` offset                                                        |
| `draft`      | `true` to hide from site, `false` to show | Published by default — set to `true` only if you want to hold for review                          |
| `title`      | Recipe name                               | Title Case, slugified from filename                                                               |
| `cuisine`    | Cuisine type (optional)                   | e.g., 'Indian', 'American', 'Japanese'                                                            |
| `categories` | Array of category strings                 | Common: `['Dinner']`, `['Cocktail']`, `['Dessert']`, `['Breakfast']`, `['Appetizer']`             |
| `method`     | Cooking method (string or array)          | e.g., 'Baking', 'Grilling', 'Sous Vide', `['Pan-Frying', 'Baking', 'Grilling']`                   |
| `tags`       | Array of keyword tags                     | Include main ingredients, style notes. e.g., `['Chicken', 'Curry', 'Indian', 'Restaurant-style']` |

### Body Structure

```markdown
## Timing

- **Prep Time:** 30 minutes (plus overnight marinating)
- **Cook Time:** 1 hour
- **Total Time:** 1 hour 30 minutes (plus marinating time)
- **Servings:** 4 people

## Ingredients

- 2 cups flour
- 1 tsp salt
- 1 cup (145g) whole milk yogurt

**Sub-sections for grouped ingredients (optional):**

**Green Chutney:**

- 2 cups (35g) fresh cilantro leaves

### Pantry

- 2 large eggs (room temperature)

## Instructions

1. Mix ingredients together
2. Bake at 350°F for 30 minutes

**Sub-sections for multi-step recipes (optional):**

**Green Chutney:**

1. Blend cilantro, garlic, cumin, salt, ginger, and chilies

### Pan-Frying

1. Preheat oven to 350°F

## Notes/Tips

{{< alert >}}
**Warning!** This action is destructive!
{{< /alert >}}

- Use besan flour to thicken the marinade if your yogurt is on the looser side.

## Source

{{< youtubeLite id="dJ-sAEzw9Jc" label="Recipe Video" >}}

or

https://example.com/original-recipe
```

### Sections Reference

| Section      | Required?       | Format                                                                           |
| ------------ | --------------- | -------------------------------------------------------------------------------- |
| Timing       | Yes             | 4 bullet points: Prep, Cook, Total, Servings                                     |
| Ingredients  | Yes             | Bulleted list. Use bold sub-headers for grouped ingredients or pantry categories |
| Instructions | Yes             | Numbered steps. Use bold sub-headers or `###` headers for multi-phase recipes    |
| Notes/Tips   | Optional        | Bullet points, tips, storage info, variations                                    |
| Source       | When applicable | YouTube embed shortcode or URL                                                   |

## Image Handling

When the user provides images (or wants to add them):

1. Create a subdirectory: `content/recipes/<recipe-slug>/`
2. Move the markdown file there as `index.md`
3. Save images in `content/recipes/<recipe-slug>/img/`
4. Add gallery shortcode after instructions:

```markdown
{{< gallery >}}
<img src="img/recipe-photo-1.png" class="grid-w100" />
<img src="img/recipe-photo-2.png" class="grid-w100" />
{{< /gallery >}}
```

## Formatting Conventions

### Fractions

Always use Unicode fractions instead of slash notation:

- Use **½** instead of 1/2
- Use **¼** instead of 1/4
- Use **¾** instead of 3/4

When converting from slash notation, replace all instances in both ingredients and instructions.

### Instructions Spacing

Numbered steps must be single-spaced with no blank lines between them, and each step must be on a single line (no hard wrapping):

```markdown
1. Mix the dry ingredients together
2. Add the wet ingredients and stir until combined
3. Bake at 350°F for 30 minutes
```

Never add blank lines between consecutive numbered steps. Never hard-wrap long instruction lines — keep each step on one line. Blank lines are only allowed before a new sub-section header (bold or `###`).

## Auto-Inference Rules

When the user provides a URL, video ID, or pasted text, use these rules to auto-fill metadata:

### Categories (from title/description keywords)

| Keywords                                               | Category        |
| ------------------------------------------------------ | --------------- |
| cocktail, drink, beer, wine, margarita, whiskey        | `['Cocktail']`  |
| appetizer, starter, dip, snack                         | `['Appetizer']` |
| dessert, cake, cookie, pie, brownie, ice cream, pastry | `['Dessert']`   |
| breakfast, brunch, pancake, eggs, oatmeal              | `['Breakfast']` |
| default                                                | `['Dinner']`    |

### Method (from instructions/description keywords)

| Keywords                    | Method       |
| --------------------------- | ------------ |
| sous vide, vacuum seal      | 'Sous Vide'  |
| bake, oven, preheat         | 'Baking'     |
| grill, bbq, smoke, smoked   | 'Grilling'   |
| fry, pan, wok, saute        | 'Pan-Frying' |
| boil, simmer, soup, stew    | 'Soup'       |
| stir fry, wok               | 'Stir Fry'   |
| braise, slow cook, crockpot | 'Braising'   |
| drink, mix, shake, blend    | 'Drink'      |
| default                     | 'Other'      |

### Tags (from title + instructions)

- Extract key ingredients from the title (chicken -> 'Chicken', pork -> 'Pork', etc.)
- Add style tags like 'Easy', 'Fast' when appropriate
- Add cuisine tag if identifiable
- Always include at least one descriptive tag

## Input Sources & Handling

### 1. Website URL

- Try extracting via the existing `scripts/extract_recipe.py` tool (JSON-LD first, HTML fallback)
- If extraction succeeds, review and refine the output
- If extraction fails or is incomplete, manually structure from pasted content

### 2. YouTube Video

- Extract transcript + description (via `scripts/extract_recipe.py`)
- Parse ingredients and instructions from the transcript
- Add YouTube embed in Source section: `{{< youtubeLite id="VIDEO_ID" label="Recipe Title" >}}`
- Note: transcripts are unstructured — significant manual refinement will likely be needed

### 3. Pasted Recipe Text

- Identify and extract: title, ingredients list, instructions steps, timing info, servings
- Infer cuisine from ingredient patterns or explicit mentions
- Structure into the recipe format above
- Ask the user for any missing metadata (cuisine, method, tags) if not inferable

### 4. Verbal Description / "From Scratch"

- Ask clarifying questions: name, what it is, ingredients, cooking steps, timing, servings
- Fill in all sections based on user's answers
- Infer cuisine and categories where possible

## Updating Existing Recipes

When the user wants to modify an existing recipe:

1. **Locate** the existing file in `content/recipes/` (match by title or slug)
2. **Read** the current file
3. **Apply changes** — add/remove ingredients, update instructions, fix timing, change metadata
4. **Preserve** existing structure and formatting style
5. **Preserve** draft status — keep `draft = false` unless user explicitly wants to hold for review

Common update scenarios:

- Add missing timing info
- Fix ingredient measurements or formatting
- Add notes/tips or storage info
- Update instructions for clarity
- Add a source link or YouTube embed
- Change/update tags, categories, or cuisine
- Add images to a recipe that previously had none

## Output Convention

- Always create new recipes with `draft = false` (published by default)
- Use kebab-case slugs derived from the title (e.g., 'Butter Chicken' -> `butter-chicken.md`)
- Set timezone offset to `-04:00` for dates
- After creating a file, run Prettier to format it: `npx prettier --write content/recipes/<recipe-slug>.md`
- After creating a file, summarize what was done and highlight anything that needs user review
