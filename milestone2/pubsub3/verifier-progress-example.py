import time
import random
import asyncio
from rich.console import Console
from rich.live import Live
from rich.text import Text

console = Console()

class FileStatus:
    def __init__(self, filename):
        self.filename = filename
        self.confirm_status = "pending"  # pending, confirming, success, error
        self.fetch_status = "pending"  # pending, fetching, success, error
        self.verify_status = "pending"  # pending, verifying, success, error
        self.confirm_error = None
        self.fetch_error = None
        self.verify_error = None
        self.completed = False  # Track if file is fully done
        self.started = False  # Track if file has started processing

def get_status_icon(status):
    """Return the appropriate icon for a status."""
    if status == "pending":
        return "[dim]·[/dim]"
    elif status in ["confirming", "fetching", "verifying"]:
        return "[cyan]●[/cyan]"
    elif status == "success":
        return "[green]✓[/green]"
    elif status == "error":
        return "[red]✗[/red]"
    return "?"

def create_status_display(file_statuses):
    """Create a display showing all file statuses as individual lines."""
    lines = []

    # Only show files that have started and haven't been completed yet
    for fs in file_statuses:
        if fs.started and not fs.completed:
            # If confirm failed, don't show fetch/verify status
            if fs.confirm_status == "error":
                fetch_icon = " "
                verify_icon = " "
            # If fetch failed, don't show verify status
            elif fs.fetch_status == "error":
                fetch_icon = get_status_icon(fs.fetch_status)
                verify_icon = " "
            else:
                fetch_icon = get_status_icon(fs.fetch_status)
                verify_icon = get_status_icon(fs.verify_status)

            # Build the base line
            line = f"{get_status_icon(fs.confirm_status)} {fetch_icon} {verify_icon} {fs.filename}"

            # Append error message if there is one
            if fs.confirm_error:
                error_msg = fs.confirm_error.split(": ", 1)[-1]
                line += f"[red]: {error_msg}[/red]"
            elif fs.fetch_error:
                error_msg = fs.fetch_error.split(": ", 1)[-1]
                line += f"[red]: {error_msg}[/red]"
            elif fs.verify_error:
                error_msg = fs.verify_error.split(": ", 1)[-1]
                line += f"[red]: {error_msg}[/red]"

            lines.append(line)

    return "\n".join(lines) if lines else "[dim]No files currently processing...[/dim]"

async def simulate_confirm(file_status):
    """Simulate confirming hash on chain."""
    file_status.confirm_status = "confirming"
    await asyncio.sleep(random.uniform(20, 60))

    # 10% chance of failure
    if random.random() < 0.1:
        file_status.confirm_status = "error"
        file_status.confirm_error = f"Hash confirmation failed for {file_status.filename}: Transaction not found"
        return False

    file_status.confirm_status = "success"
    return True

async def simulate_download(file_status):
    """Simulate downloading a file via IPFS."""
    file_status.fetch_status = "fetching"
    await asyncio.sleep(random.uniform(1, 10))

    # 20% chance of failure
    if random.random() < 0.2:
        file_status.fetch_status = "error"
        file_status.fetch_error = f"Failed to fetch {file_status.filename}: IPFS timeout"
        return False

    file_status.fetch_status = "success"
    return True

async def simulate_verify(file_status):
    """Simulate verifying a file."""
    file_status.verify_status = "verifying"
    await asyncio.sleep(random.uniform(0.3, 1.5))

    # 15% chance of failure
    if random.random() < 0.15:
        file_status.verify_status = "error"
        file_status.verify_error = f"Verification failed for {file_status.filename}: Checksum mismatch"
        return False

    file_status.verify_status = "success"
    return True

