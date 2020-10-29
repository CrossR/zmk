import argparse
import json
import re
import pathlib

PARSER = argparse.ArgumentParser()
PARSER.add_argument("keymap_path", type=str, help="Path to keymap file.")
PARSER.add_argument(
    "-s",
    "--substitution_file",
    type=str,
    help="JSON file containing substitutions to be made.",
    default="substitutions.json",
)
PARSER.add_argument(
    "-d",
    "--dry-run",
    action="store_true",
    default=False,
    help="Report keycodes that would be changed, but don't perform change.",
)
ARGS = PARSER.parse_args()

# Given a keymap path and a list of substitutions, perform any required
# replacements.
def format_file(keymap_file_path, substitutions):

    # Read the keymap file as a binary file, then decode.
    # This is needed to deal with cases where there is unicode in the keymap file.
    keymap_file_bytes = keymap_file_path.read_bytes()
    keymap_file = keymap_file_bytes.decode("utf-8").split("\n")

    for (old_keycode, new_keycode) in substitutions:

        # Only match against things that look like a keycode.
        #
        # Looks like a keycode if its &inc_dec_[kc]p or any two letters.
        # Require a word boundary either side of the code just to prevent
        # weird partial matches (i.e. VOLU inside of M_VOLU).
        old_keycode_regex = re.compile(rf"(&(inc_dec_[kc]p|\w{{2}}) \w*)\b{old_keycode}\b")

        lines_to_update = [
            i for i, line in enumerate(keymap_file) if old_keycode_regex.search(line)
        ]

        if not lines_to_update:
            continue

        if new_keycode is None:
            print(
                f"{keymap_file_path} contains {old_keycode}, which currently has no replacement!"
            )
            continue

        if ARGS.dry_run:
            print(
                f"Would have replaced {old_keycode} with {new_keycode} on {len(lines_to_update)} lines."
            )
            continue

        # First capture group then new keycode.
        replacement_keycode = f"\\1{new_keycode}"

        for line in lines_to_update:
            keymap_file[line] = old_keycode_regex.sub(
                replacement_keycode, keymap_file[line]
            )

    # Similarly, want to write the file back as a binary file, to keep any
    # unicode.
    new_keymap_file = "\n".join(keymap_file)
    new_keymap_file_bytes = new_keymap_file.encode("utf-8")
    pathlib.Path(keymap_file_path).write_bytes(new_keymap_file_bytes)


# Load the given JSON file and parse it into a list of Python dictionaries for
# later use.
def load_substitutions(substitution_file_path):
    substitutions = []

    with open(substitution_file_path) as substitution_file:
        substitution_json = json.load(substitution_file)
        substitutions = [(s["from"], s["to"]) for s in substitution_json]

    return substitutions


def main():

    json_file_path = pathlib.Path(ARGS.substitution_file)

    if not json_file_path.is_file():
        print(f"{ARGS.substitution_file} doesn't point to a file! Aborting...")
        return
    elif not json_file_path.suffix == ".json":
        print(f"{ARGS.substitution_file} doesn't point to a JSON file! Aborting...")
        return

    substitutions = load_substitutions(ARGS.substitution_file)

    keymap_file_path = pathlib.Path(ARGS.keymap_path)

    # If path is a directory, get all keymap files.
    # If its just a file, format that single file.
    if keymap_file_path.is_dir():
        for keymap_file in keymap_file_path.glob("**/*.keymap"):
            print(f"Sorting out {str(keymap_file)}....")
            format_file(keymap_file, substitutions)
    elif keymap_file_path.is_file() and keymap_file_path.suffix == ".keymap":
        format_file(keymap_file_path, substitutions)
    else:
        print(
            f"{ARGS.keymap_path} doesn't point to a folder or a keymap file! Aborting..."
        )
        return


if __name__ == "__main__":
    main()
