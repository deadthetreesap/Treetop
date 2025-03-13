
import curses
import psutil
import time
import subprocess

def get_cpu_stats():
    """Return formatted CPU usage stats."""
    cpu_percent = psutil.cpu_percent(interval=None)
    cores_percent = psutil.cpu_percent(interval=None, percpu=True)
    stats = f"Overall CPU: {cpu_percent}%\n"
    for i, percent in enumerate(cores_percent):
        stats += f"Core {i}: {percent}%\n"
    return stats

def get_ram_stats():
    """Return formatted RAM usage stats."""
    mem = psutil.virtual_memory()
    stats = (f"RAM Total: {mem.total // (1024**2)} MB\n"
             f"Used: {mem.used // (1024**2)} MB ({mem.percent}%)\n"
             f"Free: {mem.available // (1024**2)} MB")
    return stats

def get_storage_stats():
    """Return formatted storage usage stats for the root partition."""
    disk = psutil.disk_usage('/')
    stats = (f"Total: {disk.total // (1024**3)} GB\n"
             f"Used: {disk.used // (1024**3)} GB ({disk.percent}%)\n"
             f"Free: {disk.free // (1024**3)} GB")
    return stats

def get_gpu_stats():
    """
    Use rocm-smi to get Radeon GPU stats.
    
    This function calls 'rocm-smi' with parameters to show temperature and usage.
    Ensure that rocm-smi is installed and accessible.
    """
    try:
        # Call rocm-smi with options to show temperature and GPU usage.
        result = subprocess.run(
            ["rocm-smi", "--showtemp", "--showuse"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            # Return the output; you may further process it if desired.
            return result.stdout.strip()
        else:
            return f"rocm-smi error (code {result.returncode}): {result.stderr.strip()}"
    except Exception as e:
        return f"Exception when calling rocm-smi: {e}"

def draw_window(window, title, content):
    """Clear window, draw a border, title and content."""
    window.clear()
    window.box()
    window.addstr(0, 2, f" {title} ")
    for idx, line in enumerate(content.splitlines(), start=1):
        try:
            window.addstr(idx, 1, line)
        except curses.error:
            # Avoid crash if content is larger than window
            pass
    window.noutrefresh()  # Mark for refresh later

def main(stdscr):
    # Turn off cursor and set up non-blocking input
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(500)  # Refresh every 500 ms

    # Get the size of the screen
    height, width = stdscr.getmaxyx()
    half_height = height // 2
    half_width = width // 2

    # Create four sub-windows (corners):
    win_cpu = curses.newwin(half_height, half_width, 0, 0)              # Top-left: CPU
    win_gpu = curses.newwin(half_height, half_width, 0, half_width)       # Top-right: GPU
    win_ram = curses.newwin(half_height, half_width, half_height, 0)      # Bottom-left: RAM
    win_storage = curses.newwin(half_height, half_width, half_height, half_width)  # Bottom-right: Storage

    while True:
        # Get updated stats
        cpu_stats = get_cpu_stats()
        gpu_stats = get_gpu_stats()
        ram_stats = get_ram_stats()
        storage_stats = get_storage_stats()

        # Draw each window with corresponding stats
        draw_window(win_cpu, "CPU", cpu_stats)
        draw_window(win_gpu, "GPU", gpu_stats)
        draw_window(win_ram, "RAM", ram_stats)
        draw_window(win_storage, "Storage", storage_stats)

        # Refresh the screen all at once
        curses.doupdate()

        # Check if user pressed 'q' to exit
        try:
            key = stdscr.getch()
            if key == ord('q'):
                break
        except Exception:
            pass

        time.sleep(0.5)  # Adjust refresh rate as needed

if __name__ == '__main__':
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass

