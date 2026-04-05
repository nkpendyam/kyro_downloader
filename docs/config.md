# Configuration Reference

## Config File Location
Config files are searched in this order:
1. `~/.config/kyro/config.yaml`
2. `~/.kyro/config.yaml`
3. `./config/config.yaml`
4. Explicit path via `--config` flag

## All Options

### General
```yaml
general:
  output_path: "./downloads"      # Default download directory
  notifications: true              # Desktop notifications
  auto_update: true                # Auto-check yt-dlp updates
  check_duplicates: true           # Skip duplicate downloads
  show_thumbnail: false            # Show thumbnail in CLI
```

### Download
```yaml
download:
  max_retries: 3                   # Max retry attempts
  concurrent_workers: 3            # Parallel downloads
  rate_limit: null                 # Rate limit (e.g. "1M")
  proxy: null                      # Proxy URL
  fragment_retries: 10             # Fragment retry count
  concurrent_fragments: 4          # Parallel fragment downloads
  prefer_format: "mp4"             # Preferred container format
```

### UI
```yaml
ui:
  theme: "dark"                    # GUI theme
  language: "en"                   # Interface language
  show_thumbnail: false            # Show thumbnails in CLI
```

## Environment Variables
All settings can be overridden via environment variables using the `KYRO_` prefix with `__` for nesting.

```bash
export KYRO_DOWNLOAD__MAX_RETRIES=5
export KYRO_GENERAL__OUTPUT_PATH="/mnt/downloads"
export KYRO_DOWNLOAD__CONCURRENT_WORKERS=8
```

## CLI Config Management
```bash
kyro config show       # Display current configuration
kyro config save       # Save current config to file
kyro config reset      # Reset to defaults and save
kyro config --path /custom/path.yaml show
```
