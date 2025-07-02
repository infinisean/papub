import os
import re
import argparse
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from rich import print
import subprocess
import shutil

console = Console()

def get_video_info(file_path):
    try:
        result = subprocess.run(
            ['ffmpeg', '-i', file_path],
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        output = result.stderr
        # Extract video quality and audio channels from ffmpeg output
        quality_match = re.search(r'Stream.*Video.*(\d{3,4}x\d{3,4})', output)
        audio_match = re.search(r'Stream.*Audio.*(\d+) channels', output)
        quality = quality_match.group(1) if quality_match else "UNKNOWN"
        audio_channels = audio_match.group(1) if audio_match else "UNKNOWN"
        return quality, audio_channels
    except Exception as e:
        console.print(f"[yellow]Error analyzing file {file_path}: {e}[/yellow]")
        return "UNKNOWN", "UNKNOWN"

def find_movies(directory):
    movie_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.getsize(file_path) > 500 * 1024 * 1024:  # Minimum size 500MB
                imdb_match = re.search(r'\[tt\d{7,8}\]', file)
                if imdb_match:
                    imdb_id = imdb_match.group(0)
                    movie_files.append((file_path, imdb_id))
    return movie_files

def process_movies(movie_files):
    duplicates = {}
    needs_quality = []

    for file_path, imdb_id in movie_files:
        quality_match = re.search(r'(\d{3,4}p)', file_path)
        quality = quality_match.group(1) if quality_match else None
        audio_match = re.search(r'(\d+ch)', file_path)
        audio_channels = audio_match.group(1) if audio_match else None

        if not quality or not audio_channels:
            quality, audio_channels = get_video_info(file_path)
            if quality == "UNKNOWN" or audio_channels == "UNKNOWN":
                needs_quality.append(file_path)

        if imdb_id not in duplicates:
            duplicates[imdb_id] = []
        duplicates[imdb_id].append((file_path, quality, audio_channels))

    return duplicates, needs_quality

def display_and_manage_duplicates(duplicates, directory, live_mode):
    space_saved = 0
    deleted_files = []

    remove_me_dir = os.path.join(directory, "REMOVE_ME")
    if not live_mode and not os.path.exists(remove_me_dir):
        os.makedirs(remove_me_dir)

    for imdb_id, files in duplicates.items():
        if len(files) > 1:
            table = Table(title=f"Duplicates for {imdb_id}")
            table.add_column("Rank", justify="right", style="cyan", no_wrap=True)
            table.add_column("Title", style="magenta")
            table.add_column("Quality", style="green")
            table.add_column("Audio Channels", style="green")
            table.add_column("Size (MB)", style="green")

            sorted_files = sorted(files, key=lambda x: (x[1], x[2]), reverse=True)
            for rank, (file_path, quality, audio_channels) in enumerate(sorted_files, start=1):
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                color = "green" if rank == 1 else "red"
                table.add_row(str(rank), file_path, quality, audio_channels, f"{size_mb:.2f}", style=color)

            console.print(table)

            choice = Prompt.ask("Choose the best movie to keep", choices=[str(i) for i in range(len(sorted_files) + 1)], default="1")
            if choice != "0":
                best_index = int(choice) - 1
                for i, (file_path, _, _) in enumerate(sorted_files):
                    if i != best_index:
                        if live_mode:
                            os.remove(file_path)
                        else:
                            shutil.move(file_path, remove_me_dir)
                        deleted_files.append(file_path)
                        space_saved += os.path.getsize(file_path)

    console.print("\nDeleted Files:")
    for file in deleted_files:
        console.print(f"[red]{file}[/red]")

    console.print(f"\nTotal Space Saved: {space_saved / (1024 * 1024):.2f} MB")

def main():
    parser = argparse.ArgumentParser(description="Manage movie files in a directory.")
    parser.add_argument("directory", help="Directory to scan for movie files")
    parser.add_argument("-l", "--live", action="store_true", help="Enable live mode to delete files instead of moving them")
    args = parser.parse_args()

    movie_files = find_movies(args.directory)
    duplicates, needs_quality = process_movies(movie_files)

    if needs_quality:
        with open("needs_quality.txt", "w") as f:
            for file in needs_quality:
                f.write(f"{file}\n")
        console.print("[yellow]Some files need quality information added. See needs_quality.txt for details.[/yellow]")

    display_and_manage_duplicates(duplicates, args.directory, args.live)

if __name__ == "__main__":
    main()