#!/usr/bin/env python3
"""
Generate all permutations of words from an input file.
Each word is used at most once per combination.
"""

import sys
from itertools import permutations
from pathlib import Path


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


def generate_combinations(words, output_file):
    """Generate all permutations of words and write to output file."""
    num_words = len(words)
    print(f"Found {num_words} words")

    total_combinations = 0

    with open(output_file, 'w') as f:
        # Generate combinations of all lengths (1 to n words)
        for length in range(1, num_words + 1):
            print(f"Generating combinations of length {length}...")

            # Generate all permutations of 'length' words
            for perm in permutations(words, length):
                # Concatenate words without separator
                combination = ''.join(perm)
                f.write(combination + '\n')
                total_combinations += 1

    return total_combinations


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <input_wordfile> [output_file]")
        print(f"Example: {sys.argv[0]} words.txt words_combined.txt")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "words_combined.txt"

    print("Generating word combinations...")

    # Read words from input file
    words = read_words(input_file)

    # Generate and write combinations
    total_combinations = generate_combinations(words, output_file)

    print(f"Done! Generated {total_combinations} combinations")
    print(f"Output saved to: {output_file}")


if __name__ == "__main__":
    main()
