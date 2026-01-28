"""
PCIe Register Parser using pdfplumber for table extraction

Uses pdfplumber to extract register definition tables directly from PDF.
This is more reliable than parsing text extraction for tabular data.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    print("Warning: pdfplumber not installed. Run: pip install pdfplumber")


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
    description: str = ""

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


class PDFRegisterParser:
    """Parser for PCIe register definitions using pdfplumber."""

    # Pattern for register headers in text
    # Must start with section like "7.5.1.1.3" (at least 2 dots), followed by register name
    REGISTER_HEADER_PATTERN = re.compile(
        r'^(\d+(?:\.\d+){2,})\s*([A-Z][^(]+?)\s*\(Offset\s+([0-9A-Fa-f]+h)\)',
        re.MULTILINE
    )

    # Register attributes
    ATTRIBUTES = {'RO', 'RW', 'RWC', 'RW1C', 'RW1CS', 'RsvdP', 'RsvdZ', 'HwInit'}

    def __init__(self, pdf_path: str):
        """
        Initialize parser with PDF path.

        Args:
            pdf_path: Path to PCIe spec PDF
        """
        if not PDFPLUMBER_AVAILABLE:
            raise ImportError("pdfplumber is required. Install with: pip install pdfplumber")

        self.pdf_path = Path(pdf_path)
        self.registers: Dict[str, Register] = {}

    def parse(self, start_page: int = 673, end_page: int = 900) -> Dict[str, Register]:
        """
        Parse registers from PDF using table extraction.

        Args:
            start_page: Start page (Chapter 7 begins around 673)
            end_page: End page (Chapter 7 ends around 900)

        Returns:
            Dictionary mapping register names to Register objects
        """
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {self.pdf_path}")

        print(f"Opening PDF: {self.pdf_path}")
        print(f"Parsing pages {start_page}-{end_page}...")

        with pdfplumber.open(self.pdf_path) as pdf:
            current_register = None
            current_section = None
            current_name = None
            current_offset = None

            for page_num in range(start_page - 1, min(end_page, len(pdf.pages))):
                page = pdf.pages[page_num]
                page_text = page.extract_text()

                # Look for register headers in text
                for match in self.REGISTER_HEADER_PATTERN.finditer(page_text):
                    section = match.group(1)
                    name = match.group(2).strip()
                    offset = match.group(3)

                    # Save previous register if exists
                    if current_register:
                        self.registers[current_name] = current_register

                    # Start new register
                    current_section = section
                    current_name = name
                    current_offset = offset
                    current_register = Register(
                        section=section,
                        name=name,
                        offset=offset,
                        fields=[],
                        page=page_num + 1
                    )

                # Try text-based field parsing first (more reliable than table extraction)
                text_fields_found = False
                if current_register:
                    text_fields = self._parse_fields_from_text(page_text)
                    if text_fields:
                        current_register.fields.extend(text_fields)
                        text_fields_found = True

                # Only try table extraction if text parsing didn't find anything
                if not text_fields_found:
                    tables = page.extract_tables()

                    for table in tables:
                        if not table or len(table) < 2:
                            continue

                        # Check if this is a register bit field table
                        header_row = table[0]
                        if not header_row:
                            continue

                        # Look for table with "Bit", "Location", "Description", "Attributes" columns
                        header_text = ' '.join([str(cell) if cell else '' for cell in header_row]).lower()

                        if 'bit' in header_text and ('attribute' in header_text or 'register' in header_text):
                            # This looks like a register bit field table
                            fields = self._parse_table_fields(table)

                            if current_register and fields:
                                current_register.fields.extend(fields)

                        # Also try parsing tables where all columns are merged into one cell
                        elif len(table[0]) <= 2:  # Very few columns - might be merged
                            fields = self._parse_merged_table(table)
                            if current_register and fields:
                                current_register.fields.extend(fields)

            # Save last register
            if current_register:
                self.registers[current_name] = current_register

        print(f"Found {len(self.registers)} registers with table data")
        return self.registers

    def _parse_table_fields(self, table: List[List]) -> List[RegisterField]:
        """
        Parse register fields from extracted table.

        Args:
            table: Table rows from pdfplumber

        Returns:
            List of RegisterField objects
        """
        if len(table) < 2:
            return []

        fields = []
        header = table[0]

        # Find column indices
        bit_col = None
        name_col = None
        attr_col = None
        desc_col = None

        for i, cell in enumerate(header):
            if not cell:
                continue
            cell_lower = str(cell).lower()

            if 'bit' in cell_lower and 'location' in cell_lower:
                bit_col = i
            elif 'bit' in cell_lower and bit_col is None:
                bit_col = i
            elif 'register' in cell_lower or 'description' in cell_lower:
                if name_col is None:
                    name_col = i
                else:
                    desc_col = i
            elif 'attribute' in cell_lower or 'attr' in cell_lower:
                attr_col = i

        # Parse data rows
        for row in table[1:]:
            if not row or len(row) < 2:
                continue

            # Extract bit location
            if bit_col is not None and bit_col < len(row):
                bit_str = str(row[bit_col]) if row[bit_col] else ""
                bit_str = bit_str.strip()

                # Skip if not a valid bit pattern
                if not self._is_bit_pattern(bit_str):
                    continue

                # Extract field name
                field_name = ""
                if name_col is not None and name_col < len(row):
                    field_name = str(row[name_col]) if row[name_col] else ""
                    field_name = field_name.strip()

                # Extract attribute
                attribute = ""
                if attr_col is not None and attr_col < len(row):
                    attribute = str(row[attr_col]) if row[attr_col] else ""
                    attribute = attribute.strip()

                    # Validate attribute
                    if attribute not in self.ATTRIBUTES:
                        # Try to find attribute in cell text
                        for attr in self.ATTRIBUTES:
                            if attr in attribute:
                                attribute = attr
                                break

                # Extract description
                description = ""
                if desc_col is not None and desc_col < len(row):
                    description = str(row[desc_col]) if row[desc_col] else ""
                    description = description.strip()

                if bit_str and field_name:
                    fields.append(RegisterField(
                        bits=bit_str,
                        name=field_name,
                        attribute=attribute if attribute else "RW",  # Default
                        description=description
                    ))

        return fields

    def _parse_merged_table(self, table: List[List]) -> List[RegisterField]:
        """
        Parse register fields from table where columns are merged into one cell.

        Format: "BitLocation Register Description Attributes" all in one cell
        Each row: "0 Field Name - Description RW"
        """
        fields = []

        # Pattern to extract: bit number + field name/desc + attribute at end
        field_pattern = re.compile(
            r'^(\d+(?::\d+)?)\s+(.+?)\s+(RW|RO|RWC|RW1C|RW1CS|RsvdP|RsvdZ|HwInit)\s*$',
            re.MULTILINE
        )

        for row in table:
            if not row:
                continue

            # Get the cell content (usually first or second cell)
            cell_text = ""
            for cell in row:
                if cell and len(str(cell)) > 20:  # Long enough to be field data
                    cell_text = str(cell)
                    break

            if not cell_text:
                continue

            # Split by newlines and parse each line as a potential field
            lines = cell_text.split('\n')

            for line in lines:
                line = line.strip()
                if not line or len(line) < 10:
                    continue

                match = field_pattern.match(line)
                if match:
                    bit_str = match.group(1)
                    field_desc = match.group(2).strip()
                    attribute = match.group(3)

                    # Extract field name (usually before the dash or first sentence)
                    field_name = field_desc
                    if '-' in field_desc:
                        field_name = field_desc.split('-')[0].strip()
                    elif '.' in field_desc:
                        field_name = field_desc.split('.')[0].strip()

                    # Rest is description
                    description = field_desc

                    fields.append(RegisterField(
                        bits=bit_str,
                        name=field_name,
                        attribute=attribute,
                        description=description
                    ))

        return fields

    def _parse_fields_from_text(self, text: str) -> List[RegisterField]:
        """
        Parse register fields directly from text.

        This handles the case where pdfplumber table extraction fails and all
        table data is in merged cells. We parse text line by line looking for
        patterns like:

        "0 I/O Space Enable- Controls..."
        "continued description text..."
        "more description... RW"

        The attribute (RW, RO, etc.) appears at the end of the description,
        which may span multiple lines.

        Args:
            text: Page text content

        Returns:
            List of RegisterField objects
        """
        fields = []
        lines = text.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Look for line starting with bit number followed by field name
            # Pattern: "0 Field Name-" or "7:5 Field Name -"
            # Note: Use non-lazy match to capture full field name until dash
            match = re.match(r'^(\d+(?::\d+)?)\s+([A-Z][\w\s/]+?)\s*-', line)

            if match:
                bit_str = match.group(1)
                field_name = match.group(2).strip()

                # Collect the full description across multiple lines
                # Continue until we find a line ending with an attribute or hit next field
                first_desc_line = line[match.end():].strip()
                description_lines = []
                j = i + 1
                attribute = None

                # Check if first line ends with attribute
                for attr in self.ATTRIBUTES:
                    if first_desc_line.endswith(' ' + attr) or first_desc_line.endswith(attr):
                        # Extract attribute from first line
                        if first_desc_line.endswith(' ' + attr):
                            first_desc_line = first_desc_line[:-len(attr)-1].strip()
                        else:
                            first_desc_line = first_desc_line[:-len(attr)].strip()
                        attribute = attr
                        break

                description_lines.append(first_desc_line)

                # Always collect continuation lines regardless of attribute position
                # The attribute appearing at the end of first line is just table column layout
                # Continue until we hit a structural boundary (next field, page footer, etc.)
                while j < len(lines):
                    next_line = lines[j].strip()

                    # Stop if we hit another field (starts with bit number)
                    if re.match(r'^\d+(?::\d+)?\s+[A-Z]', next_line):
                        break

                    # Stop if we hit a register header or table header or page number
                    if re.match(r'^\d+\.\d+\.\d+', next_line) or \
                       'BitLocation' in next_line or \
                       'Register Description' in next_line or \
                       next_line.startswith('Table ') or \
                       next_line.startswith('Figure ') or \
                       next_line.startswith('Page ') or \
                       re.match(r'^Page \d+$', next_line):
                        break

                    # Check if this line ends with an attribute
                    # Note: We may have already found attribute on first line from table column
                    # Continue collecting description regardless
                    line_has_attr = False
                    for attr in self.ATTRIBUTES:
                        if next_line.endswith(attr) or next_line.endswith(attr + '.'):
                            # Found an attribute marker, but keep collecting description
                            if next_line.endswith(attr + '.'):
                                desc_part = next_line[:-len(attr)-1].strip()
                            elif next_line.endswith(attr):
                                desc_part = next_line[:-len(attr)].strip()
                            else:
                                desc_part = next_line

                            # Save attribute if we don't have one yet
                            if not attribute:
                                attribute = attr

                            if desc_part:
                                description_lines.append(desc_part)
                            line_has_attr = True
                            break

                    # Add this line to description if it doesn't have attribute marker
                    if not line_has_attr and next_line:
                        description_lines.append(next_line)

                    j += 1

                # Join description lines
                description = ' '.join(description_lines)

                # If we didn't find attribute in multiline, check if it's at end of first line
                if not attribute:
                    for attr in self.ATTRIBUTES:
                        if description.endswith(attr) or description.endswith(attr + '.'):
                            if description.endswith(attr + '.'):
                                description = description[:-len(attr)-1].strip()
                                attribute = attr
                            else:
                                description = description[:-len(attr)].strip()
                                attribute = attr
                            break

                # Default to RW if no attribute found
                if not attribute:
                    attribute = "RW"

                # Create field
                fields.append(RegisterField(
                    bits=bit_str,
                    name=field_name,
                    attribute=attribute,
                    description=description
                ))

                # Move to where we stopped
                i = j
            else:
                i += 1

        return fields

    def _is_bit_pattern(self, s: str) -> bool:
        """Check if string looks like a bit pattern (e.g., '0', '7:5', '15:12')."""
        if not s:
            return False

        # Single bit: just a number
        if s.isdigit():
            return True

        # Bit range: number:number
        if ':' in s:
            parts = s.split(':')
            if len(parts) == 2:
                try:
                    int(parts[0])
                    int(parts[1])
                    return True
                except ValueError:
                    pass

        return False

    def save_to_json(self, output_path: str):
        """Save parsed registers to JSON file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to serializable format
        data = {
            name: {
                'section': reg.section,
                'name': reg.name,
                'offset': reg.offset,
                'chapter': reg.chapter,
                'page': reg.page,
                'description': reg.description,
                'fields': [asdict(field) for field in reg.fields]
            }
            for name, reg in self.registers.items()
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        print(f"✓ Saved {len(self.registers)} registers to {output_path}")


def main():
    """CLI entry point for PDF register parser."""
    import sys

    # Default paths
    pdf_path = Path(__file__).parent.parent.parent.parent / "SYkDTqhOLhpUTnMx.pdf"
    output_path = Path(__file__).parent.parent.parent / "data" / "registers" / "registers.json"

    # Allow override from command line
    if len(sys.argv) > 1:
        pdf_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])

    if not PDFPLUMBER_AVAILABLE:
        print("Error: pdfplumber not installed")
        print("Install with: pip install pdfplumber")
        sys.exit(1)

    print(f"Parsing registers from PDF: {pdf_path}")

    parser = PDFRegisterParser(str(pdf_path))
    registers = parser.parse(start_page=673, end_page=900)

    print(f"\nFound {len(registers)} registers")

    # Print sample
    if registers:
        print("\nSample registers:")
        for i, (name, reg) in enumerate(list(registers.items())[:5]):
            print(f"  {i+1}. {reg.name} (Offset {reg.offset})")
            print(f"     Section: {reg.section}, Page: {reg.page}")
            print(f"     Fields: {len(reg.fields)}")

    # Save to JSON
    parser.save_to_json(str(output_path))


if __name__ == "__main__":
    main()
