# Convert Pocket CSV files to HTML

Because [Pocket is shutting down](https://support.mozilla.org/en-US/kb/future-of-pocket),
I exported my bookmarks, but the link was a ZIP file of CSV files.

I needed a single HTML file to import elsewhere (I chose Pinboard, specifically).

To run, use [`uv`](https://docs.astral.sh/uv/):

```
uv run main.py -o bookmarks.html *.csv
```
