#!/bin/bash
# Quick analysis of extracted PCIe spec text using grep

TEXT_FILE="pcie_spec_full_text.txt"

echo "================================================================================"
echo "PCIe Spec Text Analysis"
echo "================================================================================"

echo ""
echo "1. LTSSM Content:"
echo "   Total mentions: $(grep -i "LTSSM" $TEXT_FILE | wc -l)"
echo "   Pages with LTSSM:"
grep -i "LTSSM" $TEXT_FILE -B 5 | grep "^PAGE" | sort -u | head -20

echo ""
echo "2. Register Definitions:"
echo "   'Register' mentions: $(grep -i "Register" $TEXT_FILE | wc -l)"
echo "   Section headers with 'Register' (first 20):"
grep -n "Register" $TEXT_FILE | grep "^[0-9]*:[0-9][0-9]*\.[0-9]" | head -20

echo ""
echo "3. Key Hardware Terms:"
echo "   - Configuration Space: $(grep -i "Configuration Space" $TEXT_FILE | wc -l)"
echo "   - Capability: $(grep -i "Capability" $TEXT_FILE | wc -l)"
echo "   - State Machine: $(grep -i "State Machine" $TEXT_FILE | wc -l)"
echo "   - Link Training: $(grep -i "Link Training" $TEXT_FILE | wc -l)"
echo "   - Flow Control: $(grep -i "Flow Control" $TEXT_FILE | wc -l)"
echo "   - Transaction Layer: $(grep -i "Transaction Layer" $TEXT_FILE | wc -l)"
echo "   - Physical Layer: $(grep -i "Physical Layer" $TEXT_FILE | wc -l)"

echo ""
echo "4. Cross-references:"
echo "   Section references: $(grep -E "see Section [0-9]" $TEXT_FILE | wc -l)"
echo "   Table references: $(grep -E "Table [0-9]" $TEXT_FILE | wc -l)"
echo "   Figure references: $(grep -E "Figure [0-9]" $TEXT_FILE | wc -l)"

echo ""
echo "5. Sample cross-references:"
grep -E "see Section [0-9]" $TEXT_FILE | head -10

echo ""
echo "================================================================================"
echo "Analysis complete!"
echo "================================================================================"
