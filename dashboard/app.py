"""EGOFET Sample & Measurement Dashboard."""

import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.database import (
    DB_PATH,
    SAMPLE_STEPS,
    add_ink_batch,
    add_measurement,
    add_step,
    add_wafer,
    get_connection,
    get_sample,
    get_wafer,
    init_db,
    list_ink_batches,
    list_samples,
    list_wafers,
    update_step,
)

STATUS_COLORS = {
    "pending": "#6c757d",
    "in_progress": "#ffc107",
    "completed": "#28a745",
    "aborted": "#dc3545",
}
STATUS_EMOJI = {
    "pending": "⬜",
    "in_progress": "🔄",
    "completed": "✅",
    "aborted": "❌",
}

st.set_page_config(page_title="EGOFET Dashboard", layout="wide")
st.title("🧪 EGOFET Sample Tracker")

init_db()

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📋 Sample Board", "➕ New Wafer", "🔍 Sample Detail", "🧪 Ink Tracker", "📊 Quick Status"]
)

# ── Tab 1: Sample Board ──────────────────────────────────────────────

with tab1:
    st.subheader("All Samples")

    wafers = list_wafers()
    if not wafers:
        st.info("No wafers yet. Go to 'New Wafer' tab to add your first batch.")
    else:
        wafer_options = {w["name"]: w["id"] for w in wafers}
        selected_wafer = st.selectbox(
            "Filter by wafer", ["All"] + list(wafer_options.keys())
        )

        wid = None if selected_wafer == "All" else wafer_options[selected_wafer]
        samples = list_samples(wafer_id=wid)

        cols = st.columns(3)
        for i, s in enumerate(samples):
            with cols[i % 3]:
                step_text = s["step_status"] or "no_steps"
                last_step = step_text.split(",")[-1].strip() if step_text else "—"
                step_type, step_status = (last_step.split(":", 1) + ["", "pending"])[:2]
                color = STATUS_COLORS.get(step_status.strip(), "#6c757d")
                emoji = STATUS_EMOJI.get(step_status.strip(), "⬜")

                st.markdown(
                    f"""<div style="border:2px solid {color}; border-radius:10px;
                    padding:12px; margin:4px 0;">
                    <strong>{emoji} {s['label']}</strong><br>
                    <small>Wafer: {s['wafer_name']}</small><br>
                    <small style="color:{color}">{SAMPLE_STEPS.get(step_type.strip(), step_type)}</small><br>
                    <small>{step_status}</small>
                    </div>""",
                    unsafe_allow_html=True,
                )
                if st.button("View", key=f"view_{s['id']}"):
                    st.session_state["selected_sample"] = s["id"]

# ── Tab 2: New Wafer ─────────────────────────────────────────────────

with tab2:
    st.subheader("Register New Wafer")

    col1, col2 = st.columns(2)
    with col1:
        date_str = st.text_input("Date (YYMMDD)", datetime.now().strftime("%y%m%d"))
        wafer_num = st.number_input("Wafer number", min_value=1, value=1, step=1)
        substrate = st.selectbox("Substrate", ["Kapton", "Si/SiO2", "Glass"])
        thickness = st.selectbox("Thickness", ["75um", "125um", "150um", "300nm SiO2"])

    with col2:
        n_pieces = st.slider("Pieces per wafer", 1, 8, 4)
        n_devices = st.slider("Devices per piece", 1, 6, 3)
        notes = st.text_area("Notes", placeholder="e.g., Evaporation: 5nm Cr + 40nm Au")

    wafer_name = f"{date_str}_W{wafer_num}"

    if st.button("Create Wafer", type="primary"):
        try:
            wid = add_wafer(
                name=wafer_name,
                substrate=substrate,
                size=thickness,
                n_pieces=n_pieces,
                n_devices_per_piece=n_devices,
                notes=notes,
            )
            st.success(
                f"Wafer **{wafer_name}** created with {n_pieces} pieces "
                f"x {n_devices} devices ({n_pieces * n_devices} total devices)."
            )
            st.balloons()
        except Exception as e:
            st.error(f"Error: {e}")

    st.divider()
    st.caption(
        "Naming convention: `YYMMDD_W{N}` → Pieces: `YYMMDD_W{N}_P{M}` "
        "→ Devices: numbered 1-{N}"
    )

# ── Tab 3: Sample Detail ─────────────────────────────────────────────

