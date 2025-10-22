# BorgCrack

BorgCrack is a password recovery tool for the slightly forgetful users of Borg backup repositories. You input the repository config file (see `sample/config`) and a list of words or symbols that you remember that the password was comprised of (see `sample/wordlist.txt`). After the generation of all permutations of possible passwords using `word_combo.py`, you can then run the brute force decryption attempts in parallel with `borg_crack.py`. 

## Features

- **Multi-threaded cracking**: Uses multiprocessing to distribute password testing across CPU cores
- **Wordlist generation**: Create comprehensive wordlists from seed words using permutations

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

```bash
# Clone the repository
git clone https://github.com/tobiasmllr/borgcrack.git
cd borgcrack

# Install dependencies
uv sync
```

## Usage

### Quick Start

```bash
# Generate a wordlist from seed words
uv run word_combo.py sample/wordlist.txt input/wordlist_combined.txt

# Crack a Borg backup password
uv run borg_crack.py input/wordlist_combined.txt 12 sample/config
```

### Word Combination Generator

Generate all permutations of words from an input file. Each word is used at most once per combination.

```bash
uv run word_combo.py <input_wordfile> [output_file] [min_chars] [max_chars]
```

**Arguments:**
- `input_wordfile`: Path to file containing seed words (one per line)
- `output_file`: Path for output wordlist (default: `output/words_combined.txt`)
- `min_chars`: Minimum character length for generated combinations (optional)
- `max_chars`: Maximum character length for generated combinations (optional)


**Example:**
```bash
# Create wordlist from seeds
echo -e "word1\nword2\nword3" > input/words.txt
uv run word_combo.py input/words.txt output/words_combined.txt 8 16

# This generates:
# word1word2, word1word3, word2word1, word2word3, word3word1, word3word2
# word1word2word3, word1word3word2, word2word1word3, etc.
```

**Warning:** The number of combinations grows factorially with the number of input words:
- 5 words --> 325 combinations
- 10 words --> 9,864,100 combinations
- 15 words --> ~1.3 trillion combinations

### Borg Password Cracker

Attempt to crack a Borg backup password using a wordlist.

```bash
uv run borg_crack.py <wordlist.txt> [num_workers] [config_file]
```

**Arguments:**
- `wordlist.txt`: Path to password wordlist (one password per line)
- `num_workers`: Number of worker processes (default: CPU count)
- `config_file`: Path to Borg repository config file (default: `config`)

**Examples:**
```bash
# Use all CPU cores with default config location
uv run borg_crack.py passwords.txt

# Use 8 workers with custom config
uv run borg_crack.py passwords.txt 8 /path/to/borg/config

# Specify config file only (uses all cores)
uv run borg_crack.py passwords.txt /path/to/config
```

**Output:**
When a password is found, it's displayed on screen and appended to `output/found_passwords.txt` with metadata:
```
# Cracked on 2025-10-21 23:45:12
# Config file: sample/config
# Wordlist file: sample/wordlist_combined.txt
Password: correcthorsebatterystaple
```

**Performance:**
On a Ryzen 5 5600X utilizing 12 workers, I get around 190 pw/sec.

## How It Works

### Borg Key Format

As described in the [Docs](https://borgbackup.readthedocs.io/en/stable/internals/data-structures.html#key-files), Borg uses a keyfile encrypted with PBKDF2-HMAC-SHA256. The `config` file contains a base64-encoded msgpack structure with:
- `salt`: Random salt for key derivation
- `iterations`: PBKDF2 iteration count (typically 100,000)
- `hash`: HMAC-SHA256 of the decrypted key
- `data`: AES-CTR encrypted repository key
- `algorithm`: Encryption algorithm identifier

### Cracking Process

1. Load the encrypted key from the Borg config file
2. Extract salt, iterations, and expected hash
3. For each password in the wordlist:
   - Derive KEK (Key Encryption Key) using PBKDF2 with the password
   - Decrypt the repository key using AES-CTR
   - Compute HMAC-SHA256 of decrypted data
   - Compare with expected hash
4. If hashes match, password is correct

## Dependencies

- Python 3.13+
- `msgpack` - MessagePack serialization
- `pycryptodome` - Cryptographic primitives (PBKDF2, AES, HMAC)

## Ethical Use

This tool is intended for **legitimate password recovery only**:
- Recovering passwords to your own Borg backups
- Authorized security testing with explicit permission
- Educational purposes in controlled environments

**Do not use this tool to:**
- Access backups you don't own or have permission to access
- Perform unauthorized access attempts
- Violate terms of service or applicable laws

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.