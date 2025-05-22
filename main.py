import csv
import html
import typer
from pathlib import Path
from typing import List, Tuple, Dict, Any
from jinja2 import Environment, select_autoescape # For templating

# Create a Typer app instance
app = typer.Typer()

# HTML Template for Jinja2 - Timestamp and User login metadata removed
BOOKMARK_TEMPLATE_CONTENT = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<!-- This is an automatically generated file. -->
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Pocket Non-Archived Bookmarks</H1>
<DL><p>
{% for bookmark in bookmarks %}
    <DT><A HREF="{{ bookmark.url|e }}" ADD_DATE="{{ bookmark.add_date }}" TAGS="{{ bookmark.tags|e }}"{% if bookmark.toread %} TOREAD="yes"{% endif %}>{{ bookmark.title|e }}</A>
{% endfor %}
</DL><p>
"""

def _convert_data_to_html_bookmarks(
    csv_filepaths: List[Path],
    output_html_filepath: Path
) -> Tuple[int, int]:
    """
    Core logic to convert multiple Pocket CSV export files into a single HTML
    bookmark file for Pinboard using Jinja2 templating. Includes only non-archived
    items and marks them as "to read".

    Args:
        csv_filepaths: A list of paths to the Pocket CSV files.
        output_html_filepath: The path for the generated HTML bookmark file.

    Returns:
        A tuple containing (processed_count, skipped_archived_count).
    """
    processed_count: int = 0
    skipped_archived_count: int = 0
    bookmarks_data: List[Dict[str, Any]] = []

    env = Environment(
        loader=None, # Template is a string
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.from_string(BOOKMARK_TEMPLATE_CONTENT)

    for csv_filepath in csv_filepaths:
        typer.echo(f"Processing file: {csv_filepath}...")
        try:
            with open(csv_filepath, 'r', newline='', encoding='utf-8') as csvfile:
                content: str = csvfile.read()
                if content.startswith('\ufeff'): # BOM
                    content = content[1:]
                
                csvreader: csv.DictReader[str] = csv.DictReader(content.splitlines())
                
                for row in csvreader:
                    status: str = row.get('status', '').strip().lower()
                    
                    if status == "archive":
                        skipped_archived_count += 1
                        continue

                    bookmark_item = {
                        "url": row.get('url', ''),
                        "title": row.get('title', ''),
                        "add_date": row.get('time_added', ''),
                        "tags": row.get('tags', ''),
                        "toread": True
                    }
                    bookmarks_data.append(bookmark_item)
                    processed_count += 1
        except FileNotFoundError:
             typer.secho(f"Error: File not found - {csv_filepath}.", fg=typer.colors.RED)
        except Exception as e:
            typer.secho(f"Error processing file {csv_filepath}: {e}", fg=typer.colors.RED)
    
    html_output = template.render(
        bookmarks=bookmarks_data # Only bookmarks data is now passed
    )

    try:
        with open(output_html_filepath, 'w', encoding='utf-8') as htmlfile:
            htmlfile.write(html_output)
    except Exception as e:
        typer.secho(f"Error writing to output file {output_html_filepath}: {e}", fg=typer.colors.RED)
        return 0, skipped_archived_count

    return processed_count, skipped_archived_count

@app.command()
def convert(
    csv_files: List[Path] = typer.Argument(
        ...,
        help="Paths to the Pocket CSV export files. Can specify multiple files.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
    ),
    output_file: Path = typer.Option(
        "pinboard_import.html",
        "--output",
        "-o",
        help="Path for the generated HTML bookmark file.",
        writable=True,
        resolve_path=True,
    )
):
    """
    Converts Pocket CSV export files to a Pinboard-compatible HTML bookmark file
    using Jinja2 templating, filtering out archived items.
    """
    typer.secho(f"Starting conversion...", fg=typer.colors.CYAN)
    
    processed_count, skipped_archived_count = _convert_data_to_html_bookmarks(
        csv_filepaths=csv_files,
        output_html_filepath=output_file
    )

    if processed_count > 0 or output_file.exists():
        typer.secho(f"\nConversion complete.", fg=typer.colors.GREEN)
        typer.echo(f"Processed {processed_count} non-archived bookmarks.")
        typer.echo(f"Skipped {skipped_archived_count} archived bookmarks.")
        typer.secho(f"HTML file saved as: {output_file.resolve()}", fg=typer.colors.GREEN)
        # Removed timestamp and user from this final message
    else:
        typer.secho(f"\nConversion finished, but no bookmarks were processed or output file not created.", fg=typer.colors.YELLOW)

if __name__ == "__main__":
    app()