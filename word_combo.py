#!/usr/bin/env python3
"""
Generate all permutations of words from an input file.
Each word is used at most once per combination.
"""

import sys
from itertools import permutations


def read_words(input_file):
    """Read words from file, removing empty lines and whitespace."""
    try:
        with open(input_file, 'r') as f:
            words = [line.strip() for line in f if line.strip()]
        return words
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)


def generate_combinations(words, output_file, min_chars=None, max_chars=None):
    """Generate all permutations of words and write to output file.

    Args:
        words: List of words to permute
        output_file: Path to output file
        min_chars: Minimum character length for generated combinations (optional)
        max_chars: Maximum character length for generated combinations (optional)
    """
    num_words = len(words)
    print(f"Found {num_words} words")

    if num_words >= 11:
        print("Warning: Large number of words leads to a very high number of combinations!")
        input("Press Enter to continue or Ctrl+C to abort...")

    if min_chars is not None:
        print(f"Minimum character length: {min_chars}")
    if max_chars is not None:
        print(f"Maximum character length: {max_chars}")

    total_combinations = 0
    filtered_combinations = 0

    with open(output_file, 'w') as f:
        # Generate combinations of all lengths (1 to n words)
        for length in range(1, num_words + 1):
            print(f"Generating combinations of length {length}...")

            # Generate all permutations of 'length' words
            for perm in permutations(words, length):
                # Concatenate words without separator
                combination = ''.join(perm)
                total_combinations += 1

                # Apply character length filters
                comb_len = len(combination)
                if min_chars is not None and comb_len < min_chars:
                    filtered_combinations += 1
                    continue
                if max_chars is not None and comb_len > max_chars:
                    filtered_combinations += 1
                    continue

                f.write(combination + '\n')

    if filtered_combinations > 0:
        print(f"Filtered out {filtered_combinations} combinations due to length constraints")

    return total_combinations - filtered_combinations


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <input_wordfile> [output_file] [min_chars] [max_chars]")
        print(f"Example: {sys.argv[0]} input/words.txt output/words_combined.txt")
        print(f"Example: {sys.argv[0]} input/words.txt output/words_combined.txt 8 20")
        print(f"\nArguments:")
        print(f"  input_wordfile - Path to file with seed words (one per line)")
        print(f"  output_file    - Output file path (default: output/words_combined.txt)")
        print(f"  min_chars      - Minimum character length (optional)")
        print(f"  max_chars      - Maximum character length (optional)")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "output/words_combined.txt"

    min_chars = None
    max_chars = None

    if len(sys.argv) > 3:
        try:
            min_chars = int(sys.argv[3])
        except ValueError:
            print(f"Error: min_chars must be an integer")
            sys.exit(1)

    if len(sys.argv) > 4:
        try:
            max_chars = int(sys.argv[4])
        except ValueError:
            print(f"Error: max_chars must be an integer")
            sys.exit(1)

    if min_chars is not None and max_chars is not None and min_chars > max_chars:
        print(f"Error: min_chars ({min_chars}) cannot be greater than max_chars ({max_chars})")
        sys.exit(1)

    print("Generating word combinations...")

    # Read words from input file
    words = read_words(input_file)

    # Generate and write combinations
    total_combinations = generate_combinations(words, output_file, min_chars, max_chars)

    print(f"Done! Generated {total_combinations} combinations")
    print(f"Output saved to: {output_file}")


if __name__ == "__main__":
    main()
