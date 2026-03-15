import time
import random
import asyncio
from rich.console import Console
from rich.live import Live
from rich.text import Text

console = Console()

# TODO also add a local_only option for verification messages from the script itself
class FileStatus:
    def __init__(self, filename, onchain_only=False):
        self.filename = filename
        self.onchain_only = onchain_only  # True for blockchain events
        self.confirm_status = "pending"  # pending, confirming, success, error
        self.fetch_status = "pending" if not onchain_only else None
        self.verify_status = "pending" if not onchain_only else None
        self.confirm_error = None
        self.fetch_error = None
        self.verify_error = None
        self.completed = False
        self.started = False

def get_status_icon(status):
    """Return the appropriate icon for a status."""
    if status == "pending":
        return "[dim]·[/dim]"
    elif status in ["confirming", "fetching", "verifying"]:
        return "[cyan]●[/cyan]"
    elif status == "success":
        return "[green]✔[/green]"  # Heavy check mark (U+2714)
    elif status == "error":
        return "[red]✖[/red]"  # Heavy multiplication X (U+2716)
    return "?"


def create_status_display(file_statuses):
    """Create a display showing all file statuses as individual lines."""
    lines = []

    # Only show files that have started and haven't been completed yet
    for fs in file_statuses:
        if fs.started and not fs.completed:
            if fs.onchain_only:
                # For message-only items, only show confirm status
                line = f"{get_status_icon(fs.confirm_status)}     {fs.filename}"

                # Append error message if there is one
                if fs.confirm_error:
                    error_msg = fs.confirm_error.split(": ", 1)[-1]
                    line += f"[red]: {error_msg}[/red]"
            else:
                # Original file processing logic
                if fs.confirm_status == "error":
                    fetch_icon = " "
                    verify_icon = " "
                elif fs.fetch_status == "error":
                    fetch_icon = get_status_icon(fs.fetch_status)
                    verify_icon = " "
                else:
                    fetch_icon = get_status_icon(fs.fetch_status)
                    verify_icon = get_status_icon(fs.verify_status)

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

    return "\n".join(lines) if lines else ""

async def simulate_confirm(file_status):
    """Simulate confirming hash on chain."""
    file_status.confirm_status = "confirming"
    await asyncio.sleep(random.uniform(3, 9))

    # 10% chance of failure
    if random.random() < 0.1:
        file_status.confirm_status = "error"
        file_status.confirm_error = f"Hash confirmation failed for {file_status.filename}: Transaction not confirmed"
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

    # For message-only items, just confirm
    if file_status.onchain_only:
        confirm_success = await simulate_confirm(file_status)

        if not confirm_success:
            error_msg = file_status.confirm_error.split(": ", 1)[-1]
            live.console.print(f"[red]✖[/red]     {file_status.filename}[red]: {error_msg}[/red]")
            file_status.completed = True
            return False

        # Success
        await asyncio.sleep(0.8)
        file_status.completed = True
        live.console.print(f"[green]✔[/green]     {file_status.filename}")
        return True

    # Original file processing logic
    confirm_task = asyncio.create_task(simulate_confirm(file_status))

    download_success = await simulate_download(file_status)

    if not download_success:
        await confirm_task

        errors = []
        if file_status.confirm_status == "error":
            errors.append(file_status.confirm_error.split(": ", 1)[-1])
        errors.append(file_status.fetch_error.split(": ", 1)[-1])

        confirm_icon = get_status_icon(file_status.confirm_status)
        error_msg = ", ".join(errors)
        live.console.print(f"{confirm_icon} [red]✖[/red]   {file_status.filename}[red]: {error_msg}[/red]")

        file_status.completed = True
        return False

    verify_success = await simulate_verify(file_status)

    if not verify_success:
        await confirm_task

        errors = []
        if file_status.confirm_status == "error":
            errors.append(file_status.confirm_error.split(": ", 1)[-1])
        errors.append(file_status.verify_error.split(": ", 1)[-1])

        confirm_icon = get_status_icon(file_status.confirm_status)
        error_msg = ", ".join(errors)
        live.console.print(f"{confirm_icon} [green]✔[/green] [red]✖[/red] {file_status.filename}[red]: {error_msg}[/red]")

        file_status.completed = True
        return False

    confirm_success = await confirm_task

    if not confirm_success:
        error_msg = file_status.confirm_error.split(": ", 1)[-1]
        live.console.print(f"[red]✖[/red] [green]✔[/green] [green]✔[/green] {file_status.filename}[red]: {error_msg}[/red]")
        file_status.completed = True
        return False

    await asyncio.sleep(0.8)
    file_status.completed = True
    live.console.print(f"[green]✔ ✔ ✔[/green] {file_status.filename}")

    return True

