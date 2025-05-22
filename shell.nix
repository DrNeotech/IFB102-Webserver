{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = [
    pkgs.python312
    (pkgs.python312.withPackages (ps: with ps; [
      ps.pillow
      ps.numpy
      ps.requests
      ps.requests-futures
      ps.click
      ps.python-dotenv
      ps.flask
    ]))
  ];
}