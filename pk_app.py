import streamlit as st
import pandas as pd
import numpy as np
import os
import math
import re
import altair as alt

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Cardiokinetics",
    layout="wide"
)

# --- CUSTOM CSS FOR HOSPITAL BLUE THEME (LARGE SIZE) ---
st.markdown("""
<style>
    /* Global Text Styles - Increased Base Size */
    html, body, [class*="css"] {
        font-size: 18px;
        color: #000000;
    }

    /* MAXIMIZE WIDTH: Reduce padding to fit more columns */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 100%;
    }
    
    /* Headers - Hospital Blue Theme & Larger */
    h1 {
        color: #003366; /* Dark Navy Blue */
        font-weight: 800;
        letter-spacing: -0.5px;
        padding-top: 0px;
        font-size: 3.5rem !important; /* Much larger title */
    }
    h2 {
        color: #004080; /* Medium Navy */
        font-weight: 700;
        border-bottom: 3px solid #003366;
        padding-bottom: 10px;
        margin-top: 20px;
        font-size: 2.2rem !important;
    }
    h3 {
        color: #0059b3; /* Bright Blue */
        font-weight: 600;
        font-size: 1.6rem !important;
    }
    
    /* Button Styling - SOLID BLUE BACKGROUND WITH WHITE TEXT */
    /* Added !important to force styling across all sections including tabs */
    div.stButton > button {
        background-color: #003366 !important; /* Solid Dark Blue */
        color: #FFFFFF !important; /* White Text - Forced */
        font-weight: 800;
        height: 65px; /* Taller button */
        font-size: 1.2rem !important; /* Larger text */
        border: 3px solid #003366 !important;
        border-radius: 10px;
        width: 100%;
        transition: all 0.2s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-top: 10px; /* Added spacing above buttons */
    }
    
    div.stButton > button:hover {
        background-color: #004080 !important; /* Slightly lighter blue on hover */
        border-color: #004080 !important;
        color: #FFFFFF !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 8px rgba(0,0,0,0.2);
    }
    
    div.stButton > button:active {
        background-color: #002244 !important; /* Very dark blue on click */
        border-color: #002244 !important;
        transform: translateY(0);
        color: #FFFFFF !important;
    }

    /* --- FIXED INPUT STYLING --- */
    /* Fix for "cut off" search bar: Increase height to match buttons and adjust vertical alignment */
    
    /* Container styling */
    div[data-baseweb="input"] {
        min-height: 65px; /* Match button height */
        border-radius: 10px; /* Match button radius */
        background-color: #003366; /* Dark Blue Background */
        border: 2px solid #003366;
        display: flex;
        align-items: center; /* Center vertically */
    }
    
    /* Select box container styling */
    div[data-baseweb="select"] > div {
        min-height: 65px;
        border-radius: 10px;
        border: 2px solid #003366;
        background-color: #003366; /* Dark Blue Background for Dropdowns too */
        display: flex;
        align-items: center;
    }
    
    /* Inner text input styling */
    div[data-baseweb="input"] input {
        font-size: 1.2rem;
        color: #FFFFFF; /* White text */
        caret-color: #FFFFFF; /* White cursor */
        padding-left: 10px;
        /* Ensure input takes full height to avoid clipping */
        height: 100%; 
        min-height: 60px;
    }
    
    /* Select box inner text - WHITE for readability on dark bg */
    div[data-baseweb="select"] div {
        font-size: 1.2rem;
        color: #FFFFFF; 
    }
    
    /* Force number inputs to have white text if they use the dark background class */
    div[data-baseweb="input"] input[type="number"] {
         color: #FFFFFF;
    }
    
    /* Dropdown SVG icon color (the little arrow) */
    div[data-baseweb="select"] svg {
        fill: #FFFFFF;
    }

    /* Metric Cards Styling - Bigger Content */
    div[data-testid="metric-container"] {
        background-color: #F0F7FF; /* Very light blue background */
        border: 2px solid #0059b3;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        transition: all 0.2s ease;
    }
    div[data-testid="metric-container"]:hover {
        border-color: #003366;
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    div[data-testid="metric-container"] label {
        color: #004080;
        font-weight: 700;
        font-size: 1.2rem !important;
    }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        color: #002244;
        font-size: 2.5rem !important; /* Very large numbers */
    }

    /* Tabs Styling - Now look like buttons! */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px; /* Space out the tabs */
        margin-bottom: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 60px;
        font-size: 1.2rem;
        white-space: pre-wrap;
        background-color: #FFFFFF; /* White background for inactive */
        border: 2px solid #003366; /* Blue border */
        border-radius: 8px;
        color: #003366; /* Blue text */
        font-weight: 700;
        flex-grow: 1; /* Make them fill width */
        text-align: center;
    }
    .stTabs [aria-selected="true"] {
        background-color: #003366; /* Solid Blue for Active */
        color: #FFFFFF; /* White text */
        border: 2px solid #003366;
    }
</style>
""", unsafe_allow_html=True)

