"""
Linux Kernel Header Parser for PCIe Constants

Extracts PCIe register definitions from include/uapi/linux/pci_regs.h
to provide a second authoritative source for verification.
"""

import re
import json
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class HeaderConstant:
    """A single #define constant from the header."""
    name: str
    value: str
    description: str
    line_number: int

    @property
    def is_register_offset(self) -> bool:
        """Check if this constant defines a register offset (not a bit field)."""
        # Register offsets are typically like PCI_EXP_DEVCAP (0x04)
        # Bit fields are like PCI_EXP_DEVCAP_PAYLOAD (0x00000007)
        # Heuristic: offsets are small hex values (< 0x100), no underscores after register name
        if not self.value.startswith('0x'):
            return False
        try:
            val = int(self.value, 16)
            # Register offsets are typically < 256 (0x100)
            return val < 0x100
        except ValueError:
            return False


class LinuxHeaderParser:
    """Parser for Linux kernel PCIe header file."""

    GITHUB_RAW_URL = "https://raw.githubusercontent.com/torvalds/linux/master/include/uapi/linux/pci_regs.h"

    # Pattern to match: #define NAME VALUE /* comment */
    # Handles various whitespace: tabs, spaces, multiple spaces
    DEFINE_PATTERN = re.compile(
        r'^\s*#define\s+(\S+)\s+(\S+)(?:\s*\/\*\s*(.+?)\s*\*\/)?',
        re.MULTILINE
    )

    def __init__(self, header_path: Optional[str] = None):
        """
        Initialize parser.

        Args:
            header_path: Path to local pci_regs.h file. If None, will download from GitHub.
        """
        self.header_path = header_path
        self.constants: List[HeaderConstant] = []

    def fetch_header(self) -> str:
        """Fetch header file from GitHub."""
        print(f"Fetching header from {self.GITHUB_RAW_URL}...")
        with urllib.request.urlopen(self.GITHUB_RAW_URL) as response:
            content = response.read().decode('utf-8')
        print(f"✓ Downloaded {len(content)} bytes")
        return content

    def parse(self, filter_prefix: str = "PCI_EXP_") -> List[HeaderConstant]:
        """
        Parse header file and extract constants.

        Args:
            filter_prefix: Only extract constants starting with this prefix.
                          Set to empty string to extract all PCI constants.

        Returns:
            List of HeaderConstant objects
        """
        # Get header content
        if self.header_path:
            with open(self.header_path, 'r') as f:
                content = f.read()
        else:
            content = self.fetch_header()

        # Extract all #define statements
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            match = self.DEFINE_PATTERN.match(line)
            if match:
                name = match.group(1)
                value = match.group(2)
                description = match.group(3) or ""

                # Filter by prefix
                if filter_prefix and not name.startswith(filter_prefix):
                    continue

                constant = HeaderConstant(
                    name=name,
                    value=value,
                    description=description.strip(),
                    line_number=line_num
                )
                self.constants.append(constant)

        print(f"✓ Extracted {len(self.constants)} constants with prefix '{filter_prefix}'")
        return self.constants

    def get_register_offsets(self) -> Dict[str, HeaderConstant]:
        """
        Get only register offset definitions (not bit field masks).

        Returns:
            Dictionary mapping register names to HeaderConstant objects
        """
        offsets = {}
        for const in self.constants:
            if const.is_register_offset:
                offsets[const.name] = const
        return offsets

    def get_bit_fields(self) -> Dict[str, List[HeaderConstant]]:
        """
        Get bit field definitions grouped by register.

        Returns:
            Dictionary mapping register name to list of bit field constants
        """
        # Group bit fields by their base register name
        # e.g., PCI_EXP_DEVCAP_PAYLOAD -> PCI_EXP_DEVCAP
        bit_fields = {}

        for const in self.constants:
            if const.is_register_offset:
                continue

            # Try to find the base register name
            # Pattern: PCI_EXP_DEVCAP_PAYLOAD -> PCI_EXP_DEVCAP
            parts = const.name.split('_')
            for i in range(len(parts), 2, -1):
                potential_reg = '_'.join(parts[:i])
                if potential_reg not in bit_fields:
                    bit_fields[potential_reg] = []
                bit_fields[potential_reg].append(const)
                break

        return bit_fields

    def save_to_json(self, output_path: str):
        """Save all constants to JSON file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Organize data
        data = {
            'source': 'Linux Kernel include/uapi/linux/pci_regs.h',
            'url': self.GITHUB_RAW_URL,
            'total_constants': len(self.constants),
            'constants': [asdict(c) for c in self.constants],
            'register_offsets': {
                name: asdict(const)
                for name, const in self.get_register_offsets().items()
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        print(f"✓ Saved {len(self.constants)} constants to {output_path}")
        print(f"  - Register offsets: {len(data['register_offsets'])}")
        print(f"  - Bit fields: {len(self.constants) - len(data['register_offsets'])}")


def main():
    """CLI entry point for Linux header parser."""
    import sys

    # Default paths
    output_path = Path(__file__).parent.parent.parent / "data" / "linux_headers" / "pci_constants.json"

    # Allow override from command line
    if len(sys.argv) > 1:
        output_path = Path(sys.argv[1])

    print("Parsing Linux kernel PCIe header file...")

    parser = LinuxHeaderParser()
    constants = parser.parse(filter_prefix="PCI_EXP_")

    print(f"\nFound {len(constants)} PCI Express constants")

    # Print sample register offsets
    offsets = parser.get_register_offsets()
    if offsets:
        print("\nSample register offsets:")
        for i, (name, const) in enumerate(list(offsets.items())[:5]):
            print(f"  {i+1}. {name} = {const.value}")
            if const.description:
                print(f"     {const.description}")

    # Print Gen5 constants
    gen5_constants = [c for c in constants if '32_0' in c.name or '32.0' in c.description]
    if gen5_constants:
        print(f"\nPCIe Gen5 (32.0 GT/s) constants found: {len(gen5_constants)}")
        for const in gen5_constants:
            print(f"  - {const.name} = {const.value} // {const.description}")

    # Save to JSON
    parser.save_to_json(str(output_path))


if __name__ == "__main__":
    main()