async def main():
    # Create a list of files and events to process
    items = [
        FileStatus("init election", onchain_only=True),
        FileStatus("add subchannel guardian1", onchain_only=True),
        FileStatus("add subchannel guardian2", onchain_only=True),
        FileStatus("add subchannel guardian3", onchain_only=True),
        FileStatus("add subchannel device1", onchain_only=True),
        FileStatus("add subchannel verifier1", onchain_only=True),
        FileStatus("advance to phase 2", onchain_only=True),
        FileStatus("dataset_part1.tar.gz"),
        FileStatus("dataset_part2.tar.gz"),
        FileStatus("dataset_part3.tar.gz"),
        FileStatus("dataset_part4.tar.gz"),
        FileStatus("dataset_part5.tar.gz"),
        FileStatus("dataset_part6.tar.gz"),
        FileStatus("dataset_part7.tar.gz"),
        FileStatus("dataset_part8.tar.gz"),
        FileStatus("dataset_part9.tar.gz"),
        FileStatus("advance to phase 3", onchain_only=True),
        FileStatus("model_weights_1.pkl"),
        FileStatus("model_weights_2.pkl"),
        FileStatus("model_weights_3.pkl"),
        FileStatus("model_weights_4.pkl"),
        FileStatus("model_weights_5.pkl"),
        FileStatus("advance to phase 4", onchain_only=True),
        FileStatus("tally"),
        FileStatus("decrypted tally"),
        FileStatus("admin summary"),
        FileStatus("guardian1 summary"),
        FileStatus("guardian2 summary"),
        FileStatus("guardian3 summary"),
        FileStatus("verifier1 summary"),
        FileStatus("rm subchannel guardian1", onchain_only=True),
        FileStatus("rm subchannel guardian2", onchain_only=True),
        FileStatus("rm subchannel guardian3", onchain_only=True),
        FileStatus("rm subchannel device1", onchain_only=True),
        FileStatus("rm subchannel verifier1", onchain_only=True),
        FileStatus("end election", onchain_only=True),
    ]

    console.print("Connected to Cardano node")
    console.print("Connected to IPFS node")
    console.print("Enter election info:")
    console.print("Running verifier...\n")

    # TODO probably only need 1 refresh per second?
    with Live(create_status_display(items), console=console, refresh_per_second=10) as live:
        semaphore = asyncio.Semaphore(6) # TODO raise pretty high and assume TXs are the bottleneck

        async def process_with_semaphore(fs):
            async with semaphore:
                return await process_file(fs, live)

        tasks = [asyncio.create_task(process_with_semaphore(fs)) for fs in items]

        async def update_display():
            while not all(task.done() for task in tasks):
                live.update(create_status_display(items))
                await asyncio.sleep(0.1)
            live.update(create_status_display(items))

        await asyncio.gather(update_display(), *tasks)

    console.print("Verification complete.")
    successful = sum(1 for fs in items if
                    (fs.onchain_only and fs.confirm_status == "success") or
                    (not fs.onchain_only and fs.confirm_status == "success" and
                     fs.fetch_status == "success" and fs.verify_status == "success"))
    console.print(f"Successfully processed: [green]{successful}/{len(items)}[/green] items")

    failed = len(items) - successful
    if failed > 0:
        console.print(f"Errors encountered: [red]{failed}[/red]")

if __name__ == "__main__":
    asyncio.run(main())

