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

# 2. Python + hand-written docs
command -v mkdocs python
python -c "import pycardano; print(pycardano.__file__)"
mkdocs build --strict --site-dir site

# 3. Aiken HTML, placed inside the built site
(cd aiken && aiken docs --destination ../site/aiken)
