{
  description = "A flake to install OpenFST Thrax";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "aarch64-darwin";
      pkgs = nixpkgs.legacyPackages.${system};
      openfst = pkgs.stdenv.mkDerivation {
        pname = "openfst";
        version = "1.8.4";
        src = pkgs.fetchurl {
          url = "https://www.openfst.org/twiki/pub/FST/FstDownload/openfst-1.8.4.tar.gz";
          sha512 = "/XXp910dOK+GY/W+qwhMTLP9hvdjCkgNPhbAuO+Th2hupZo5nAEwVEknTwhnoEgTAeor+DfdkyWhVy44fDNc8w==";
        };
        buildInputs = with pkgs; [
          clang_22
          gnumake
        ];
        configureFlags = [
          "--enable-compact-fsts"
          "--enable-compress"
          "--enable-const-fsts"
          "--enable-far"
          "--enable-linear-fsts"
          "--enable-lookahead-fsts"
          "--enable-mpdt"
          "--enable-ngram-fsts"
          "--enable-pdt"
          "--enable-grm"
          "--enable-static=no"
        ];

        configurePhase = ''
          ./configure --prefix=$out --enable-compact-fsts \
          --enable-compress --enable-const-fsts --enable-far \
          --enable-linear-fsts --enable-lookahead-fsts \
          --enable-mpdt --enable-ngram-fsts --enable-pdt \
          --enable-grm --enable-static=no
        '';
        installPhase = ''
          make
          make install
        '';
      };
      thrax = pkgs.stdenv.mkDerivation {
        pname = "thrax";
        version = "1.3.10";
        src = pkgs.fetchurl {
          url = "https://www.openfst.org/twiki/pub/GRM/ThraxDownload/thrax-1.3.10.tar.gz";
          sha512 = "Uuik43cHELeajm1CW+lWrKMq5AOcqOBSN44Qg4UgvC+VHxKISms88KAQWCVCDvhwu1PX+BkBEGU1OfP2b4DqaA==";
        };
        buildInputs = [
          pkgs.clang_22
          pkgs.gnumake
          openfst
        ];
        configurePhase = ''
          ./configure --prefix=$out
        '';
        installPhase = ''
          make
          make install
        '';

        # Check if binary exists post-build
        postInstall = ''
          ls -la $out/bin/
          file $out/bin/thrax-makedep
        '';
      };
    in {
      defaultPackage.${system} = thrax;
      packages.${system} = thrax;
    };
}
