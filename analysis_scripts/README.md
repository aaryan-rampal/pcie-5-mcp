# PCIe Spec Analysis Scripts

Scripts used to analyze the PCIe 5.0 Base Specification PDF structure.

## Main Pipeline

1. **extract_to_text.py** - Extracts entire PDF to `pcie_spec_full_text.txt` (3.3MB)
2. **analyze_structure.sh** - Uses grep to analyze structural patterns
3. **final_stats.sh** - Generates comprehensive statistics

## Test Scripts (Exploratory)

- `test_1_basic_info.py` - Basic PDF info and first pages
- `test_2_toc_extraction.py` - TOC extraction experiments
- `test_3_sample_content.py` - Sample pages from different sections
- `test_4_find_ltssm.py` - Find LTSSM-related content
- `test_5_find_registers.py` - Find register definitions

## Output Files

- `pcie_spec_full_text.txt` - Full PDF extraction (grep-able)
- `analysis_results.txt` - Structural analysis output
- `final_stats.txt` - Statistics and key findings
- `samples.txt` - Sample content from key pages

## Usage

```bash
# Extract PDF to text (first time only)
.venv/bin/python extract_to_text.py

# Run analysis
./analyze_structure.sh
./final_stats.sh

# Quick searches
grep -i "LTSSM" pcie_spec_full_text.txt
grep "Register" pcie_spec_full_text.txt | grep "^[0-9]*:[0-9]"
```

## Key Insights

See `../PCIe_doc_summary.md` for the full analysis report.
