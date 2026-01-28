#!/bin/bash
# Sample actual content from key pages

TEXT="pcie_spec_full_text.txt"

echo "=== SAMPLE 1: LTSSM Content (Page 315) ===" > samples.txt
sed -n '/^PAGE 315$/,/^PAGE 316$/p' $TEXT | head -50 >> samples.txt

echo -e "\n=== SAMPLE 2: Register Definition (Page 725) ===" >> samples.txt
sed -n '/^PAGE 725$/,/^PAGE 726$/p' $TEXT | head -50 >> samples.txt

echo -e "\n=== SAMPLE 3: Configuration Space (Page 685) ===" >> samples.txt
sed -n '/^PAGE 685$/,/^PAGE 686$/p' $TEXT | head -50 >> samples.txt

echo -e "\n=== SAMPLE 4: Error Handling (Page 507) ===" >> samples.txt
sed -n '/^PAGE 507$/,/^PAGE 508$/p' $TEXT | head -50 >> samples.txt

echo -e "\n=== SAMPLE 5: TOC Structure (Page 3) ===" >> samples.txt
sed -n '/^PAGE 3$/,/^PAGE 4$/p' $TEXT >> samples.txt

echo "Samples written to samples.txt"
