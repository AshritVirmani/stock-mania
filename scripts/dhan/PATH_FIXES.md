# Dhan Scripts Path Fixes

## ✅ Fixed Path Issues

All Dhan scripts have been updated to use the correct paths after project reorganization.

### Changes Made:

1. **PROJECT_ROOT calculation:**
   - **Before:** `PROJECT_ROOT = SCRIPT_DIR.parent` → pointed to `scripts/`
   - **After:** `PROJECT_ROOT = SCRIPT_DIR.parent.parent` → points to actual project root

2. **LEGACY_SCRIPTS_DIR path:**
   - **Before:** `PROJECT_ROOT / "legacy_scripts"` → wrong location
   - **After:** `PROJECT_ROOT / "scripts" / "legacy"` → correct location

### Files Updated:

- ✅ `00_complete_setup_dhan.py`
- ✅ `01_fetch_intraday_data.py`
- ✅ `04_intraday_ta_accuracy_analysis.py`
- ✅ `05_intraday_pattern_discovery.py`
- ✅ `06_fetch_options_data.py`

### Path Structure:

```
ta/                                    (PROJECT_ROOT)
├── scripts/
│   ├── dhan/                         (SCRIPT_DIR)
│   │   └── 00_complete_setup_dhan.py
│   └── legacy/                       (LEGACY_SCRIPTS_DIR)
│       └── complete_setup.py
└── analysis_results/                 (Output directory)
    └── {SYMBOL}/
        └── intraday_analysis/
```

### Verification:

All scripts now correctly:
- Point to project root (not `scripts/`)
- Reference `scripts/legacy/` for legacy scripts
- Save outputs to `analysis_results/{SYMBOL}/intraday_analysis/`

## 🚀 Usage

Scripts should now work correctly:

```bash
# Complete Dhan workflow
python3 scripts/dhan/00_complete_setup_dhan.py NMDC.NS --start 2024-11-01 --end 2024-11-24 --interval 1

# Individual steps
python3 scripts/dhan/01_fetch_intraday_data.py NMDC.NS --from-date 2024-11-01 --to-date 2024-11-24
```

All outputs will be saved to: `analysis_results/{SYMBOL}/intraday_analysis/`

