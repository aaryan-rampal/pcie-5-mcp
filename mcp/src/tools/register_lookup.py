"""
MCP Tool: Register Lookup

Provides fast, structured lookup of PCIe register definitions.
Wraps the parsed register database.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any


class RegisterLookupTool:
    """Tool for looking up PCIe register definitions."""

    def __init__(self, register_db_path: str):
        """
        Initialize register lookup tool.

        Args:
            register_db_path: Path to registers.json
        """
        self.register_db_path = Path(register_db_path)
        self.registers: Dict[str, Any] = {}

        if self.register_db_path.exists():
            with open(self.register_db_path, 'r') as f:
                self.registers = json.load(f)

    def lookup(
        self,
        name: Optional[str] = None,
        offset: Optional[str] = None,
        field: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Look up register definition.

        Args:
            name: Register name (e.g., "Device Control")
            offset: Hex offset (e.g., "08h")
            field: Specific bit field name

        Returns:
            Register definition with fields, or error message
        """
        if not self.registers:
            return {
                'error': 'Register database not loaded',
                'hint': 'Run register parser first'
            }

        # Search by name
        if name:
            result = self._lookup_by_name(name)
            if result:
                if field:
                    return self._get_field(result, field)
                return result

        # Search by offset
        if offset:
            result = self._lookup_by_offset(offset)
            if result:
                if field:
                    return self._get_field(result, field)
                return result

        return {
            'error': 'Register not found',
            'searched': {
                'name': name,
                'offset': offset,
                'field': field
            }
        }

    def _lookup_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Look up register by name (case-insensitive)."""
        name_lower = name.lower()

        for reg_name, reg_data in self.registers.items():
            if name_lower in reg_name.lower():
                return {
                    'name': reg_data['name'],
                    'section': reg_data['section'],
                    'offset': reg_data['offset'],
                    'chapter': reg_data['chapter'],
                    'fields': reg_data['fields']
                }

        return None

    def _lookup_by_offset(self, offset: str) -> Optional[Dict[str, Any]]:
        """Look up register by offset."""
        offset = offset.lower()
        if not offset.endswith('h'):
            offset += 'h'

        for reg_name, reg_data in self.registers.items():
            if reg_data['offset'].lower() == offset:
                return {
                    'name': reg_data['name'],
                    'section': reg_data['section'],
                    'offset': reg_data['offset'],
                    'chapter': reg_data['chapter'],
                    'fields': reg_data['fields']
                }

        return None

    def _get_field(self, register: Dict[str, Any], field_name: str) -> Dict[str, Any]:
        """Get specific field from register."""
        field_name_lower = field_name.lower()

        for field in register['fields']:
            if field_name_lower in field['name'].lower():
                return {
                    'register': register['name'],
                    'offset': register['offset'],
                    'field': field,
                    'section': register['section']
                }

        return {
            'error': f"Field '{field_name}' not found in register '{register['name']}'",
            'available_fields': [f['name'] for f in register['fields']]
        }

    def list_registers(self) -> Dict[str, Any]:
        """List all available registers."""
        return {
            'total': len(self.registers),
            'registers': [
                {
                    'name': reg_data['name'],
                    'offset': reg_data['offset'],
                    'section': reg_data['section']
                }
                for reg_data in self.registers.values()
            ]
        }
