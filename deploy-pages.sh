#!/bin/bash
set -e

TOKEN="${GITHUB_TOKEN}"
REPO="alemarraa/een-construction-website"
REMOTE="https://alemarraa:${TOKEN}@github.com/${REPO}.git"
ROOT="/Users/alessandromarra/een-construction-website"

if [ -z "$TOKEN" ]; then
  echo "Error: GITHUB_TOKEN environment variable is not set."
  echo "Usage: GITHUB_TOKEN=<token> ./deploy-pages.sh"
  exit 1
fi

cd "$ROOT"

echo "→ Step 1/3: Pushing source code to main..."
git push "$REMOTE" main

echo "→ Step 2/3: Building site for GitHub Pages..."
export PATH="/Users/alessandromarra/.local/share/fnm/node-versions/v20.20.2/installation/bin:$PATH"
npx pnpm build:pages

touch dist/public/.nojekyll

echo "→ Step 3/3: Pushing built site to gh-pages branch..."
cd dist/public
git init -b gh-pages
git add -A
git commit -m "Deploy to GitHub Pages"
git push --force "$REMOTE" gh-pages

echo ""
echo "✓ Done! Now go to:"
echo "  https://github.com/${REPO}/settings/pages"
echo ""
echo "  Set Source → Deploy from a branch"
echo "  Branch → gh-pages / folder → / (root)"
echo "  Click Save"
echo ""
echo "  Your site: https://alemarraa.github.io/een-construction-website/"
