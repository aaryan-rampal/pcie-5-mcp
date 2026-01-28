#!/bin/bash
# Detailed structural analysis of PCIe spec

TEXT="pcie_spec_full_text.txt"
OUT="analysis_results.txt"

echo "Running structural analysis..." > $OUT

echo "=== 1. CHAPTER STRUCTURE ===" >> $OUT
echo "Main chapters (lines starting with single digit):" >> $OUT
grep -n "^[0-9]\. " $TEXT | head -20 >> $OUT

echo -e "\n=== 2. LTSSM PAGES ===" >> $OUT
echo "Pages containing LTSSM:" >> $OUT
grep -i "LTSSM" $TEXT -B 3 | grep "^PAGE" | sort -u >> $OUT

echo -e "\n=== 3. REGISTER SECTIONS ===" >> $OUT
echo "Section headers about registers:" >> $OUT
grep "Register" $TEXT | grep -E "^[0-9]+\.[0-9]" | head -50 >> $OUT

echo -e "\n=== 4. KEY SECTION PATTERNS ===" >> $OUT
echo "Sections about Link Training:" >> $OUT
grep -i "Link Training" $TEXT | grep -E "^[0-9]+\.[0-9]" | head -20 >> $OUT

echo -e "\n=== 5. TABLE PATTERNS ===" >> $OUT
echo "Table references (first 50):" >> $OUT
grep -E "Table [0-9]+-[0-9]+" $TEXT | head -50 >> $OUT

echo -e "\n=== 6. CAPABILITY STRUCTURES ===" >> $OUT
echo "Capability sections:" >> $OUT
grep "Capability" $TEXT | grep -E "^[0-9]+\.[0-9]" | head -30 >> $OUT

echo -e "\n=== 7. STATE MACHINE MENTIONS ===" >> $OUT
echo "State machine references:" >> $OUT
grep -i "State Machine" $TEXT | head -30 >> $OUT

echo -e "\n=== 8. ERROR HANDLING ===" >> $OUT
echo "Error-related sections:" >> $OUT
grep -i "Error" $TEXT | grep -E "^[0-9]+\.[0-9]" | head -20 >> $OUT

echo "Analysis complete! Results in $OUT"
wc -l $OUT
