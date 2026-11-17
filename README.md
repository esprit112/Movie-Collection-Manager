# Movie Collection Manager

A desktop catalogue for a film collection, built with PySide6 and The Movie Database.

Built for the specific problem of owning several hundred films across drives and shelves and having no idea, at the moment of choosing one, what you actually own and what you have already watched.

## What it does

- **Search TMDB and add a film.** Title and year go in; details, artwork and metadata come back.
- **Import files you already have.** Point it at a folder and add what is there, rather than typing a catalogue by hand.
- **Posters.** Artwork is fetched from TMDB and shown with the record, so the shelf looks like a shelf.
- **Watched state and a personal rating.** Track what you have seen, and what you thought of it, separately from what the internet thought.
- **Detail panel.** A selected film opens with its poster, metadata and collection statistics.
- **CSV export.** The collection leaves the app when you want it to.
- **Backups.** The SQLite database can be backed up and restored; a restore takes a safety copy first, and backup history is recorded.
- **Cinema theme.** Dark, high-contrast, built for browsing rather than data entry.
- **Logging.** Errors and TMDB calls go to `movie_app.log` next to the app.

## Requirements

```
PySide6>=6.6.0
pillow>=10.0.0
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
```

```bash
pip install -r requirements.txt
```

A free TMDB API key is needed. Create an account at https://www.themoviedb.org, then request a key under Settings, API. The app asks for it on first run and stores it in `tmdb_api_key.txt` beside the database, as plain text.

## Run

```bash
python main.py
```

## Files

```
main.py               window, table, detail panel, dialogs
database.py           SQLite schema, queries, backup and restore
tmdb_api.py           TMDB search and details, poster handling
themes.py             light and dark palettes
cinema_colors.py      the cinema colour scheme
utils.py              logging, helpers
config.json           settings: window, theme and preferences
tmdb_api_key.txt      TMDB key, stored as plain text
movie_app.log         log file
```

The database lives beside the application. Back it up before moving the folder to another machine.

## Limits

- **TMDB metadata is other people's work.** Posters and descriptions remain TMDB's and the rights holders'; this app is a private catalogue, not a distribution tool.
- **The free TMDB tier is rate-limited.** Large imports pause and resume; they are not instant.
- **No tests.** It is a personal utility, and it is honest about that.
- **One library, one database.** There is no multi-user mode and no sync between machines; copy the database file.
- **Restore overwrites.** It takes a safety copy first, but read the confirmation before clicking through it.

## Licence

MIT. See [LICENSE](LICENSE).

---

Built by [Martin Greer](https://github.com/esprit112).
