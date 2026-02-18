{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  name = "quart-flask-htmx-dev";

  buildInputs = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.python311Packages.setuptools
    pkgs.python311Packages.wheel

    # Web framework bits
    pkgs.python311Packages.flask
    pkgs.python311Packages.quart
    pkgs.python311Packages.jinja2

    # Optional: type checking / linting
    # pkgs.python311Packages.black
    # pkgs.python311Packages.mypy
  ];

  shellHook = ''
    echo "Python: $(python --version)"
    echo "You’re in the Quart/Flask dev shell. Run your app with: python app.py"
  '';
}
