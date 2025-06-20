import streamlit as st
import requests
import re
import time
import json


st.sidebar.title("🔐 API Configuration")
api_key = st.sidebar.text_input("Enter your API Key", type="password")

st.title("📊 DashAnalytix Agentic Analysis (via API)")

months = st.slider("Select how many months of data to analyze:", min_value=1, max_value=36, value=18)

# Dynamically calculate years and remaining months
years = months // 12
remaining_months = months % 12

if years > 0:
    st.info(f"🕒 Selected Duration: {months} months ({years} year{'s' if years > 1 else ''} and {remaining_months} month{'s' if remaining_months != 1 else ''})")
else:
    st.info(f"🕒 Selected Duration: {months} month{'s' if months != 1 else ''}")


# Read JSON files from disk (assuming files are in same folder or provide full path)
def load_json_file(filename):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error reading {filename}: {e}")
        return None



add_data_g1= load_json_file("add_data_g1.json")
add_data_g2= load_json_file("add_data_g2.json")
kpi_data_g1= load_json_file("kpi_data_g1.json")
kpi_data_g2= load_json_file("kpi_data_g2.json")


if add_data_g1 is not None and add_data_g2 is not None and kpi_data_g1 is not None and kpi_data_g2 is not None:
    # st.json(additional_data)
    st.info("📥 Data successfully fetched from Files")



if st.button("Run Agent Analysis"):
    with st.spinner("🔍 Analyzing KPIs"):
        try:
            payload = { "months": months , "api_key": api_key  }  
            response = requests.post("https://insightgeneration-production.up.railway.app/analyze", json={
                    "add_data_g1": add_data_g1,
                    "add_data_g2": add_data_g2,
                    "kpi_data_g1": kpi_data_g1,
                    "kpi_data_g2": kpi_data_g2,
                    "months": months,
                    "api_key": api_key,

                })            
            if response.status_code == 200:
                result = response.json()
                st.write(result)  # debug output

                agents_result = result.get("agents_result", [])
                duration = result.get("duration_seconds", 0)

                st.success(f"✅ Agents completed in {round(duration, 2)} Seconds")
                st.markdown("## 📊 Generated Insights")

                # Display all agent insights plainly without numbering
                for agent_text in agents_result:
                    if agent_text.strip():
                        st.markdown(agent_text.strip())

            else:
                st.error(f"❌ Server error: {response.text}")

        except Exception as e:
            st.error(f"❌ Request failed: {str(e)}")
