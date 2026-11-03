#!/bin/sh
# sift installer for Linux and macOS: puts the latest release binary into ~/.local/bin.
#   curl -fsSL https://sa1ntsinner.github.io/sift/install.sh | sh
# SIFT_INSTALL_DIR picks another folder.
set -eu

case "$(uname -s)-$(uname -m)" in
  Linux-x86_64 | Linux-amd64) file=sift-linux-x64 ;;
  Darwin-arm64) file=sift-macos-arm64 ;;
  *)
    echo "There is no sift download for $(uname -s) $(uname -m) yet." >&2
    echo "With Python 3.11+ it installs anyway: uv tool install steamsift" >&2
    exit 1
    ;;
esac

dir="${SIFT_INSTALL_DIR:-$HOME/.local/bin}"
url="https://github.com/sa1ntsinner/sift/releases/latest/download/$file"

mkdir -p "$dir"
echo "Downloading $url"
curl -fL --progress-bar "$url" -o "$dir/sift.part"
chmod +x "$dir/sift.part"
mv -f "$dir/sift.part" "$dir/sift"
"$dir/sift" --version

case ":$PATH:" in
  *":$dir:"*) echo "Done. Run: sift" ;;
  *)
    case "${SHELL:-}" in
      */zsh) rc="$HOME/.zshrc" ;;
      */bash) rc="$HOME/.bashrc" ;;
      *) rc="$HOME/.profile" ;;
    esac
    echo "Done. $dir is not on your PATH yet. Add it once, then run sift:"
    echo "  echo 'export PATH=\"$dir:\$PATH\"' >> $rc && . $rc"
    ;;
esac
