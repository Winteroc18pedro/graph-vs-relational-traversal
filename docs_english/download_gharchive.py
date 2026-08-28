########################################################################
# ANNOTATED COPY — for learning purposes only.
#
# This is a line-by-line explained duplicate of scripts/download_gharchive.py.
# It is NOT meant to be run as part of the project pipeline — it lives in
# docs_english/ because its purpose is to teach, not to execute. The real, "clean"
# script (with none of this commentary) is scripts/download_gharchive.py.
#
# Read top to bottom — each concept builds on the one before it.
########################################################################


########################################################################
# THE MODULE DOCSTRING (the triple-quoted string below)
#
# In Python, if the very first thing in a file is a string literal (not
# assigned to any variable, just sitting there on its own), Python treats
# it specially: it becomes the "docstring" of the file, stored in a hidden
# attribute called __doc__.
#
# Why bother? Because tools can read it back out automatically:
#   - Running `python scripts/download_gharchive.py --help` prints this
#     text as part of the help output (we wire that up later via
#     `argparse.ArgumentParser(description=__doc__)`).
#   - If someone `import`s this file as a module and runs
#     `help(download_gharchive)` in a Python shell, this text is shown.
#
# It is written in plain English (not a comment starting with #) precisely
# so that it can be extracted and displayed by other programs, not just
# read by a human looking at the source.
########################################################################
"""Download and decompress a single GH Archive hourly dataset file.

Defaults to this project's fixed dataset hour (see README.md), but any
date/hour can be requested for exploration.

Usage:
    python scripts/download_gharchive.py
    python scripts/download_gharchive.py --date 2026-08-27 --hour 15
"""


########################################################################
# IMPORTS
#
# Python's standard library ships with a huge collection of ready-made
# modules (files full of pre-written code) that you can pull into your own
# script with the `import` keyword, instead of writing that functionality
# yourself from scratch. All four imports below are "standard library" —
# meaning they come bundled with Python itself. Nothing needs to be
# separately installed (e.g. no `pip install` required) to run this script.
#
# `import x` makes everything inside module `x` accessible as `x.something`.
# `from x import y` reaches inside module `x` and pulls out just `y`,
# making it accessible directly as `y` (no `x.` prefix needed).
########################################################################

# argparse: turns command-line flags (like `--date 2026-08-27`) typed after
# `python scripts/download_gharchive.py` into structured Python values,
# instead of you having to manually parse sys.argv (the raw list of
# command-line words) yourself.
import argparse

# gzip: lets Python read files compressed with the gzip algorithm (the
# same compression behind the `.gz` file extension) without you having to
# implement decompression yourself.
import gzip

# shutil ("shell utilities"): a grab-bag of high-level file operations.
# We use one function from it: copyfileobj, which copies data from one
# already-open file to another in small chunks.
import shutil

# urllib.request: the standard library's built-in tool for making HTTP(S)
# requests — in our case, just fetching a file from a URL, like what a web
# browser does when you click a download link.
import urllib.request

# `from pathlib import Path` pulls the Path class out of the pathlib
# module. Path represents a filesystem path (a location of a file or
# folder) as an object with useful methods, rather than as a plain string
# you'd have to slice and glue together yourself.
from pathlib import Path


########################################################################
# CONSTANTS
#
# These are just regular Python variables, but written in ALL_CAPS by
# convention. Python has no special "constant" keyword or enforcement —
# ALL_CAPS is purely a human convention meaning "by agreement, this value
# is not meant to be reassigned elsewhere in the code." It signals intent,
# nothing more.
########################################################################

# The specific date and hour this project has chosen as its fixed,
# reproducible dataset (see README.md for why this exact hour was picked).
# Storing them here means every other part of the script can refer to
# DEFAULT_DATE / DEFAULT_HOUR instead of repeating the literal values.
DEFAULT_DATE = "2026-08-27"
DEFAULT_HOUR = 15

