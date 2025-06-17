{
  description = "SVAIA";
# Input dependencies
    inputs = {
      nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
      nixstable.url = "github:nixos/nixpkgs/nixos-25.05";
    };

    # Output configuration
    outputs = { self, nixstable, nixpkgs }:
        let
          # Get the package set for the current system
          pkgs = nixstable.legacyPackages.x86_64-linux;
          pkgs_unstable = nixpkgs.legacyPackages.x86_64-linux;

        in {
          # Development shell configuration
          devShells.x86_64-linux.default = pkgs.mkShell {
            # Build inputs (development dependencies)
            buildInputs = [
              pkgs.eza
              pkgs.python312
              pkgs.pyright
              pkgs.ruff
              pkgs.tree
              pkgs.pkgconf
              pkgs_unstable.uv
              pkgs_unstable.semgrep
              pkgs_unstable.mariadb_114
              pkgs_unstable.python312Packages.mariadb
              # Done here mariadb and not on uv cuz of an error TODO fix
           ];
          
          };
        };
}
