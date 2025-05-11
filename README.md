# My Recipe Collection

[![GitHub Pages Status](https://githubstatus.com/shields/up)](https://githubstatus.com/)

A personal collection of favorite recipes built with [Hugo](https://gohugo.io/), styled using the [Blowfish theme](https://codethemes.com/blowfish/), and deployed automatically to GitHub Pages via GitHub Actions.

## Features

- **Organized Recipes:** Recipes are categorized by cuisine, category (appetizer, main course, dessert), and tags for easy browsing.
- **Search Functionality:** A built-in search allows you to quickly find recipes based on keywords or ingredients.
- **Responsive Design:** The site is designed to look great on all devices (desktop, tablet, mobile).
- **Version Controlled:** Recipes are stored as Markdown files in a Git repository for easy version control and collaboration.

## Technologies Used

- **Hugo:** A fast and flexible static site generator.
- **Blowfish Theme:** A clean and modern Hugo theme providing the visual design.
- **Markdown:** Plain text formatting syntax used to write recipes.
- **GitHub Actions:** Automated workflows for building and deploying the site.
- **Fuse.js:** Client-side search library for fast and relevant recipe results.

## Getting Started

### Prerequisites

- [Hugo](https://gohugo.io/installation/) installed on your local machine.
- Git installed.

### Installation & Local Development

1.  **Clone the repository:**

    ```bash
    git clone git@github.com:phelewski/recipe-blog.git
    cd recipe-blog
    ```

2.  **Install theme dependencies:**

    ```bash
    git submodule update --init --recursive
    ```

3.  **Run the development server:**

    ```bash
    hugo server -D
    ```

    This will start a local web server at [http://localhost:1313/recipe-blog/](http://localhost:1313/recipe-blog/). You can view your site in your browser and make changes to the content and templates.

### Adding Recipes

1.  Create a new Markdown file in the `content/recipes/` directory.
2.  Use the recipe template (see `archetypes/default.md`) as a starting point.
3.  Fill in the recipe file with appropriate metadata (title, cuisine, tags, etc.).
4.  Write your recipe content using Markdown.
5.  Commit and push your changes to GitHub.

## Deployment (GitHub Pages)

This project uses GitHub Actions to automatically build and deploy the site to GitHub Pages whenever you push changes to the `main` branch.

- **Workflow File:** The deployment workflow is defined in [`.github/workflows/gh-pages.yml`](.github/workflows/gh-pages.yml)
- **GitHub Pages URL:** Your live website will be available at: [https://phelewski.github.io/recipe-blog/](https://phelewski.github.io/recipe-blog/)

## License

This project is licensed under the [MIT License](https://en.wikipedia.org/wiki/MIT_License) - see the [LICENSE](LICENSE) file for details.
