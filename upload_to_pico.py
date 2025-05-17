import subprocess
import os

# Set this to your local folder
source_folder = r"C:\Users\Elis\repos\sunrise_alarm_2_git"
# Target directory on the Pico (usually root)
target_path = "/"

# Read .txt containing files/folder to ignore (not to upload to Pico)
ignore_file = "ignore.txt"
with open(ignore_file) as f:
    ignore_list = f.read().split("\n")

# Optional: Track if the user chooses to apply a decision to all
apply_to_all = None  # Can be "overwrite" or "skip"


def list_files_on_pico():
    """Returns a list of file paths currently on the Pico"""
    result = subprocess.run(
        ["mpremote", "fs", "ls", "-r", ":"],
        capture_output=True,
        text=True
    )
    files = []
    for line in result.stdout.splitlines():
        if line.strip() and not line.strip().endswith("/"):
            filename = line.strip().split(" ")[-1]
            files.append("/" + filename.strip())
    return files


def upload_file(local_path, remote_path):
    print(f"Uploading {local_path} to {remote_path}")
    subprocess.run([
        "mpremote", "fs", "cp", local_path, ":" + remote_path
    ])


def upload_directory(
        local_dir: str,
        remote_dir: str,
        existing_files,
        ignore: list[str] = []
        ) -> int:
    global apply_to_all
    for root, _, files in os.walk(local_dir):

        # Skip directories in ignore.txt
        normalized_ignore = [p.replace("\\", "/") for p in ignore]
        ignore_roots = [i for i in normalized_ignore if "/" in i]
        ignore_roots = [i.replace("/", "") for i in ignore_roots]
        if len(set(root.split("\\")).intersection(ignore_roots)) > 0:
            print(f"Skipping {root}")
            continue

        files_uploaded = 0  # count of files uploaded

        for file in files:
            local_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_path, local_dir)
            remote_path = os.path.join(remote_dir, relative_path).replace("\\", "/")

            if file in ignore_list:
                print(f"Skipping {file}")
                continue

            if remote_path in existing_files:
                if apply_to_all == "skip":
                    print(f"Skipping existing file: {remote_path}")
                    continue
                elif apply_to_all == "overwrite":
                    pass  # Proceed to overwrite
                else:
                    # Ask user
                    print(f"\nFile already exists on Pico: {remote_path}")
                    decision = input("Overwrite (o), Skip (s), Overwrite all (oa), Skip all (sa)? ").strip().lower()
                    if decision == "s":
                        print(f"Skipping {remote_path}")
                        continue
                    elif decision == "sa":
                        apply_to_all = "skip"
                        print(f"Skipping {remote_path}")
                        continue
                    elif decision == "oa":
                        apply_to_all = "overwrite"
                    elif decision != "o":
                        print("Invalid input. Skipping file.")
                        continue  # default to skip
            upload_file(local_path, remote_path)
            files_uploaded += 1

    return files_uploaded


def get_mpremote_devices():
    try:
        result = subprocess.run(
            ["mpremote", "connect", "list"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        output = result.stdout.strip()
        if output:
            devices = output.splitlines()
            return devices  # List of connected device paths
        else:
            return []
    except Exception as e:
        print(f"Error checking devices: {e}")
        return []


if __name__ == "__main__":
    # attempt connection to Pico
    devices = get_mpremote_devices()
    if devices:
        print("Connected device(s):", devices)
    else:
        raise ConnectionError("No MicroPython device found.")

    print("Reading files from Pico...")
    pico_files = list_files_on_pico()

    uploaded_count = upload_directory(
        source_folder,
        target_path,
        pico_files,
        ignore_list
        )
    
    if uploaded_count == 0:
        print("\nNo files uploaded.")
    else:
        print(f"\n{uploaded_count} files have been uploaded.")
