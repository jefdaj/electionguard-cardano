{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  name = "quart-flask-htmx-dev";

  buildInputs = [
    pkgs.python312
    pkgs.python312Packages.pip
    pkgs.python312Packages.setuptools
    pkgs.python312Packages.wheel

    # Web framework bits
    pkgs.python312Packages.flask
    pkgs.python312Packages.quart
    pkgs.python312Packages.jinja2

    # Optional: type checking / linting
    # pkgs.python312Packages.black
    # pkgs.python312Packages.mypy
  ];

  shellHook = ''
    echo "Python: $(python --version)"
    echo "You’re in the Quart/Flask dev shell. Run your app with: python app.py"
  '';
}
