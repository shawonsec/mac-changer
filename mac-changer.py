import subprocess
import re
import random
import argparse
import sys

# Function to generate a random MAC address
def generate_random_mac():
    # The first two bytes typically indicate a locally administered MAC
    return "02:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}".format(
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
    )


# Function to validate the MAC address
def is_valid_mac(mac):
    pattern = r"^(\w{2}:){5}\w{2}$"
    return re.match(pattern, mac) is not None


# Function to validate the network interface
def validate_interface(interface):
    try:
        # Check if the interface exists
        subprocess.run(["ip", "link", "show", interface], check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError:
        return False


# Function to change the MAC address of a specified interface
def change_mac(interface, new_mac):
    try:
        # Bringing the interface down
        subprocess.run(["ip", "link", "set", interface, "down"], check=True)
        # Changing the MAC address
        subprocess.run(["ip", "link", "set", "dev", interface, "address", new_mac], check=True)
        # Bringing the interface up
        subprocess.run(["ip", "link", "set", interface, "up"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error changing MAC address: {e}")
        sys.exit(1)


# Function to get the current MAC address of a specified interface
def get_current_mac(interface):
    try:
        # Get information about the interface
        ip_result = subprocess.run(
            ["ip", "link", "show", interface], capture_output=True, text=True
        )
        # Search for the MAC address pattern
        match = re.search(r"(\w{2}:){5}\w{2}", ip_result.stdout)
        return match.group(0) if match else None
    except subprocess.CalledProcessError as e:
        print(f"Error getting MAC address: {e}")
        sys.exit(1)


# Argument parsing with help menu and examples
parser = argparse.ArgumentParser(
    description="Change the MAC address of a specified network interface.\n"
                "Use with caution. Requires sudo/root permissions.",
    formatter_class=argparse.RawTextHelpFormatter,
    epilog="Example usage:\n"
           "  python change_mac.py wlan0  # Changes to a random MAC address\n"
           "  python change_mac.py wlan0 -m 02:1A:2B:3C:4D:5E  # Changes to a specific MAC address"
)

parser.add_argument("interface", help="The network interface to change the MAC address (e.g., eth0, wlan0)")
parser.add_argument(
    "-m", "--mac",
    help="The new MAC address to set. If not provided, a random MAC will be generated.\n"
         "Example MAC address: 02:1A:2B:3C:4D:5E",
    default=None
)

args = parser.parse_args()

# Ensure running with sudo/root permissions
if subprocess.run(["id", "-u"], capture_output=True, text=True).stdout.strip() != "0":
    print("This script must be run with sudo or as a root user.")
    sys.exit(1)

# Ensure it's a compatible environment (Linux)
if sys.platform != "linux":
    print("This script can only be run on Linux systems.")
    sys.exit(1)

# Validate the interface
if not validate_interface(args.interface):
    print(f"Invalid network interface: {args.interface}. Please provide a valid interface.")
    sys.exit(1)

# Get current MAC address
current_mac = get_current_mac(args.interface)
print(f"Current MAC address of {args.interface}: {current_mac}")

# Determine the new MAC address
new_mac = args.mac or generate_random_mac()

# Validate user-supplied MAC address
if args.mac and not is_valid_mac(new_mac):
    print(f"Invalid MAC address format: {new_mac}")
    sys.exit(1)

print(f"Changing MAC address to: {new_mac}")

# Change the MAC address
change_mac(args.interface, new_mac)

# Verify the change
updated_mac = get_current_mac(args.interface)
if updated_mac == new_mac:
    print(f"Successfully changed MAC address to: {updated_mac}")
else:
    print("Failed to change MAC address.")
