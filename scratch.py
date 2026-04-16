import re

# Read newapp (1).py
with open('d:\\t20_DEA\\newapp (1).py', 'r', encoding='utf-8') as f:
    newapp_content = f.read()

# Find the start of the missing sections
start_str = 'st.header("The Two-Bouncer Rule: Death Overs Survival")'
blocks = newapp_content.split(start_str)

if len(blocks) > 1:
    missing_sections = start_str + blocks[1]
    # Replace variables appropriately
    missing_sections = missing_sections.replace('new_ipl', 'new_t20_data')
    missing_sections = missing_sections.replace('ipl', 't20_data')
    
    # Read t20_eda_dashboard.py
    with open('d:\\t20_DEA\\t20_eda_dashboard.py', 'r', encoding='utf-8') as f:
        t20_content = f.read()
    
    # Append the missing sections to the end of t20_eda_dashboard.py
    if start_str not in t20_content:
        t20_content += '\n\n    ' + missing_sections.lstrip()

    # Also insert the global UI upgrade after st.set_page_config
    if "GLOBAL UI UPGRADE" not in t20_content:
        ui_str = '''
# --- GLOBAL UI UPGRADE: PREMIUM DARK SCIFI THEME ---
st.markdown("""
    <style>
    /* Main App Background */
    .stApp {
        background-color: #0B0E14;
        color: #E2E8F0;
        font-family: 'Inter', sans-serif;
    }

    /* Hide Streamlit Default Menu and Footer for a clean SaaS look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Glassmorphism Effect for Standard Streamlit Metrics */
    div[data-testid="metric-container"] {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.7));
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
        transition: transform 0.2s ease;
    }

    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        border: 1px solid rgba(0, 210, 255, 0.3);
    }

    /* Style the Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0F172A;
        border-right: 1px solid #1E293B;
    }

    /* Clean Divider Lines */
    hr {
        border-color: #1E293B !important;
    }
    </style>
""", unsafe_allow_html=True)
'''
        # Let's find the position to insert
        lines = t20_content.split('\n')
        insert_idx = -1
        for i, line in enumerate(lines):
            if "st.set_page_config" in line:
                insert_idx = i + 1
                break
        if insert_idx != -1:
            lines.insert(insert_idx, ui_str)
            t20_content = '\n'.join(lines)
            
    with open('d:\\t20_DEA\\t20_eda_dashboard.py', 'w', encoding='utf-8') as f:
        f.write(t20_content)
        print("Updated successfully.")
else:
    print("Could not find missing sections.")
