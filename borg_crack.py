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
    Verify if a password is correct for the Borg key.

    Args:
        args: Tuple of (password, salt, iterations, expected_hash, encrypted_data)

    Returns:
        Tuple of (password, success) where success is True if password is correct
    """
    password, salt, iterations, expected_hash, encrypted_data = args

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
            return (password, True)
        return (password, False)
    except:
        return (password, False)

def crack_borg_key(config_file, wordlist_file, num_workers=None):
    """
    Attempt to crack the Borg key using a wordlist.

    Args:
        config_file: Path to Borg config file
        wordlist_file: Path to wordlist file
        num_workers: Number of worker processes (default: CPU count)
    """
    print("Borg Backup Key Cracker")
    print("="*60)

    if num_workers is None:
        num_workers = mp.cpu_count()

    print(f"[*] Using {num_workers} worker processes")

    # Load the key
    print(f"[*] Reading key from {config_file}...")
    key_b64 = read_borg_key_from_config(config_file)
    key_data = base64.b64decode(key_b64)
    outer = msgpack.unpackb(key_data, raw=True)

    salt = outer[b'salt']
    iterations = outer[b'iterations']
    expected_hash = outer[b'hash']
    encrypted_data = outer[b'data']

    print(f"[*] Algorithm: {outer[b'algorithm'].decode('utf-8')}")
    print(f"[*] Iterations: {iterations}")
    print(f"[*] Salt: {salt.hex()[:32]}...")

    # Load passwords from wordlist
    print(f"\n[*] Loading wordlist from {wordlist_file}...")

    try:
        with open(wordlist_file, 'r', encoding='utf-8', errors='ignore') as f:
            passwords = [line.rstrip('\n\r') for line in f]
    except FileNotFoundError:
        print(f"[!] Error: Wordlist file '{wordlist_file}' not found")
        sys.exit(1)

    total = len(passwords)
    print(f"[*] Loaded {total} passwords")
    print(f"[*] Starting cracking process...")
    print(f"[*] Warning: This will be SLOW due to {iterations} PBKDF2 iterations")
    print()

    # Prepare arguments for workers
    args_list = [(pw, salt, iterations, expected_hash, encrypted_data) for pw in passwords]

    start_time = time.time()
    found = False
    found_password = None

    # Use multiprocessing pool
    with mp.Pool(processes=num_workers) as pool:
        # Process in chunks and show progress
        chunk_size = max(1, total // 100)  # Update progress every 1%

        for i, (password, success) in enumerate(pool.imap_unordered(verify_password, args_list, chunksize=1), 1):
            if i % 10 == 0 or success:
                elapsed = time.time() - start_time
                rate = i / elapsed if elapsed > 0 else 0
                eta = (total - i) / rate if rate > 0 else 0
                print(f"\r[*] Tried {i}/{total} passwords ({rate:.1f} pw/s, ETA: {eta:.0f}s)...", end='', flush=True)

            if success:
                found = True
                found_password = password
                pool.terminate()
                break

    elapsed = time.time() - start_time

    print()  # New line after progress

    if found:
        print(f"\n{'='*60}")
        print(f"[+] PASSWORD FOUND!")
        print(f"{'='*60}")
        print(f"Password: {found_password}")
        print(f"Time: {elapsed:.2f} seconds")
        print(f"Rate: {(i/elapsed):.2f} passwords/second")

        # Append found password to file
        with open("output/found_passwords.txt", 'a') as f:
            # timestamp
            t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            f.write(f"# Cracked on {t}\n")
            f.write(f"# Config file: {config_file}\n")
            f.write(f"# Wordlist file: {wordlist_file}\n")
            f.write(f"Password: {found_password}\n")
        print(f"\nPassword saved to: output/found_passwords.txt")

        return found_password
    else:
        print(f"\n[!] Password not found in wordlist")
        print(f"[!] Tried all {total} passwords in {elapsed:.2f} seconds")
        print(f"[!] Rate: {(total/elapsed):.2f} passwords/second")
        return None

def crack_borg_key_cli():
    """CLI entry point for borg-crack command."""
    if len(sys.argv) < 2:
        print("Usage: borg-crack <wordlist.txt> [num_workers] [config_file]")
        print("\nOptions:")
        print("  wordlist.txt  - Path to password wordlist")
        print("  num_workers   - Number of worker processes (default: CPU count)")
        print("  config_file   - Path to Borg config file (default: input/config)")
        sys.exit(1)

    wordlist_file = sys.argv[1]
    config_file = "input/config"
    num_workers = None

    if len(sys.argv) >= 3:
        try:
            num_workers = int(sys.argv[2])
        except ValueError:
            # If it's not a number, treat it as config file path
            config_file = sys.argv[2]
            num_workers = None

    if len(sys.argv) >= 4:
        config_file = sys.argv[3]

    crack_borg_key(config_file, wordlist_file, num_workers)


if __name__ == "__main__":
    crack_borg_key_cli()