# --- DATA LOADING FUNCTION ---


@st.cache_data
def load_data():
    # Helper function to clean and format headers scientifically
    def clean_header(c):
        original = c.strip()

        # 1. Rename AUC explicitly - Case Insensitive Check
        if original.lower() == "auc":
            return "Area Under the Curve (AUC) [ng.hr/mL]"

        # 2. Fix Scientific Units (Title casing destroys units like mL, pH, etc.)
        c_title = original.title()

        # Restore specific unit capitalization
        c_title = c_title.replace("Ng/Ml", "ng/mL")
        c_title = c_title.replace("Ug/Ml", "µg/mL")
        c_title = c_title.replace("Mg/L", "mg/L")
        c_title = c_title.replace("Ng.Hr/Ml", "ng.hr/mL")
        c_title = c_title.replace("Ng*H/Ml", "ng.hr/mL")
        c_title = c_title.replace("Ml/Min", "mL/min")
        c_title = c_title.replace("L/Min", "L/min")
        c_title = c_title.replace("Iv", "IV")

        return c_title

    # Check if the user's Excel file exists
    if os.path.exists("drug_data.xlsx"):
        try:
            # Load the Excel file
            df = pd.read_excel("drug_data.xlsx")

            # Apply the clean_header function to all columns
            df.columns = [clean_header(c) for c in df.columns]

            # Ensure critical columns exist. If not, try to guess or use defaults.
            # We need 'Name' and 'Class' for the logic to work.
            if 'Name' not in df.columns:
                st.error(
                    "Error: Your Excel file must have a column labeled 'Name'.")
                return pd.DataFrame()  # Return empty on error
            if 'Class' not in df.columns:
                # If no class column, add a placeholder
                df['Class'] = "Uncategorized"

            return df
        except Exception as e:
            st.error(f"Error reading Excel file: {e}")
            return pd.DataFrame()
    else:
        # FALLBACK: Use Mock Data if file not found
        st.warning("⚠️ 'drug_data.xlsx' not found. Displaying mock data.")
        # Updated mock data to match the new naming conventions
        INITIAL_DATA = [
            {
                "Name": "Lisinopril",
                "Class": "ACE Inhibitor",
                "Half-Life": "12h",
                "Cmax": "40 ng/mL",
                "Area Under the Curve (AUC) [ng.hr/mL]": "500 ng·h/mL",
                "Bioavailability": "25%",
                "Clearance": "50 mL/min"
            },
            {
                "Name": "Atorvastatin",
                "Class": "Statin",
                "Half-Life": "14h",
                "Cmax": "20 ng/mL",
                "Area Under the Curve (AUC) [ng.hr/mL]": "200 ng·h/mL",
                "Bioavailability": "14%",
                "Clearance": "N/A"
            },
            {
                "Name": "Metoprolol",
                "Class": "Beta Blocker",
                "Half-Life": "3-7h",
                "Cmax": "100 ng/mL",
                "Area Under the Curve (AUC) [ng.hr/mL]": "1200 ng·h/mL",
                "Bioavailability": "50%",
                "Clearance": "1 L/min"
            },
        ]
        return pd.DataFrame(INITIAL_DATA)


