# AccessD Web UI Import

- Source repository: https://github.com/RaspAP/raspap-webgui
- Imported from commit: ae9813b47bdbe35ea300fd9709e526d5b759ed82
- Imported on: 2026-02-19

## Import actions

1. Cloned upstream repository to `/tmp/raspap-webgui`.
2. Removed upstream git metadata by copying with `--exclude .git`.
3. Added project into this repository at `external/accessd.webui`.
4. Applied AccessD branding substitutions in UI/docs/metadata while keeping core PHP namespaces and class references unchanged.

## Notes

- This folder is a vendored copy and can be rebased later from upstream as needed.
- Some internal identifiers still use `RaspAP` intentionally to preserve compatibility.
