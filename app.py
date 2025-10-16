import streamlit as st
import pandas as pd
import io

# --- Page Configuration with Dark Theme ---
st.set_page_config(
    page_title="GRN Comparison Tool",
    layout="wide"
)

st.title("📊 GRN Comparison Tool")
st.write("Upload your old and new reports to perform comparisons.")

# --- File Uploaders ---
uploaded_old_file = st.file_uploader("1. Upload the OLD Excel Report (File A)", type="xlsx")
uploaded_new_file = st.file_uploader("2. Upload the NEW Excel Report (File B)", type="xlsx")

# --- Main Logic ---
if uploaded_old_file and uploaded_new_file:
    try:
        df_old = pd.read_excel(uploaded_old_file, header=5)
        df_new = pd.read_excel(uploaded_new_file, header=5)

        KEY_COLUMN = 'Invoice No'
        AMOUNT_COLUMN = 'total'
        
        df_old[KEY_COLUMN] = df_old[KEY_COLUMN].astype(str).str.strip()
        df_new[KEY_COLUMN] = df_new[KEY_COLUMN].astype(str).str.strip()

        st.success("Files loaded successfully! Choose an action below.")
        st.divider()

        # --- FEATURE 1: Get ONLY New GRNs ---
        st.subheader("1. Get a Report of ONLY New GRNs")
        if st.button("Generate New GRN Report"):
            # ... (logic is the same)
            old_grns = set(df_old[KEY_COLUMN].dropna())
            new_grns = set(df_new[KEY_COLUMN].dropna())
            added_grns = list(new_grns - old_grns)
            st.write(f"Found **{len(added_grns)}** new GRNs.")
            if added_grns:
                new_grn_report_df = df_new[df_new[KEY_COLUMN].isin(added_grns)]
                st.dataframe(new_grn_report_df)
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    new_grn_report_df.to_excel(writer, index=False, sheet_name='New_GRNs')
                excel_data = output.getvalue()
                st.download_button(
                    label="📥 Download New GRN Report",
                    data=excel_data,
                    file_name="New_GRN_Report.xlsx"
                )
            else:
                st.info("No new GRNs found.")

        st.divider()

        # --- FEATURE 2: Get Full Report with Status Column ---
        st.subheader("2. Get the Full New Report with an 'Old'/'New' Status Column")
        if st.button("Generate Full Report with Status"):
            # ... (logic is the same)
            old_grns_set = set(df_old[KEY_COLUMN].dropna())
            report_with_status = df_new.copy()
            report_with_status['GRN Status'] = report_with_status[KEY_COLUMN].apply(
                lambda grn: "Old" if grn in old_grns_set else "New"
            )
            st.write("Generated the full report with status:")
            st.dataframe(report_with_status)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                report_with_status.to_excel(writer, index=False, sheet_name='Report_With_Status')
            excel_data = output.getvalue()
            st.download_button(
                label="📥 Download Full Report with Status",
                data=excel_data,
                file_name="Full_Report_with_Status.xlsx"
            )

        st.divider()

        # --- FEATURE 3: Find Amount Differences for Existing GRNs ---
        st.subheader("3. Find Amount Differences for Common GRNs")
        if st.button("Generate Amount Difference Report"):
            # ... (logic is the same)
            old_subset = df_old[[KEY_COLUMN, AMOUNT_COLUMN]].copy()
            new_subset = df_new[[KEY_COLUMN, AMOUNT_COLUMN]].copy()
            old_subset[AMOUNT_COLUMN] = pd.to_numeric(old_subset[AMOUNT_COLUMN], errors='coerce')
            new_subset[AMOUNT_COLUMN] = pd.to_numeric(new_subset[AMOUNT_COLUMN], errors='coerce')
            
            comparison_df = pd.merge(
                old_subset, new_subset, on=KEY_COLUMN, how='inner', suffixes=('_old', '_new')
            )
            comparison_df['Difference'] = comparison_df[f'{AMOUNT_COLUMN}_new'] - comparison_df[f'{AMOUNT_COLUMN}_old']
            amended_grns = comparison_df[comparison_df['Difference'] != 0].copy()

            st.write(f"Found **{len(amended_grns)}** GRNs with changed amounts.")
            
            if not amended_grns.empty:
                amended_grns.rename(columns={
                    KEY_COLUMN: 'GRN',
                    f'{AMOUNT_COLUMN}_old': 'Old Amount',
                    f'{AMOUNT_COLUMN}_new': 'New Amount'
                }, inplace=True)
                
                st.dataframe(amended_grns[['GRN', 'Old Amount', 'New Amount', 'Difference']])

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    amended_grns[['GRN', 'Old Amount', 'New Amount', 'Difference']].to_excel(writer, index=False, sheet_name='Amount_Differences')
                excel_data = output.getvalue()
                st.download_button(
                    label="📥 Download Amount Difference Report",
                    data=excel_data,
                    file_name="Amount_Difference_Report.xlsx"
                )
            else:
                st.info("No amount differences found for any common GRNs.")

    except KeyError as e:
        st.error(f"Error: A required column was not found: {e}. Please check your Excel files.")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")