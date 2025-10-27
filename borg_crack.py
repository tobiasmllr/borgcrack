#!/usr/bin/env python3
"""
Borg Backup Key Cracker

This script attempts to crack a Borg backup key by trying passwords from a wordlist.
Supports multiprocessing for faster cracking.
"""

import msgpack
import base64
import hmac
import hashlib
import configparser
import sys
import time
import multiprocessing as mp
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256
from Crypto.Util import Counter

def read_borg_key_from_config(config_file):
    """Read the Borg key from the config file."""
    config = configparser.ConfigParser()
    config.read(config_file)
    return config.get('repository', 'key')

def verify_password(args):
    """
    Verify if a password is correct for the Borg key(s).

    Args:
        args: Tuple of (password, configs_data) where configs_data is a list of tuples
              containing (config_name, salt, iterations, expected_hash, encrypted_data)

    Returns:
        Tuple of (password, matched_configs) where matched_configs is a list of config names
        that matched this password (empty list if no matches)
    """
    password, configs_data = args
    matched_configs = []

    # Each config may have different salt/iterations, so we need to try each one
    for config_name, salt, iterations, expected_hash, encrypted_data in configs_data:
        try:
            # Derive KEK from password
            kek = PBKDF2(
                password.encode('utf-8'),
                salt,
                dkLen=32,
                count=iterations,
                hmac_hash_module=SHA256
            )

            # Decrypt data
            ctr = Counter.new(128, initial_value=0)
            cipher = AES.new(kek, AES.MODE_CTR, counter=ctr)
            decrypted_data = cipher.decrypt(encrypted_data)

            # Verify HMAC
            computed_hash = hmac.new(kek, decrypted_data, hashlib.sha256).digest()

            if computed_hash == expected_hash:
                matched_configs.append(config_name)
        except:
            continue

    return (password, matched_configs)

