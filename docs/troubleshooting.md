# Troubleshooting

## Common Issues

### EXE fails to launch
- **Cause**: Build/runtime dependency mismatch (for example missing CustomTkinter in source runs) or unsupported Python for build tooling
- **Fix**: Ensure you're using Python 3.11-3.12 for building. The pre-built EXE should work on any Windows 10/11 system.

### "Failed to extract auth file" error
- **Cause**: GUI initialization issues
- **Fix**: Restart the application and restart

### Download fails with "No video-only formats"
- **Cause**: Some videos (especially age-restricted) don't have separate video/audio streams
- **Fix**: Use `--format` to specify a combined format, or try without quality restrictions

### FFmpeg not found
- **Cause**: FFmpeg not in PATH
- **Fix**: Install FFmpeg and add to PATH, or set `FFMPEG_PATH` environment variable

### Slow download speeds
- **Cause**: Rate limiting or network issues
- **Fix**: Try `--proxy` flag, or increase `concurrent_fragments` in config

### yt-dlp update fails
- **Cause**: Network issues or pip permissions
- **Fix**: Run `pip install --upgrade yt-dlp` manually, or use `kyro --update`

### Config not saving
- **Cause**: Permission issues with `~/.config/kyro/` directory
- **Fix**: Run `mkdir -p ~/.config/kyro` and ensure write permissions

### GUI crashes on startup
- **Cause**: CustomTkinter 5.2 API incompatibility (fixed in latest version)
- **Fix**: Update to the latest version from GitHub Releases

## Getting Help
- **GitHub Issues**: https://github.com/nkpendyam/kyro_downloader/issues
- **Logs**: Check `~/.config/kyro/kyro.log` for detailed error logs
- **Verbose mode**: Run with `--verbose` flag for detailed output
