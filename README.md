# The Final Hours of Portal 2 - Online Service Reimplementation

This is my preservation project for *The Final Hours of Portal 2*, the interactive Flash ebook written by Geoff Keighley.

The original ebook still works, but many of its online features disappeared as websites, APIs, and old media players went offline. This project recreates those endpoints with a small FastAPI server so the original ebook can keep using them.

This repo contains the [server software](https://github.com/nikolan123/TFHoP2-server) only. Use the [Windows x64 patcher](https://builds.nikolan.net/download/nikolan123_s_TFHoP2-patcher/latest/windows-patcher/Portal-2-The-Final-Hours-Patcher.exe), view its [source code](https://github.com/nikolan123/TFHoP2-patcher), or read the [blog post](https://nikolan.net/posts/portal2/).

Run the server from this directory with:

```powershell
uv sync
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

>[!WARNING]
> **Help Needed**
> There are 2 polls and one unknown web embed that have not been archived. If you know what used to be there or the poll questions, PLEASE open an issue or contact me another way. The complete list of online-dependent content and its current preservation status is in the [preservation checklist](checklist.md).

Unofficial fan preservation project by Niko. Not affiliated with Valve or the original creators.