def crack_borg_key(config_files, wordlist_file, num_workers=None):
    """
    Attempt to crack the Borg key using a wordlist.

    Args:
        config_files: Path to Borg config file or list of paths to multiple config files
        wordlist_file: Path to wordlist file
        num_workers: Number of worker processes (default: CPU count)
    """
    print("Borg Backup Key Cracker")
    print("="*60)

    if num_workers is None:
        num_workers = mp.cpu_count()

    print(f"[*] Using {num_workers} worker processes")

    # Handle single file or list of files
    if isinstance(config_files, str):
        config_files = [config_files]

    print(f"[*] Loading {len(config_files)} config file(s)...")

    # Load all config files
    configs_data = []
    for config_file in config_files:
        print(f"[*] Reading key from {config_file}...")
        try:
            key_b64 = read_borg_key_from_config(config_file)
            key_data = base64.b64decode(key_b64)
            outer = msgpack.unpackb(key_data, raw=True)

            salt = outer[b'salt']
            iterations = outer[b'iterations']
            expected_hash = outer[b'hash']
            encrypted_data = outer[b'data']

            print(f"    Algorithm: {outer[b'algorithm'].decode('utf-8')}")
            print(f"    Iterations: {iterations}")
            print(f"    Salt: {salt.hex()[:32]}...")

            configs_data.append((config_file, salt, iterations, expected_hash, encrypted_data))
        except Exception as e:
            print(f"[!] Error loading {config_file}: {e}")
            continue

    if not configs_data:
        print("[!] No valid config files loaded. Exiting.")
        sys.exit(1)

    print(f"\n[*] Successfully loaded {len(configs_data)} config file(s)")

    # Load passwords from wordlist
    print(f"[*] Loading wordlist from {wordlist_file}...")

    try:
        with open(wordlist_file, 'r', encoding='utf-8', errors='ignore') as f:
            passwords = [line.rstrip('\n\r') for line in f]
    except FileNotFoundError:
        print(f"[!] Error: Wordlist file '{wordlist_file}' not found")
        sys.exit(1)

    total = len(passwords)
    print(f"[*] Loaded {total} passwords")
    print(f"[*] Starting cracking process...")

    # Show max iterations warning
    max_iterations = max(cfg[2] for cfg in configs_data)
    print(f"[*] Warning: This will be SLOW due to up to {max_iterations} PBKDF2 iterations per config")
    print()

    # Prepare arguments for workers - each password gets tested against all configs
    args_list = [(pw, configs_data) for pw in passwords]

    start_time = time.time()
    found_passwords = {}  # Maps config_file -> password

    # Use multiprocessing pool
    with mp.Pool(processes=num_workers) as pool:
        for i, (password, matched_configs) in enumerate(pool.imap_unordered(verify_password, args_list, chunksize=1), 1):
            if i % 10 == 0 or matched_configs:
                elapsed = time.time() - start_time
                rate = i / elapsed if elapsed > 0 else 0
                eta = (total - i) / rate if rate > 0 else 0
                found_count = len(found_passwords)
                print(f"\r[*] Tried {i}/{total} passwords ({rate:.1f} pw/s, ETA: {eta:.0f}s, Found: {found_count}/{len(configs_data)})...", end='', flush=True)

            if matched_configs:
                for config_name in matched_configs:
                    found_passwords[config_name] = password
                    print(f"\n[+] PASSWORD FOUND for {config_name}: {password}")

                    # Save immediately to file
                    with open("output/found_passwords.txt", 'a') as f:
                        t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                        f.write(f"# Cracked on {t}\n")
                        f.write(f"# Wordlist file: {wordlist_file}\n")
                        f.write(f"Config: {config_name}\n")
                        f.write(f"Password: {password}\n\n")

                    print(f"    Saved to: output/found_passwords.txt")

                # If all configs are cracked, we can stop
                if len(found_passwords) == len(configs_data):
                    pool.terminate()
                    break

    elapsed = time.time() - start_time

    print()  # New line after progress

    if found_passwords:
        print(f"\n{'='*60}")
        print(f"[+] CRACKING COMPLETE!")
        print(f"{'='*60}")
        print(f"Found passwords for {len(found_passwords)}/{len(configs_data)} config file(s)")
        print(f"Time: {elapsed:.2f} seconds")
        print(f"Rate: {(i/elapsed):.2f} passwords/second")
        print()

        # Display summary of found passwords
        for config_file, password in found_passwords.items():
            print(f"  {config_file}: {password}")

        print(f"\nAll passwords saved to: output/found_passwords.txt")

        if len(found_passwords) < len(configs_data):
            print(f"\n[!] Warning: {len(configs_data) - len(found_passwords)} config file(s) not cracked")
            for config_file, _, _, _, _ in configs_data:
                if config_file not in found_passwords:
                    print(f"    - {config_file}")

        return found_passwords
    else:
        print(f"\n[!] No passwords found in wordlist")
        print(f"[!] Tried all {total} passwords in {elapsed:.2f} seconds")
        print(f"[!] Rate: {(total/elapsed):.2f} passwords/second")
        return None

def crack_borg_key_cli():
    """CLI entry point for borg-crack command."""
    if len(sys.argv) < 2:
        print("Usage: borg-crack <wordlist.txt> [num_workers] [config_file1] [config_file2] ...")
        print("\nOptions:")
        print("  wordlist.txt   - Path to password wordlist")
        print("  num_workers    - Number of worker processes (default: CPU count)")
        print("  config_file... - Path(s) to Borg config file(s) (default: input/config)")
        print("\nExamples:")
        print("  borg-crack wordlist.txt")
        print("  borg-crack wordlist.txt 8")
        print("  borg-crack wordlist.txt input/config1 input/config2")
        print("  borg-crack wordlist.txt 8 input/config1 input/config2 input/config3")
        sys.exit(1)

    wordlist_file = sys.argv[1]
    config_files = []
    num_workers = None

    # Parse remaining arguments
    for arg in sys.argv[2:]:
        try:
            # Try to parse as integer (num_workers)
            num_workers = int(arg)
        except ValueError:
            # It's a config file path
            config_files.append(arg)

    # If no config files specified, use default
    if not config_files:
        config_files = ["input/config"]

    crack_borg_key(config_files, wordlist_file, num_workers)


if __name__ == "__main__":
    crack_borg_key_cli()