# ---------------------------------------------------------------------
# Building DATA_DIR, piece by piece:
#
#   __file__
#     A special variable that Python automatically sets inside every
#     module to the path of that module's own source file. Here, it
#     would be something like:
#       C:\dev\Research\scripts\download_gharchive.py
#
#   Path(__file__)
#     Wraps that string in a Path object, unlocking path-related methods
#     (like the ones used next) instead of having to manipulate the raw
#     string by hand.
#
#   .resolve()
#     Converts the path to an absolute path (starting from the drive
#     root, e.g. `C:\...`) and cleans up anything like `..` segments.
#     This matters because __file__ can sometimes be a relative path,
#     depending on how the script was launched — .resolve() guarantees
#     we always get the full, unambiguous location.
#
#   .parent
#     Path objects understand the folder hierarchy. `.parent` of
#     `C:\dev\Research\scripts\download_gharchive.py` is
#     `C:\dev\Research\scripts` (the folder containing the file).
#
#   .parent.parent
#     Going up one more level: `C:\dev\Research\scripts`'s parent is
#     `C:\dev\Research` — the project root.
#
#   / "data"
#     Path objects overload the `/` operator to mean "join a path
#     segment onto this path" — this is pathlib's readable alternative
#     to os.path.join(). The result is `C:\dev\Research\data`.
#
# Why compute this from __file__ instead of just writing "data" as a
# relative path? Because a relative path like "data" is interpreted
# relative to wherever you happen to be standing in the terminal (your
# "current working directory") when you run the script — which could be
# anywhere. Building the path from __file__ instead guarantees the data/
# folder always ends up next to the project, regardless of which
# directory you were in when you typed the `python ...` command.
# ---------------------------------------------------------------------
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


########################################################################
# FUNCTIONS — WHY BOTHER?
#
# A function is a named, reusable block of code. Instead of writing the
# download logic inline at the bottom of the file, wrapping it in a
# function called `download` means:
#   1. It can be called multiple times with different arguments (e.g.
#      different dates/hours) without duplicating code.
#   2. It could later be imported and reused by other scripts (e.g. a
#      future script that downloads several hours in a loop).
#   3. It gives the block of logic a name, which documents intent.
########################################################################