# Load the data
df = load_data()

# Helper function to extract numeric values from strings (e.g., "12h" -> 12.0, "61 ± 13.42" -> 61.0)


def extract_numeric(val_str):
    if isinstance(val_str, (int, float)):
        return float(val_str)

    val_str = str(val_str)

    # 1. Handle "±" specifically: Split by it and take the first part
    if '±' in val_str:
        val_str = val_str.split('±')[0]

    # 2. Simple regex to find the first valid number (integer or float) in the remaining string
    # This matches optional +/- sign, digits, optional dot, digits.
    match = re.search(r"[-+]?\d*\.?\d+", val_str)
    if match:
        return float(match.group())

    return None


# --- NAVIGATION & HEADER (Top Layout) ---
if 'current_view' not in st.session_state:
    st.session_state.current_view = "Table View"

# Split screen: Left (Title + Search) vs Right (Buttons)
# We use a ratio of 1:2 to give the controls on the right enough space
top_left, top_right = st.columns([1, 2])

with top_left:
    st.title("Cardiokinetics")
    # Search bar placed below title, size restricted by column width (1/3 of page)
    search_term = st.text_input(
        "Search", placeholder="Search by Drug Name or Class...", label_visibility="collapsed")

with top_right:
    # Spacer to align buttons slightly lower, matching the visual weight of the left side
    st.markdown("<br>", unsafe_allow_html=True)

    # Navigation Buttons - Now 5 Columns to fit "PK Graph"
    # Added gap="medium" to space them out
    nav_btn1, nav_btn2, nav_btn3, nav_btn4, nav_btn5 = st.columns(
        5, gap="medium")

    with nav_btn1:
        if st.button("Table View", use_container_width=True):
            st.session_state.current_view = "Table View"
    with nav_btn2:
        if st.button("Drugs by Class", use_container_width=True):
            st.session_state.current_view = "Drugs by Class"
    with nav_btn3:
        if st.button("Individual View", use_container_width=True):
            st.session_state.current_view = "Individual Drug View"
    with nav_btn4:
        if st.button("PK Calculator", use_container_width=True):
            st.session_state.current_view = "PK Calculator"
    with nav_btn5:
        # NEW BUTTON FOR GRAPH
        if st.button("PK Graph", use_container_width=True):
            st.session_state.current_view = "PK Graph"

st.markdown("---")

view_option = st.session_state.current_view

# --- VIEW 1: TABLE VIEW ---
if view_option == "Table View":

    if not df.empty:
        # Use the global search_term defined in the top layout
        if search_term:
            filtered_df = df[
                df['Name'].astype(str).str.contains(search_term, case=False) |
                df['Class'].astype(str).str.contains(search_term, case=False)
            ]
        else:
            filtered_df = df

        st.write(f"Showing {len(filtered_df)} records")
        # Added height=800 to make the table significantly taller
        st.dataframe(filtered_df, use_container_width=True,
                     hide_index=True, height=800)
    else:
        st.info("No data available to display in table.")

# --- VIEW 2: DRUGS BY CLASS ---
elif view_option == "Drugs by Class":
    st.header("Therapeutic Class Overview")

    if not df.empty:
        drug_classes = df['Class'].unique()

        for drug_class in drug_classes:
            class_subset = df[df['Class'] == drug_class]
            count = len(class_subset)

            with st.expander(f"**{drug_class}** ({count} Drugs)"):
                # Show all columns except Class (since we are already in that group)
                display_cols = [
                    c for c in class_subset.columns if c != 'Class']
                st.dataframe(class_subset[display_cols],
                             hide_index=True, use_container_width=True)
    else:
        st.info("No data available to display classes.")

