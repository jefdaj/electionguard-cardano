set -euo pipefail

system=$(nix eval --impure --raw --expr builtins.currentSystem)

# 1. Nix: table of packages built from meta.description
mkdir -p docs/nix
{
  echo "# Nix packages"
  echo
  # Nix interpolation, not shell; single quotes are intentional
  # shellcheck disable=SC2016
  nix eval --raw ".#packages.${system}" --apply '
    ps: "| Package | Description |\n|---|---|\n" +
      builtins.concatStringsSep "\n" (builtins.attrValues
        (builtins.mapAttrs (n: p: "| `${n}` | ${p.meta.description or ""} |") ps))
  '
} > docs/nix/packages.md

# 2. Aiken HTML into docs/ so mkdocs copies it and can validate links to it
rm -rf docs/aiken
(cd aiken && aiken docs --destination ../docs/aiken)

# Point source links at the aiken/ subdirectory
# TODO add a tag per aiken version so the src links work?
find docs/aiken -name '*.html' -exec \
  sed -i -E 's#(https://github\.com/jefdaj/electionguard-cardano/blob/[^/"]+)/#\1/aiken/#g' {} +

# 3. Build the site
mkdocs build --strict --site-dir site

# 4. serve locally to check everything looks good
python -m http.server -d site/