# ---------------------------------------------------------------------
# Reading the function signature:
#
#   def download(date: str, hour: int, data_dir: Path = DATA_DIR) -> Path:
#
#   `def`            keyword that starts a function definition.
#   `download`       the function's name — how you'll call it later.
#   `date: str`      a parameter named `date`. The `: str` after it is a
#                    "type hint" — a note (not enforced by Python at
#                    runtime!) telling readers and editor tooling "this
#                    is expected to be a string." It's documentation,
#                    not a guarantee — Python will not stop you from
#                    passing something else.
#   `hour: int`      another parameter, hinted as an integer.
#   `data_dir: Path = DATA_DIR`
#                    a parameter hinted as a Path object, with a DEFAULT
#                    VALUE of DATA_DIR. Default values mean the caller
#                    can omit this argument entirely and it will fall
#                    back to DATA_DIR automatically. This is what lets
#                    tests or future code override where files get saved
#                    without changing the function itself.
#   `-> Path`        a return type hint: this function is expected to
#                    hand back a Path object when it finishes.
# ---------------------------------------------------------------------
def download(date: str, hour: int, data_dir: Path = DATA_DIR) -> Path:
    # ---------------------------------------------------------------
    # Ensure the destination folder exists before we try to save
    # anything into it.
    #
    #   .mkdir(...)        "make directory" — creates the folder.
    #   parents=True        also create any missing parent folders
    #                        along the way (not needed here since the
    #                        project root already exists, but it's a
    #                        safe default).
    #   exist_ok=True        do NOT raise an error if the folder
    #                        already exists — just silently continue.
    #                        Without this, re-running the script a
    #                        second time would crash on this line.
    # ---------------------------------------------------------------
    data_dir.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------------
    # f-strings: a string literal prefixed with `f` lets you embed
    # variable values directly inside `{curly braces}`. This line
    # builds a filename like "2026-08-27-15.json.gz" by substituting
    # the actual `date` and `hour` values into the template.
    # ---------------------------------------------------------------
    filename = f"{date}-{hour}.json.gz"

    # Same f-string technique, building the full download URL by
    # inserting the filename into GH Archive's known URL pattern.
    url = f"https://data.gharchive.org/{filename}"

    # The `/` operator again (from pathlib): joins the data_dir Path
    # with the filename string, producing a full Path like
    # C:\dev\Research\data\2026-08-27-15.json.gz — this is where the
    # downloaded (still-compressed) file will be saved.
    gz_path = data_dir / filename

    # print() writes text to the terminal so a human running the
    # script can see what's happening, since the download itself
    # (next line) can take a few seconds with no visible feedback
    # otherwise.
    print(f"Downloading {url} ...")

    # ---------------------------------------------------------------
    # Why not the simpler urllib.request.urlretrieve(url, gz_path)?
    #
    # That was the original approach, and it looks correct — but it
    # fails against GH Archive's server with "HTTP Error 403: Forbidden".
    # Every HTTP request carries a header called User-Agent, which
    # identifies what kind of client is making the request (a browser,
    # a script, etc.). urlretrieve sends a default User-Agent that
    # literally says "Python-urllib/3.14" — and GH Archive's server
    # rejects requests that don't look like they're coming from a real
    # browser, as a basic anti-bot measure. 403 specifically means "I
    # understood your request and I'm refusing it" (as opposed to 404,
    # which would mean "that file doesn't exist").
    #
    # The fix: build the request manually so we can set our own
    # User-Agent header, pretending to be a browser.
    #
    #   urllib.request.Request(url, headers={...})
    #     Creates a Request OBJECT — describing what to fetch and with
    #     what headers — without sending anything yet. This is the
    #     "manual" version of what urlretrieve did automatically
    #     (and inflexibly) under the hood.
    #
    #   urllib.request.urlopen(request)
    #     Actually sends the request over the network and returns a
    #     response object, which behaves like a readable file: you can
    #     stream bytes out of it just like reading from an open file.
    #     It's used here inside the SAME `with` statement as the output
    #     file, so both the network response and the destination file
    #     are properly closed afterward.
    #
    #   shutil.copyfileobj(response, f_out)
    #     Same streaming-copy idea explained later in this file for the
    #     decompression step: read from `response` and write to
    #     `f_out` in small chunks, rather than pulling the entire
    #     download into memory first.
    # ---------------------------------------------------------------
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request) as response, open(gz_path, "wb") as f_out:
        shutil.copyfileobj(response, f_out)
    print(f"Saved to {gz_path}")

    # ---------------------------------------------------------------
    # gz_path.with_suffix(""):
    # Path objects understand file extensions ("suffixes"). `with_suffix`
    # returns a NEW Path with the extension replaced — passing an empty
    # string removes it entirely. So:
    #   C:\...\2026-08-27-15.json.gz   -->   C:\...\2026-08-27-15.json
    # This becomes the target filename for the decompressed output.
    # (Original gz_path is untouched — Path objects are immutable; this
    # creates a new object rather than modifying gz_path in place.)
    # ---------------------------------------------------------------
    json_path = gz_path.with_suffix("")
    print(f"Decompressing to {json_path} ...")

    # ---------------------------------------------------------------
    # THE `with` STATEMENT (a "context manager")
    #
    # Opening a file gives you a live connection to it that ought to be
    # closed again once you're done — otherwise you can leak resources
    # (a subtle bug that gets worse the more files you open over a
    # program's lifetime) or leave partially-written data unflushed to
    # disk. `with ... as ...:` guarantees the file gets closed properly
    # once the indented block underneath finishes — even if an error
    # happens partway through. This is the standard, idiomatic way to
    # work with files in Python; you'll see it constantly.
    #
    # This line opens TWO files at once inside a single `with`, using a
    # comma to combine them:
    #
    #   gzip.open(gz_path, "rb") as f_in
    #     Opens the downloaded .gz file, but using gzip's own open()
    #     function instead of Python's plain built-in open(). This
    #     means reads from f_in are automatically decompressed on the
    #     fly — you never see the raw compressed bytes, only the
    #     decompressed content, as if the file were never compressed
    #     at all. "rb" means "read, binary mode" (raw bytes, not text
    #     — important because JSON Lines data should be handled as
    #     bytes here; we're not trying to interpret/decode it yet,
    #     just move it to another file).
    #
    #   open(json_path, "wb") as f_out
    #     Opens (creating if necessary) the destination plain-text
    #     .json file for writing. "wb" means "write, binary mode" —
    #     matching f_in's binary mode, since we're copying raw bytes
    #     through, not text.
    # ---------------------------------------------------------------
    with gzip.open(gz_path, "rb") as f_in, open(json_path, "wb") as f_out:
        # ---------------------------------------------------------------
        # shutil.copyfileobj(f_in, f_out):
        # Reads from f_in and writes to f_out in small chunks (a
        # default internal buffer size), looping until f_in is
        # exhausted. The key benefit over something like
        # `f_out.write(f_in.read())` is memory usage: `f_in.read()`
        # would load the ENTIRE decompressed file into memory in one
        # go before writing any of it out. For a huge file, that could
        # use a large amount of RAM all at once. copyfileobj instead
        # streams it through in small pieces, keeping memory usage low
        # regardless of the file's total size.
        # ---------------------------------------------------------------
        shutil.copyfileobj(f_in, f_out)

    # Once the `with` block above ends, both files have been
    # automatically closed. Now we tell the user we're done.
    print(f"Done: {json_path}")

    # Hand back the path to the final, decompressed file, so that
    # calling code (see main(), below) — or anyone who imports this
    # function from another script — can immediately know where the
    # usable data ended up, without having to reconstruct the path
    # themselves.
    return json_path