with tab3:
    st.subheader("Sample Detail")

    samples_all = list_samples()
    sample_map = {s["label"]: s["id"] for s in samples_all}

    if not sample_map:
        st.info("No samples. Create a wafer first.")
    else:
        # Check if selected from board
        preselected = st.session_state.get("selected_sample")
        preselected_label = None
        if preselected:
            for s in samples_all:
                if s["id"] == preselected:
                    preselected_label = s["label"]
                    break

        selected_label = st.selectbox(
            "Select sample",
            list(sample_map.keys()),
            index=(
                list(sample_map.keys()).index(preselected_label)
                if preselected_label
                else 0
            ),
        )
        sample = get_sample(sample_map[selected_label])

        if sample:
            st.markdown(f"### {sample['label']}")
            st.caption(f"Wafer: **{sample['wafer_name']}** | Piece #{sample['piece_number']}")

            # Devices
            st.markdown("#### Devices")
            dev_df = pd.DataFrame(sample["devices"])
            dev_df["label"] = dev_df.apply(
                lambda r: f"{sample['label']}_D{r['device_number']}", axis=1
            )
            st.dataframe(dev_df[["device_number", "channel_w_um", "channel_l_um"]], use_container_width=True)

            # Steps timeline
            st.markdown("#### Steps")
            if sample["steps"]:
                for step in sample["steps"]:
                    status = step["status"]
                    emoji = STATUS_EMOJI.get(status, "⬜")
                    params = json.loads(step["params_json"] or "{}")
                    name = SAMPLE_STEPS.get(step["step_type"], step["step_type"])

                    with st.expander(f"{emoji} {name} — {status}", expanded=(status == "in_progress")):
                        c1, c2 = st.columns(2)
                        with c1:
                            new_status = st.selectbox(
                                "Status",
                                ["pending", "in_progress", "completed", "aborted"],
                                index=["pending", "in_progress", "completed", "aborted"].index(status),
                                key=f"status_{step['id']}",
                            )
                        with c2:
                            notes = st.text_area(
                                "Notes",
                                value=step["notes"] or "",
                                key=f"notes_{step['id']}",
                            )

                        if params:
                            st.caption(f"Params: {json.dumps(params, indent=2)}")

                        if st.button("Update", key=f"update_{step['id']}"):
                            update_step(step["id"], status=new_status, notes=notes)
                            st.rerun()

                        started = step["started_at"] or "—"
                        completed = step["completed_at"] or "—"
                        st.caption(f"Started: {started} | Completed: {completed}")
            else:
                st.info("No steps recorded.")

            # Add step
            st.markdown("#### Add Step")
            c1, c2 = st.columns(2)
            with c1:
                new_step_type = st.selectbox("Step", list(SAMPLE_STEPS.keys()), format_func=lambda x: SAMPLE_STEPS[x])
                new_status = st.selectbox("Initial status", ["pending", "in_progress", "completed"])
            with c2:
                new_notes = st.text_area("Notes (markdown)")
                new_params = st.text_area("Params (JSON)", "{}")

            if st.button("Add Step", type="primary"):
                try:
                    params_dict = json.loads(new_params)
                except json.JSONDecodeError:
                    params_dict = {}
                add_step(
                    sample["id"],
                    new_step_type,
                    status=new_status,
                    params=params_dict,
                    notes=new_notes,
                )
                st.rerun()

# ── Tab 4: Ink Tracker ───────────────────────────────────────────────

with tab4:
    st.subheader("OSC Ink Batches")

    inks = list_ink_batches()
    if inks:
        ink_df = pd.DataFrame(inks)
        cols_show = ["name", "sc_weight_mg", "ps_weight_mg", "cb_volume_ml", "ratio_osc_ps", "prepared_at"]
        st.dataframe(ink_df[[c for c in cols_show if c in ink_df.columns]], use_container_width=True)
    else:
        st.info("No ink batches.")

    st.divider()
    st.markdown("#### New Ink Batch")

    c1, c2, c3 = st.columns(3)
    with c1:
        ink_date = st.text_input("Batch ID", datetime.now().strftime("INK-%y%m%d"))
        sc_w = st.number_input("SC weight (mg)", min_value=0.0, step=0.1, format="%.2f")
        ps_w = st.number_input("PS weight (mg)", min_value=0.0, step=0.1, format="%.2f")
    with c2:
        cb_v = st.number_input("CB volume (mL)", min_value=0.0, step=0.01, format="%.3f")
        ratio = st.selectbox("Ratio OSC:PS", ["4:1", "3:1", "2:1", "1:1"])
        sc_mat = st.text_input("SC material", "diFT-TES-ADT")
    with c3:
        ps_mw = st.number_input("PS MW (g/mol)", value=10000)
        ink_notes = st.text_area("Notes")

    if st.button("Add Ink Batch", type="primary"):
        try:
            add_ink_batch(ink_date, sc_w, ps_w, cb_v, sc_material=sc_mat, ps_mw=ps_mw, ratio=ratio, notes=ink_notes)
            st.success(f"Ink **{ink_date}** added.")
            st.rerun()
        except Exception as e:
            st.error(str(e))

# ── Tab 5: Quick Status ──────────────────────────────────────────────

with tab5:
    st.subheader("Status Summary")

    conn = get_connection()
    total_wafers = conn.execute("SELECT COUNT(*) FROM wafers").fetchone()[0]
    total_samples = conn.execute("SELECT COUNT(*) FROM samples").fetchone()[0]
    total_devices = conn.execute("SELECT COUNT(*) FROM devices").fetchone()[0]
    total_measurements = conn.execute("SELECT COUNT(*) FROM measurements").fetchone()[0]

    step_counts = conn.execute(
        "SELECT status, COUNT(*) as n FROM steps GROUP BY status"
    ).fetchall()
    conn.close()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Wafers", total_wafers)
    m2.metric("Samples", total_samples)
    m3.metric("Devices", total_devices)
    m4.metric("Measurements", total_measurements)

    if step_counts:
        st.markdown("#### Steps by status")
        step_df = pd.DataFrame([dict(r) for r in step_counts])
        st.bar_chart(step_df.set_index("status"))

    st.divider()
    st.caption(f"Database: `{DB_PATH}`")
