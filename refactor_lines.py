import codecs

file_path = "t20_eda_dashboard.py"

with codecs.open(file_path, "r", "utf-8") as f:
    lines = f.readlines()

# BOTTOM-UP MODIFICATION TO KEEP LINE INDEXES STABLE

# --- TARGET 3: Remove Donut Chart and keep Area chart full width (Lines 563 to 597) ---
donut_start = 563
donut_end = 598  # line 598 is st.divider()
if "st.header(\"⚖️ The Toss Advantage Reality Check\")" in lines[566]:
    new_toss = [
        '    # ==========================================\n',
        '    # UPGRADE: CAPTAINS CHOICES\n',
        '    # ==========================================\n',
        '    st.header("⚖️ Captains\' Choices Over Time")\n',
        '    st.markdown("Has the global T20 meta shifted from batting first to chasing over the last 15 years?")\n',
        '    choice_trends = matches.groupby([\'season_id\', \'toss_decision\']).size().reset_index(name=\'count\')\n',
        '    fig_area = px.area(\n',
        '        choice_trends, x=\'season_id\', y=\'count\', color=\'toss_decision\',\n',
        '        color_discrete_map={\'field\': \'#3b82f6\', \'bat\': \'#f59e0b\'},\n',
        '        labels={\'season_id\': \'Season\', \'count\': \'Number of Tosses\'},\n',
        '    )\n',
        '    fig_area.update_layout(xaxis_type=\'category\', height=400)\n',
        '    st.plotly_chart(fig_area, use_container_width=True)\n\n'
    ]
    # Replace lines [563:598]
    lines = lines[:donut_start] + new_toss + lines[donut_end:]
    print("Donut removed!")

# --- TARGET 2: Insert Venue Analytics Page (Before line 527) ---
insert_idx = 527
if 'elif menu == "Team & Toss Analysis":' in lines[insert_idx]:
    # Extract Venue Code (Lines 376:485 block)
    venue_block = lines[377:485]
    
    venue_page = [
        '# ==========================================\n',
        '# PAGE 2: VENUE ANALYTICS\n',
        '# ==========================================\n',
        'elif menu == "Venue Analytics":\n',
        '    st.title("🏟️ Venue Analytics")\n',
        '    st.markdown("Explore stadium fortresses and pitch DNA classification.")\n\n'
    ]
    venue_page.extend(venue_block)
    venue_page.append('\n')
    
    lines = lines[:insert_idx] + venue_page + lines[insert_idx:]
    print("Venue Page Created!")

# --- TARGET 1: Delete Original Venue Code (Lines 377:485) ---
if 'st.subheader("Venue Fortresses")' in lines[377]:
    # Delete from 377 to 485
    lines = lines[:377] + lines[485:]
    print("Original Venue Code deleted!")

with codecs.open(file_path, "w", "utf-8") as f:
    f.writelines(lines)
    
print("Success")