########################################################################
# parse_args(): turning command-line flags into a structured object
########################################################################
def parse_args() -> argparse.Namespace:
    # ---------------------------------------------------------------
    # argparse.ArgumentParser(...) creates a "parser" object that knows
    # how to read the list of words typed after `python
    # scripts/download_gharchive.py` on the command line (e.g.
    # `--date 2026-08-27 --hour 15`) and turn them into Python values.
    #
    # `description=__doc__` reuses this file's module docstring (the
    # triple-quoted string at the very top of the file) as the
    # descriptive text shown when someone runs the script with
    # `--help`. This is exactly the "docstrings can be read back by
    # tools" idea mentioned at the top of this file, in action.
    # ---------------------------------------------------------------
    parser = argparse.ArgumentParser(description=__doc__)

    # ---------------------------------------------------------------
    # Registering the `--date` flag:
    #   "--date"              the flag's name as typed on the command
    #                          line (e.g. `--date 2026-08-27`).
    #   default=DEFAULT_DATE   if the user doesn't pass `--date` at
    #                          all, use this value instead — this is
    #                          what makes running the script with NO
    #                          arguments still work, using the
    #                          project's fixed dataset date.
    #   help=...               shown in the `--help` output, explaining
    #                          what this flag does and what its
    #                          current default is.
    # (No `type=` is given here, so argparse treats the value as a
    # plain string by default — which is what we want for a date
    # written as "YYYY-MM-DD".)
    # ---------------------------------------------------------------
    parser.add_argument(
        "--date",
        default=DEFAULT_DATE,
        help=f"Date in YYYY-MM-DD format (default: {DEFAULT_DATE})",
    )

    # ---------------------------------------------------------------
    # Registering the `--hour` flag:
    #   type=int               unlike --date, we DO specify a type
    #                          here. Command-line input always arrives
    #                          as text (e.g. the characters "1", "5"),
    #                          so `type=int` tells argparse to convert
    #                          it to an actual Python integer (15)
    #                          before handing it back to us — and to
    #                          raise a clear error automatically if the
    #                          user types something that isn't a valid
    #                          integer (e.g. `--hour fifteen`).
    #   default=DEFAULT_HOUR    same idea as before: fall back to the
    #                          project's fixed hour if not specified.
    #   choices=range(0, 24)    restricts valid values to 0 through 23
    #                          inclusive (range(0, 24) generates
    #                          0,1,2,...,23). If the user passes
    #                          something outside that range, argparse
    #                          rejects it automatically with an error
    #                          message, before our own code ever runs
    #                          — we don't need to write that validation
    #                          ourselves.
    #   metavar="[0-23]"        purely cosmetic: controls how the
    #                          argument is displayed in the `--help`
    #                          text, showing "[0-23]" instead of
    #                          argparse's default (which would try to
    #                          list all 24 individual choices).
    # ---------------------------------------------------------------
    parser.add_argument(
        "--hour",
        type=int,
        default=DEFAULT_HOUR,
        choices=range(0, 24),
        metavar="[0-23]",
        help=f"UTC hour, 0-23 (default: {DEFAULT_HOUR})",
    )

    # ---------------------------------------------------------------
    # parser.parse_args():
    # Actually reads the real command-line arguments the script was
    # launched with (Python exposes these internally via sys.argv) and
    # returns a "Namespace" object — think of it as a simple container
    # where each flag becomes an attribute. After this line, you can
    # access `args.date` and `args.hour` as ordinary Python values
    # (a str and an int respectively), fully parsed and validated.
    # ---------------------------------------------------------------
    return parser.parse_args()