async def process_file(file_status, live):
    """Process a single file with confirmation parallel to fetch+verify."""
    file_status.started = True

    # Start confirmation task (runs independently)
    confirm_task = asyncio.create_task(simulate_confirm(file_status))

    # Start fetch→verify chain (runs independently until fetch completes)
    download_success = await simulate_download(file_status)

    if not download_success:
        # Fetch failed - wait for confirm to finish before returning
        await confirm_task

        # Log the error and mark as completed
        fetch_icon = get_status_icon(file_status.fetch_status)
        error_msg = file_status.fetch_error.split(": ", 1)[-1]

        if file_status.confirm_status == "error":
            # Both confirm and fetch failed - show confirm error
            live.console.print(f"[red]✗[/red]   {file_status.filename}[red]: {file_status.confirm_error.split(': ', 1)[-1]}[/red]")
        else:
            # Only fetch failed
            confirm_icon = get_status_icon(file_status.confirm_status)
            live.console.print(f"{confirm_icon} [red]✗[/red]   {file_status.filename}[red]: {error_msg}[/red]")

        file_status.completed = True
        return False

    # Fetch succeeded, now verify (depends on fetch)
    verify_success = await simulate_verify(file_status)

    if not verify_success:
        # Verify failed - wait for confirm to finish before returning
        await confirm_task

        # Log the error and mark as completed
        error_msg = file_status.verify_error.split(": ", 1)[-1]

        if file_status.confirm_status == "error":
            # Confirm failed, verify failed
            live.console.print(f"[red]✗[/red] [green]✓[/green] [red]✗[/red] {file_status.filename}[red]: {file_status.confirm_error.split(': ', 1)[-1]}[/red]")
        else:
            # Only verify failed
            confirm_icon = get_status_icon(file_status.confirm_status)
            live.console.print(f"{confirm_icon} [green]✓[/green] [red]✗[/red] {file_status.filename}[red]: {error_msg}[/red]")

        file_status.completed = True
        return False

    # Both chains succeeded - wait for confirmation if it's still running
    confirm_success = await confirm_task

    if not confirm_success:
        # Only confirm failed
        error_msg = file_status.confirm_error.split(": ", 1)[-1]
        live.console.print(f"[red]✗[/red] [green]✓[/green] [green]✓[/green] {file_status.filename}[red]: {error_msg}[/red]")
        file_status.completed = True
        return False

    # All three phases succeeded
    await asyncio.sleep(0.8)
    file_status.completed = True
    live.console.print(f"[green]✓ ✓ ✓[/green] {file_status.filename}")

    return True

async def main():
    # Create a list of files to process
    files = [
        "dataset_part1.tar.gz",
        "dataset_part2.tar.gz",
        "model_weights.pkl",
        "config.json",
        "training_data.csv",
        "validation_data.csv",
        "test_data.csv",
        "metadata.xml",
        "readme.md",
        "requirements.txt",
        "dataset_part1.tar.gz",
        "dataset_part2.tar.gz",
        "model_weights.pkl",
        "config.json",
        "training_data.csv",
        "validation_data.csv",
        "test_data.csv",
        "metadata.xml",
        "readme.md",
        "requirements.txt",
        "dataset_part1.tar.gz",
        "dataset_part2.tar.gz",
        "model_weights.pkl",
        "config.json",
        "training_data.csv",
        "validation_data.csv",
        "test_data.csv",
        "metadata.xml",
        "readme.md",
        "requirements.txt",
        "dataset_part1.tar.gz",
        "dataset_part2.tar.gz",
        "model_weights.pkl",
        "config.json",
        "training_data.csv",
        "validation_data.csv",
        "test_data.csv",
        "metadata.xml",
        "readme.md",
        "requirements.txt",
        "dataset_part1.tar.gz",
        "dataset_part2.tar.gz",
        "model_weights.pkl",
        "config.json",
        "training_data.csv",
        "validation_data.csv",
        "test_data.csv",
        "metadata.xml",
        "readme.md",
        "requirements.txt",
        "docker_image.tar",
        "logs_archive.zip",
        "backup_2024.sql",
        "assets_bundle.zip",
        "documentation.pdf",
    ]

    file_statuses = [FileStatus(f) for f in files]

    console.print("[cyan]Starting file download and verification process...[/cyan]\n")

    # Use Live display to update the status in real-time
    with Live(create_status_display(file_statuses), console=console, refresh_per_second=10) as live:
        # Create a semaphore to limit concurrent processing
        semaphore = asyncio.Semaphore(9)  # Process 9 files at a time

        async def process_with_semaphore(fs):
            async with semaphore:
                return await process_file(fs, live)

        # Create tasks (not just coroutines)
        tasks = [asyncio.create_task(process_with_semaphore(fs)) for fs in file_statuses]

        # Update display periodically while tasks are running
        async def update_display():
            while not all(task.done() for task in tasks):
                live.update(create_status_display(file_statuses))
                await asyncio.sleep(0.1)
            live.update(create_status_display(file_statuses))

        # Run both the tasks and the display updater
        await asyncio.gather(update_display(), *tasks)

    # Summary
    console.print("\n[cyan]Process Complete![/cyan]")
    successful = sum(1 for fs in file_statuses if fs.confirm_status == "success" and fs.fetch_status == "success" and fs.verify_status == "success")
    console.print(f"Successfully processed: [green]{successful}/{len(files)}[/green] files")

    failed = len(files) - successful
    if failed > 0:
        console.print(f"Errors encountered: [red]{failed}[/red]")

if __name__ == "__main__":
    asyncio.run(main())

