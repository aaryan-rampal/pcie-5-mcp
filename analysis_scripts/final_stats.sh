#!/bin/bash
# Final comprehensive stats

TEXT="pcie_spec_full_text.txt"

echo "PCIe 5.0 Spec - Final Statistics" > final_stats.txt
echo "=================================" >> final_stats.txt

echo -e "\n1. DOCUMENT SIZE:" >> final_stats.txt
echo "   Total pages: $(grep -c '^PAGE' $TEXT)" >> final_stats.txt
echo "   Total lines: $(wc -l < $TEXT)" >> final_stats.txt
echo "   File size: $(ls -lh $TEXT | awk '{print $5}')" >> final_stats.txt

echo -e "\n2. MAJOR CHAPTERS (from TOC):" >> final_stats.txt
sed -n '/^PAGE 3$/,/^PAGE 10$/p' $TEXT | grep -E "^[0-9]\. " >> final_stats.txt

echo -e "\n3. KEY HARDWARE CONCEPTS (mention counts):" >> final_stats.txt
echo "   LTSSM: $(grep -ic 'LTSSM' $TEXT)" >> final_stats.txt
echo "   Register: $(grep -ic 'Register' $TEXT)" >> final_stats.txt
echo "   Capability: $(grep -ic 'Capability' $TEXT)" >> final_stats.txt
echo "   Configuration Space: $(grep -ic 'Configuration Space' $TEXT)" >> final_stats.txt
echo "   Link Training: $(grep -ic 'Link Training' $TEXT)" >> final_stats.txt
echo "   State Machine: $(grep -ic 'State Machine' $TEXT)" >> final_stats.txt
echo "   Flow Control: $(grep -ic 'Flow Control' $TEXT)" >> final_stats.txt
echo "   Transaction Layer: $(grep -ic 'Transaction Layer' $TEXT)" >> final_stats.txt
echo "   Data Link Layer: $(grep -ic 'Data Link Layer' $TEXT)" >> final_stats.txt
echo "   Physical Layer: $(grep -ic 'Physical Layer' $TEXT)" >> final_stats.txt
echo "   Error: $(grep -ic 'Error' $TEXT)" >> final_stats.txt
echo "   Completion Timeout: $(grep -ic 'Completion Timeout' $TEXT)" >> final_stats.txt
echo "   Retry: $(grep -ic 'Retry' $TEXT)" >> final_stats.txt
echo "   Ordered Set: $(grep -ic 'Ordered Set' $TEXT)" >> final_stats.txt

echo -e "\n4. REFERENCE PATTERNS:" >> final_stats.txt
echo "   'see Section' refs: $(grep -c 'see Section' $TEXT)" >> final_stats.txt
echo "   'Table' refs: $(grep -c 'Table ' $TEXT)" >> final_stats.txt
echo "   'Figure' refs: $(grep -c 'Figure ' $TEXT)" >> final_stats.txt

echo -e "\n5. CHAPTER 4 (Physical Layer) - LTSSM PAGES:" >> final_stats.txt
grep -B 5 -i "LTSSM" $TEXT | grep "^PAGE" | sort -u | head -30 >> final_stats.txt

echo -e "\n6. CHAPTER 7 (Config Registers) - KEY PAGES:" >> final_stats.txt
sed -n '/^PAGE 673$/,/^PAGE 900$/p' $TEXT | grep "^PAGE" | head -20 >> final_stats.txt

echo "Stats written to final_stats.txt"
cat final_stats.txt