########################################################################
# main(): the script's entry point
#
# By convention, Python scripts often gather their top-level logic into
# a function called `main`, rather than writing that logic loose at the
# bottom of the file. It's not a special/magic name to Python itself —
# it's just a strong convention — but it keeps the "what happens when
# you run this file" logic organized in one clearly-named place.
########################################################################
def main() -> None:
    # `-> None` in the signature is a type hint meaning "this function
    # doesn't return a meaningful value" (it just performs actions).

    # Ask parse_args() (defined above) to read and validate the
    # command-line flags, giving us back a Namespace with .date and
    # .hour already filled in (either from what the user typed, or
    # from the defaults).
    args = parse_args()

    # Call the download() function defined earlier, passing in the
    # parsed date and hour. Note `data_dir` is NOT passed here — that
    # parameter's default value (DATA_DIR) is used automatically,
    # since we don't need to override it in normal usage.
    download(args.date, args.hour)


########################################################################
# THE `if __name__ == "__main__":` GUARD
#
# Every Python module (file) automatically gets a built-in variable
# called `__name__`. Its value depends on HOW the file is being used:
#
#   - If you run the file directly from the command line
#     (`python scripts/download_gharchive.py`), Python sets
#     `__name__` to the string "__main__" for that file.
#
#   - If, instead, this file is imported from somewhere else
#     (`import download_gharchive` inside another script), Python sets
#     `__name__` to the module's own name ("download_gharchive")
#     instead of "__main__".
#
# This `if` check therefore means: "only actually call main() — i.e.
# only actually perform a download — when this file is executed
# directly, not when it's merely imported."
#
# Why does that distinction matter? It means someone could write a
# different script later that does:
#
#   from download_gharchive import download
#   download("2026-08-20", 9)
#
# ...and reuse the download() function for a different hour, WITHOUT
# triggering the file's own default download as a side effect just
# from importing it. Without this guard, importing the file would
# immediately run main() too, which is almost never what you want from
# an import.
########################################################################
if __name__ == "__main__":
    main()