# --- VIEW 3: INDIVIDUAL VIEW ---
elif view_option == "Individual Drug View":
    st.header("Individual Pharmacokinetic Profile")

    if not df.empty:
        # Optional: Filter the dropdown list if a search term is present
        # This makes the global search bar useful in this view as well
        if search_term:
            filtered_names = df[df['Name'].astype(str).str.contains(
                search_term, case=False)]['Name'].unique()
            if len(filtered_names) == 0:
                st.warning(f"No drugs found matching '{search_term}'")
                filtered_names = df['Name'].unique()
        else:
            filtered_names = df['Name'].unique()

        selected_drug_name = st.selectbox("Select a Drug:", filtered_names)

        if selected_drug_name:
            # Get the row for the selected drug
            drug = df[df['Name'] == selected_drug_name].iloc[0]

            # Header
            st.info(f"**Therapeutic Class:** {drug['Class']}")

            st.subheader("Pharmacokinetic Parameters")

            # DYNAMIC METRIC GRID
            # This will automatically create a card for every column in your Excel file
            # excluding Name and Class.
            params = [col for col in df.columns if col not in [
                'Name', 'Class', 'id', 'ID']]

            # Create a grid of 3 columns
            cols = st.columns(3)

            for i, param in enumerate(params):
                val = drug[param]
                # Use the column index to place metrics in the grid (0, 1, 2, 0, 1, 2...)
                with cols[i % 3]:
                    st.metric(label=param, value=str(val))

    else:
        st.info("No data available to display individual profiles.")

