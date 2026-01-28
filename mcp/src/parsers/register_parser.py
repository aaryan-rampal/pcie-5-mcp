"""
PCIe Register Parser

Extracts register definitions from PCIe specification text.
Focused on Chapter 7 (Configuration Space) registers.

Based on analysis from PCIe_doc_summary.md:
- 3,865 register mentions across ~200 pages
- Consistent format: Section X.Y.Z [Register Name] (Offset XXh)
- Bit fields with attributes (RO, RW, RWC, RW1C, RsvdP, RsvdZ)
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class RegisterField:
    """Individual bit field within a register."""
    bits: str  # e.g., "7:5" or "3"
    name: str
    attribute: str  # RO, RW, RWC, RW1C, RsvdP, RsvdZ
    description: str = ""

    @property
    def bit_range(self) -> tuple[int, int]:
        """Parse bit range into (start, end) tuple."""
        if ":" in self.bits:
            high, low = self.bits.split(":")
            return (int(low), int(high))
        else:
            bit = int(self.bits)
            return (bit, bit)


@dataclass
class Register:
    """PCIe configuration register definition."""
    section: str  # e.g., "7.5.3.4"
    name: str
    offset: str  # e.g., "08h"
    fields: List[RegisterField]
    page: Optional[int] = None
    chapter: int = 7  # Most registers are in Chapter 7

    def get_field_by_name(self, name: str) -> Optional[RegisterField]:
        """Look up field by name."""
        for field in self.fields:
            if field.name.lower() == name.lower():
                return field
        return None

    def get_field_by_bit(self, bit: int) -> Optional[RegisterField]:
        """Look up field by bit position."""
        for field in self.fields:
            start, end = field.bit_range
            if start <= bit <= end:
                return field
        return None


class RegisterParser:
    """Parser for PCIe register definitions from spec text."""

    # Pattern: 7.5.3.4 Device Control Register(Offset 08h)
    # Note: No space before (Offset in actual spec
    REGISTER_HEADER_PATTERN = re.compile(
        r'^(\d+(?:\.\d+)*)\s+(.+?)\(Offset\s+([0-9A-Fa-f]+h)\)',
        re.MULTILINE
    )

    # Register attributes
    ATTRIBUTES = {'RO', 'RW', 'RWC', 'RW1C', 'RW1CS', 'RsvdP', 'RsvdZ', 'HwInit'}

    def __init__(self, spec_text_path: str):
        """
        Initialize parser with path to extracted spec text.

        Args:
            spec_text_path: Path to pcie_spec_full_text.txt
        """
        self.spec_text_path = Path(spec_text_path)
        self.registers: Dict[str, Register] = {}

    def parse(self) -> Dict[str, Register]:
        """
        Parse all registers from spec text.

        Returns:
            Dictionary mapping register names to Register objects
        """
        if not self.spec_text_path.exists():
            raise FileNotFoundError(f"Spec text not found: {self.spec_text_path}")

        with open(self.spec_text_path, 'r', encoding='utf-8') as f:
            text = f.read()

        # Focus on Chapter 7 (Configuration Space) - pages 673-900+
        # This is where most register definitions are
        chapter_7_start = text.find("7. Software Initialization and Configuration")
        if chapter_7_start == -1:
            chapter_7_start = text.find("Chapter 7")

        if chapter_7_start != -1:
            # Extract just Chapter 7 section for efficiency
            chapter_7_end = text.find("8. Electrical", chapter_7_start)
            if chapter_7_end == -1:
                chapter_7_text = text[chapter_7_start:]
            else:
                chapter_7_text = text[chapter_7_start:chapter_7_end]
        else:
            # Fallback: use entire text
            chapter_7_text = text

        # Find all register headers
        for match in self.REGISTER_HEADER_PATTERN.finditer(chapter_7_text):
            section = match.group(1)
            name = match.group(2).strip()
            offset = match.group(3)

            # Extract register definition (next ~50 lines after header)
            start_pos = match.end()
            end_pos = min(start_pos + 3000, len(chapter_7_text))  # ~50 lines
            register_block = chapter_7_text[start_pos:end_pos]

            # Parse fields from this block
            fields = self._parse_fields(register_block)

            # Add register even if no fields parsed (fields parsing is complex)
            register = Register(
                section=section,
                name=name,
                offset=offset,
                fields=fields if fields else []
            )
            self.registers[name] = register

        return self.registers

    def _parse_fields(self, text: str) -> List[RegisterField]:
        """
        Parse bit fields from register definition block.

        Looks for patterns like:
        0               Correctable Error Reporting Enable      RW
        1               Non-Fatal Error Reporting Enable        RW
        7:5             Max_Payload_Size                        RW
        """
        fields = []

        # Split into lines
        lines = text.split('\n')

        for line in lines[:30]:  # Look at first 30 lines
            line = line.strip()
            if not line:
                continue

            # Try to match bit field pattern
            # Format: [bit(s)]  [field name]  [attribute]
            # Example: "0    Correctable Error Reporting Enable    RW"
            parts = line.split()
            if len(parts) < 3:
                continue

            # First part should be bit number(s)
            bit_pattern = parts[0]
            if not self._is_bit_pattern(bit_pattern):
                continue

            # Last part should be an attribute
            attribute = parts[-1]
            if attribute not in self.ATTRIBUTES:
                continue

            # Middle parts are the field name
            field_name = ' '.join(parts[1:-1])

            # Clean up field name
            field_name = field_name.replace('_', ' ').strip()

            fields.append(RegisterField(
                bits=bit_pattern,
                name=field_name,
                attribute=attribute
            ))

        return fields

    def _is_bit_pattern(self, s: str) -> bool:
        """Check if string looks like a bit pattern (e.g., '0', '7:5', '15:12')."""
        # Single bit: just a number
        if s.isdigit():
            return True

        # Bit range: number:number
        if ':' in s:
            parts = s.split(':')
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                return True

        return False

    def save_to_json(self, output_path: str):
        """
        Save parsed registers to JSON file.

        Args:
            output_path: Path to output JSON file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to serializable format
        data = {
            name: {
                'section': reg.section,
                'name': reg.name,
                'offset': reg.offset,
                'chapter': reg.chapter,
                'fields': [asdict(field) for field in reg.fields]
            }
            for name, reg in self.registers.items()
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        print(f"✓ Saved {len(self.registers)} registers to {output_path}")

    def get_register_by_name(self, name: str) -> Optional[Register]:
        """Look up register by name (case-insensitive)."""
        name_lower = name.lower()
        for reg_name, register in self.registers.items():
            if reg_name.lower() == name_lower:
                return register
        return None

    def get_register_by_offset(self, offset: str) -> Optional[Register]:
        """Look up register by offset (e.g., '08h')."""
        offset = offset.lower()
        if not offset.endswith('h'):
            offset += 'h'

        for register in self.registers.values():
            if register.offset.lower() == offset:
                return register
        return None


def main():
    """CLI entry point for register parser."""
    import sys

    # Default paths
    spec_text_path = Path(__file__).parent.parent.parent.parent / "pcie_spec_full_text.txt"
    output_path = Path(__file__).parent.parent.parent / "data" / "registers" / "registers.json"

    # Allow override from command line
    if len(sys.argv) > 1:
        spec_text_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])

    print(f"Parsing registers from: {spec_text_path}")

    parser = RegisterParser(str(spec_text_path))
    registers = parser.parse()

    print(f"Found {len(registers)} registers")

    # Save to JSON
    parser.save_to_json(str(output_path))

    # Print sample
    if registers:
        print("\nSample registers:")
        for name in list(registers.keys())[:5]:
            reg = registers[name]
            print(f"  - {reg.name} (Offset {reg.offset}): {len(reg.fields)} fields")


if __name__ == "__main__":
    main()
