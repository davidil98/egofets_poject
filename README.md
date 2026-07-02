# EGOFET Project — Workflow for Fabrication, Measurement & Analysis

Experimental data management toolkit for Electrolyte-Gated Organic Field-Effect Transistors
(EGOFETs). Covers the full cycle: wafer fabrication tracking → measurement → parameter
extraction.

## Quick start

```bash
# Create conda environment (if not already done)
conda env create -f environment.yml
conda activate egofets

# Launch the sample dashboard
streamlit run dashboard/app.py
```

## Project structure

```
egofets-project/
├── samples.db                          # SQLite database (sample/measurement tracking)
├── environment.yml                     # Conda environment
│
├── src/
│   ├── readers.py                      # HDF5 → pandas (Keithley 2600 data)
│   ├── plotting.py                     # Standardised transfer/output/stability plots
│   ├── analysis.py                     # Vth (sqrt/linear), SS, on/off ratio, mobility
│   └── database.py                     # SQLite schema + full CRUD
│
├── dashboard/
│   └── app.py                          # Streamlit web UI for sample tracking
│
├── notebooks/
│   ├── 00_lab_journal/                 # Fill-in templates for lab sessions
│   │   ├── template_wafer_fab.ipynb    #   Photolithography → evaporation → lift-off
│   │   ├── template_sam_bams.ipynb     #   SAM + semiconductor deposition
│   │   ├── template_ink_prep.ipynb     #   OSC ink formulation
│   │   └── template_measurement.ipynb  #   Link HDF5 files to devices in DB
│   ├── 02_transfer_curves/             # Transfer curve analysis (Id vs Vgs)
│   │   └── 01_transfer_analysis.ipynb
│   └── 03_output_curves/               # Output curve analysis (Id vs Vds)
│       └── 01_output_analysis.ipynb
│
├── data/
│   ├── raw/                            # Raw HDF5 files from Keithley (by date)
│   ├── processed/                      # (optional) cleaned/derived data
│   └── photos/                         # Sample photos (by sample/date)
│
├── output/                             # Generated figures (PNG)
├── docs/                               # Fabrication protocols (reference)
└── README.md
```

## Naming convention

Every sample is uniquely identified with the pattern:

```
YYMMDD_W{N}_P{M}_D{K}
```

| Component | Meaning | Example |
|-----------|---------|---------|
| `YYMMDD`  | Date wafer was fabricated | `260626` = 26 June 2026 |
| `W{N}`    | Wafer number that day | `W1`, `W2` |
| `P{M}`    | Piece number (after cutting) | `P1`–`P4` |
| `D{K}`    | Device number on that piece | `D1`–`D3` |

Example: `260626_W1_P2_D3` — third device on the second piece of the first wafer from
June 26, 2026.

Ink batches follow: `INK-YYMMDD` (e.g., `INK-260626`).

## Workflow

### 1. Fabrication (use lab journal templates)

Copy the appropriate template from `notebooks/00_lab_journal/`, fill in your parameters,
and execute all cells:

| You are doing... | Copy this template |
|------------------|--------------------|
| Photolithography + evaporation + lift-off + cutting | `template_wafer_fab.ipynb` |
| SAM (PFBT) + BAMS deposition | `template_sam_bams.ipynb` |
| Preparing OSC ink (diFT:PS in CB) | `template_ink_prep.ipynb` |
| Electrical measurement session | `template_measurement.ipynb` |

Each template registers your data in `samples.db`. The dashboard reflects new entries
immediately.

### 2. Measurement

1. Save Keithley HDF5 output to `data/raw/YYYY-MM-DD_description.hdf5`.
2. Open `template_measurement.ipynb`, set the sample label and HDF5 path, run cells.
3. Use `notebooks/02_transfer_curves/` and `notebooks/03_output_curves/` for plots.

### 3. Monitor with the dashboard

```bash
streamlit run dashboard/app.py
```

Tabs available:

| Tab | What it shows |
|-----|---------------|
| **Sample Board** | All samples with color-coded status cards |
| **New Wafer** | Register a wafer → auto-creates pieces and devices |
| **Sample Detail** | Timeline of steps per sample, editable status/notes/params |
| **Ink Tracker** | OSC ink batches with masses, volumes, and ratios |
| **Quick Status** | Aggregate metrics (wafer/sample/device/measurement counts) |

### 4. Analyse

```bash
jupyter notebook notebooks/02_transfer_curves/01_transfer_analysis.ipynb
```

Extracts for every transfer measurement:
- Threshold voltage $V_{th}$ (√Ids extrapolation and linear method)
- Subthreshold swing $SS$ (mV/dec)
- $I_{on}/I_{off}$ ratio
- Goodness of fit ($R^2$)

```bash
jupyter notebook notebooks/03_output_curves/01_output_analysis.ipynb
```

Plots $I_{DS}$ vs $V_{DS}$ at stepped $V_{GS}$, showing linear and saturation regions.

## Database schema

```
wafers        id, name, substrate, size_mm, created_at, notes, photo_path
samples       id, wafer_id, piece_number, label, functionalization, created_at, notes
devices       id, sample_id, device_number, channel_w_um, channel_l_um, notes
steps         id, sample_id, step_type, status, started_at, completed_at,
              params_json, notes, photo_paths
measurements  id, device_id, sample_id, measurement_type, measured_at,
              hdf5_path, notes
ink_batches   id, name, sc_material, ps_mw_gmol, sc_weight_mg, ps_weight_mg,
              cb_volume_ml, ratio_osc_ps, prepared_at, usable_after, notes
```

Step types (matching the fabrication protocol): `photolithography`, `developing`,
`evaporation`, `lift_off`, `cutting`, `sam`, `bams`, `functionalization`, `measurement`.

Step statuses: `pending` → `in_progress` → `completed` (or `aborted`).

## Measurement data format

The HDF5 files are generated by a Keithley 2600 SourceMeter with two channels (a/GS,
b/DS). The reader (`src/readers.py`) automatically detects the measurement mode from the
`measurement_mode` attribute, regardless of the group name:

- **transfer** — $V_{GS}$ sweep at fixed $V_{DS}$; groups contain `curve_N` sub-groups
- **output** — $V_{DS}$ sweep at fixed $V_{GS}$; groups contain `curve_N` sub-groups
- **stability** — chronoamperometry; datasets directly in the group

Each curve stores: `measured_V_GS`, `measured_V_DS`, `measured_I_DS`, `measured_I_GS`,
`calculated_V_GS`, `calculated_V_DS`, `time`.

## Dependencies

```
python>=3.10
h5py, pandas, numpy, scipy        # data processing
matplotlib, seaborn               # plotting
jupyter, ipykernel                # notebooks
streamlit                         # dashboard
python-docx, pymupdf              # document parsing (optional)
```

Install everything: `conda env create -f environment.yml`