# --- VIEW 4: PK CALCULATOR ---
elif view_option == "PK Calculator":
    st.header("Pharmacokinetic Calculator")
    st.markdown(
        "Estimate missing parameters using standard one-compartment models.")

    # Create tabs for different calculators
    tab1, tab2, tab3, tab4 = st.tabs(
        ["Bioavailability (F)", "Cmin (Trough)", "Clearance (CL)", "Half-Life / ke"])

    # --- CALCULATOR 1: BIOAVAILABILITY ---
    with tab1:
        st.subheader("Calculate Bioavailability (F)")

        # Display Equation
        st.latex(
            r"F = \frac{AUC_{oral} \cdot Dose_{IV}}{AUC_{IV} \cdot Dose_{oral}}")
        st.write("Determine absolute bioavailability by comparing Oral vs. IV data.")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Oral Administration**")
            auc_oral = st.number_input(
                "AUC (Oral)", min_value=0.0, value=0.0, step=0.1, help="Area Under the Curve for Oral Dose")
            dose_oral = st.number_input(
                "Dose (Oral)", min_value=0.0, value=0.0, step=1.0)

        with col2:
            st.markdown("**IV Administration**")
            auc_iv = st.number_input(
                "AUC (IV)", min_value=0.0, value=0.0, step=0.1)
            dose_iv = st.number_input(
                "Dose (IV)", min_value=0.0, value=0.0, step=1.0)

        st.markdown("<br>", unsafe_allow_html=True)  # Extra spacing
        if st.button("Calculate F", use_container_width=True):
            if dose_oral > 0 and auc_iv > 0 and dose_iv > 0:
                # F = (AUC_oral * Dose_iv) / (AUC_iv * Dose_oral)
                f_absolute = (auc_oral * dose_iv) / (auc_iv * dose_oral)
                f_percent = f_absolute * 100
                st.success(
                    f"**Bioavailability (F):** {f_absolute:.4f} ({f_percent:.2f}%)")
            else:
                st.error("Please enter non-zero values for Doses and IV AUC.")

    # --- CALCULATOR 2: CMIN (TROUGH) ---
    with tab2:
        st.subheader("Estimate Cmin (Trough Concentration)")

        # Display Equation
        st.latex(
            r"C_{min} = C_{max} \cdot e^{-k_e \cdot t} \quad \text{where} \quad k_e = \frac{0.693}{t_{1/2}}")
        st.write(
            "Calculate the expected concentration at the end of a dosing interval based on the peak.")

        cmax = st.number_input("Cmax (Peak Concentration)",
                               min_value=0.0, value=100.0)
        t_half = st.number_input(
            "Half-Life (t½ in hours)", min_value=0.1, value=12.0)
        interval = st.number_input(
            "Time since peak / Dosing Interval (hours)", min_value=0.0, value=24.0)

        st.markdown("<br>", unsafe_allow_html=True)  # Extra spacing
        if st.button("Calculate Cmin", use_container_width=True):
            if t_half > 0:
                # Calculate elimination rate constant (k)
                k = 0.693 / t_half
                # Calculate Cmin = Cmax * e^(-k * t)
                cmin = cmax * math.exp(-k * interval)

                st.info(f"Elimination Rate Constant (k): {k:.4f} /h")
                st.success(f"**Estimated Trough (Cmin):** {cmin:.2f}")
            else:
                st.error("Half-life must be greater than 0.")

    # --- CALCULATOR 3: CLEARANCE ---
    with tab3:
        st.subheader("Calculate Clearance (CL)")

        # Display Equation
        st.latex(r"CL = \frac{F \cdot Dose}{AUC}")
        st.write("Calculate Total Clearance from Bioavailability, Dose, and AUC.")

        cl_dose = st.number_input(
            "Dose (mg)", min_value=0.0, value=500.0, key="cl_dose")
        cl_f = st.number_input("Bioavailability (F) [0 to 1]", min_value=0.0,
                               max_value=1.0, value=1.0, step=0.05, help="Use 1.0 for IV administration")
        cl_auc = st.number_input(
            "AUC (mg·h/L)", min_value=0.0, value=100.0, key="cl_auc")

        st.markdown("<br>", unsafe_allow_html=True)  # Extra spacing
        if st.button("Calculate CL", use_container_width=True):
            if cl_auc > 0:
                # CL = (F * Dose) / AUC
                clearance = (cl_f * cl_dose) / cl_auc
                st.success(f"**Clearance (CL):** {clearance:.2f} L/h")
            else:
                st.error("AUC must be greater than 0.")

    # --- CALCULATOR 4: HALF-LIFE / KE ---
    with tab4:
        st.subheader("Half-Life ↔ Elimination Constant Converter")

        # Display Equation
        st.latex(r"t_{1/2} = \frac{\ln(2)}{k_e} \approx \frac{0.693}{k_e}")

        calc_mode = st.radio("I want to calculate:", [
                             "Half-Life (t½)", "Elimination Constant (k)"])

        if calc_mode == "Half-Life (t½)":
            k_input = st.number_input(
                "Enter Elimination Constant (k) [1/h]", min_value=0.0001, value=0.1, format="%.4f")
            st.markdown("<br>", unsafe_allow_html=True)  # Extra spacing
            if st.button("Convert to t½", use_container_width=True):
                t_half_calc = 0.693 / k_input
                st.success(f"**Half-Life:** {t_half_calc:.2f} hours")

        else:
            t_input = st.number_input(
                "Enter Half-Life (t½) [hours]", min_value=0.1, value=12.0)
            st.markdown("<br>", unsafe_allow_html=True)  # Extra spacing
            if st.button("Convert to k", use_container_width=True):
                k_calc = 0.693 / t_input
                st.success(f"**Elimination Constant (k):** {k_calc:.4f} /h")

