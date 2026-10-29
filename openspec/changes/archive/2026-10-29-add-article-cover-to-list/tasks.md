## 1. Payload (`hub.py`)

- [x] 1.1 Add a `cover` field to each `list_payload` row, read defensively (missing field → `""`), and verify `tests/test_hub.py` gains a passing case for a non-empty cover plus the missing-field path (`python -m unittest tests.test_hub`).

## 2. List template (`web/list.html`)

- [x] 2.1 Make each row a cover-plus-content flex layout that renders the cover HTML at the left when `cover` is non-empty and falls back to the current title-and-skills layout when it is empty, with CSS constraining the thumbnail to a fixed max height while preserving aspect ratio; update the module's `LSA_DATA` contract comment and verify the template loads without a console error (`python -m unittest tests.test_hub`).

- [x] 2.2 (post-archive fix) Add `<base href="/">` to `list.html` so cover `src` values resolve against Anki's media-server root instead of the `/_anki/` page path. Anki 26.9.3's `AnkiWebView.setHtml` serves pages from `http://127.0.0.1:<port>/_anki/legacyPageData?id=N` (no longer QWebEngine `setHtml` with a file base), so a bare relative `src="paste-x.jpg"` resolved to `/_anki/paste-x.jpg` → 404 "Invalid path" (media files are served at the server root: verified live `GET /paste-x.jpg` → 200 `image/jpeg`). Guarded by `test_base_tag_rebases_relative_urls_to_media_root` in `tests/test_hub.py` — the selftest's hub check only probes DOM structure, not image loading, so the regression would otherwise stay invisible.