# --- VIEW 5: PK GRAPH ---
elif view_option == "PK Graph":
    st.header("Concentration-Time Graph")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Select Drug")

        # Create a dictionary to map custom labels (Name + Dose) to dataframe indices
        drug_choices = {}

        # Identify if there is a specific dose column
        dose_cols = [c for c in df.columns if any(
            k in c.lower() for k in ['dose', 'strength', 'mg'])]
        primary_dose_col = dose_cols[0] if dose_cols else None

        for index, row in df.iterrows():
            label = str(row['Name'])

            # Append dose if available
            if primary_dose_col and pd.notna(row[primary_dose_col]):
                label = f"{label} - {row[primary_dose_col]}"

            # Handle potential duplicates by appending count
            original_label = label
            count = 1
            while label in drug_choices:
                count += 1
                label = f"{original_label} ({count})"

            # Apply search filter if active
            if search_term:
                s_term = search_term.lower()
                # Check Name, Class, or the constructed Label
                if (s_term in str(row['Name']).lower() or
                    s_term in str(row['Class']).lower() or
                        s_term in label.lower()):
                    drug_choices[label] = index
            else:
                drug_choices[label] = index

        if not drug_choices:
            st.warning("No drugs found matching criteria.")
            selected_graph_drug_label = None
        else:
            selected_graph_drug_label = st.selectbox(
                "Choose a Drug to Plot:", list(drug_choices.keys()))

        # ADDED: Plotting Mode Selection
        st.markdown("---")
        plot_source = st.radio("Source for Peak Concentration ($C_{max}$):",
                               ["Use Reported $C_{max}$", "Calculate from AUC ($C_0 = AUC \cdot k$)"])

        g_time = st.slider("Time Duration to Plot (hours)", 6, 72, 24)

    with col2:
        st.subheader("Elimination Curve")

        if selected_graph_drug_label:
            # Retrieve the correct row using the index map
            idx = drug_choices[selected_graph_drug_label]
            drug_row = df.loc[idx]

            # Extract numerical values from strings (e.g. "12h" -> 12.0)
            # Try finding a column that looks like "Cmax"
            cmax_col = [c for c in df.columns if "cmax" in c.lower()][0] if [
                c for c in df.columns if "cmax" in c.lower()] else "Cmax"
            half_life_col = [c for c in df.columns if "half" in c.lower(
            )][0] if [c for c in df.columns if "half" in c.lower()] else "Half-Life"
            # Try finding AUC column
            auc_col = [c for c in df.columns if "auc" in c.lower()][0] if [
                c for c in df.columns if "auc" in c.lower()] else "Area Under the Curve (AUC) [ng.hr/mL]"

            val_cmax = extract_numeric(drug_row.get(cmax_col, None))
            val_thalf = extract_numeric(drug_row.get(half_life_col, None))
            val_auc = extract_numeric(drug_row.get(auc_col, None))

            if val_thalf and val_thalf > 0:
                # Calculate k
                k = 0.693 / val_thalf

                # Determine Cmax based on user selection
                used_cmax = val_cmax
                cmax_origin_text = "Reported"

                if "Calculate from AUC" in plot_source:
                    if val_auc:
                        used_cmax = val_auc * k
                        cmax_origin_text = "Calculated from AUC"
                    else:
                        st.warning(
                            "⚠️ No valid AUC found for this drug. Using Reported Cmax instead.")
                        # Fallback to reported

                if used_cmax and used_cmax > 0:
                    # Generate data points
                    time_points = np.linspace(0, g_time, num=100)
                    concentrations = used_cmax * np.exp(-k * time_points)

                    # Create DataFrame for chart
                    chart_data = pd.DataFrame({
                        "Time (hours)": time_points,
                        "Concentration (ng/mL)": concentrations
                    })

                    # Plot using Altair with Dark Blue theme
                    chart = alt.Chart(chart_data).mark_line(color="#FFFFFF", strokeWidth=3).encode(
                        x='Time (hours)',
                        y='Concentration (ng/mL)',
                        tooltip=['Time (hours)', 'Concentration (ng/mL)']
                    ).properties(
                        background='#003366',  # Dark Blue background
                        height=400
                    ).configure_axis(
                        labelColor='#FFFFFF',
                        titleColor='#FFFFFF',
                        gridColor='#406080',  # Lighter blue grid for contrast
                        labelFontSize=12,
                        titleFontSize=14,
                        grid=True
                    ).configure_view(
                        stroke=None
                    )

                    st.altair_chart(chart, use_container_width=True)

                    # Dynamic parameters display under graph
                    st.markdown(
                        f"**Plotting Parameters:** Cmax ({cmax_origin_text}) = {used_cmax:.2f}, Half-Life = {val_thalf}h")
                else:
                    st.error(
                        "Invalid or missing Cmax value (Reported or Calculated). Cannot plot.")
            else:
                st.error(
                    "Could not extract valid numerical Half-Life for this drug to plot.")
