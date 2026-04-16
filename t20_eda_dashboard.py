import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# 1. PAGE CONFIG
st.set_page_config(page_title="T20 Data Dashboard", page_icon="🏏", layout="wide")

# --- GLOBAL UI UPGRADE: PREMIUM CLEAN DARK THEME ---
st.markdown("""
    <style>
    /* Main App Background */
    .stApp {
        background-color: #09090B;
        color: #FAFAFA;
        font-family: 'Inter', -apple-system, sans-serif;
    }

    /* Hide Streamlit Default Menu and Footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Keyframe Animations */
    @keyframes fadeInSlide {
        0% { opacity: 0; transform: translateY(20px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes marqueeMove {
        0% { transform: translateX(50%); }
        100% { transform: translateX(-100%); }
    }

    /* Animated Header */
    .animated-header {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(-45deg, #E2E8F0, #3B82F6, #06B6D4, #E2E8F0);
        background-size: 300% 300%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradientShift 6s ease infinite, fadeInSlide 1s ease-out;
        text-align: center;
        margin-bottom: 20px;
    }

    /* Insights Ticker Marquee */
    .ticker-wrapper {
        width: 100%;
        overflow: hidden;
        background: #18181B;
        padding: 12px 0;
        border-radius: 8px;
        border: 1px solid #27272A;
        margin-bottom: 40px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        display: flex;
        white-space: nowrap;
    }
    .ticker-content {
        display: flex;
        width: max-content;
        animation: marqueeMove 30s linear infinite;
    }
    /* Stop animation on hover so users can read */
    .ticker-wrapper:hover .ticker-content {
        animation-play-state: paused;
    }
    .ticker-item {
        margin-right: 60px;
        font-weight: 500;
        color: #A1A1AA;
        font-size: 1.1rem;
    }
    .ticker-highlight {
        color: #38BDF8;
        font-weight: 700;
    }

    @keyframes marqueeMove {
        0% { transform: translateX(0%); }
        100% { transform: translateX(-50%); }
    }

    /* Premium Clean Custom Cards */
    .premium-card {
        background: #18181B;
        border: 1px solid #27272A;
        padding: 25px;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        text-align: center;
        transition: all 0.3s ease;
        animation: fadeInSlide 0.8s ease-out backwards;
    }
    .premium-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 12px 24px -8px rgba(56, 189, 248, 0.4);
        border-color: #38BDF8;
    }
    .card-title {
        color: #A1A1AA;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 15px;
        font-weight: 600;
    }
    .card-value {
        color: #FAFAFA;
        font-size: 2.5rem;
        font-weight: 800;
    }

    /* Style the Sidebar */
    [data-testid="stSidebar"] {
        background-color: #09090B;
        border-right: 1px solid #27272A;
    }
    
    /* Clean Divider Lines */
    hr {
        border-color: #27272A !important;
    }
    </style>
""", unsafe_allow_html=True)



# 2. CACHE DATA LOADING
@st.cache_data
def load_data():
    t20_data = pd.read_csv('t20_ball_by_ball.csv.gz', compression='gzip', low_memory=False)
    matches = pd.read_csv('t20_matches.csv')

    # --- FIX MISSING/UNKNOWN CITIES VIA VENUE MAPPING ---
    unknown_mask = matches['city'] == 'Unknown'
    city_mapping = {
        'Pallekele International Cricket Stadium': 'Kandy',
        'Galle International Stadium': 'Galle',
        'Arundel Castle Cricket Club Ground': 'Arundel',
        'Dubai International Cricket Stadium': 'Dubai',
        'Guanggong International Cricket Stadium': 'Guangzhou',
        'Sylhet Stadium': 'Sylhet',
        'Melbourne Cricket Ground': 'Melbourne',
        'Adelaide Oval': 'Adelaide',
        'Harare Sports Club': 'Harare',
        'Sydney Cricket Ground': 'Sydney',
        'Sharjah Cricket Stadium': 'Sharjah',
        'Sylhet International Cricket Stadium': 'Sylhet',
        'Carrara Oval': 'Gold Coast',
        'Colombo Cricket Club Ground': 'Colombo',
        'Rawalpindi Cricket Stadium': 'Rawalpindi'
    }
    matches.loc[unknown_mask, 'city'] = matches.loc[unknown_mask, 'venue'].map(city_mapping).fillna('Unknown')

    # --- KEEP ONLY T20 WORLD CUP MATCHES ---
    matches['match_date'] = pd.to_datetime(matches['match_date'])
    matches['temp_year'] = matches['match_date'].dt.year
    matches['temp_month'] = matches['match_date'].dt.month

    # T20 World Cup Date Windows (Year: [Months])
    wc_windows = {
        2007: [9],            # September
        2009: [6],            # June
        2010: [4, 5],         # April-May
        2012: [9, 10],        # September-October
        2014: [3, 4],         # March-April
        2016: [3, 4],         # March-April
        2021: [10, 11],       # October-November
        2022: [10, 11],       # October-November
        2024: [6],            # June
        2026: [2, 3]          # February-March
    }

    is_wc = [
        (y in wc_windows and m in wc_windows[y])
        for y, m in zip(matches['temp_year'], matches['temp_month'])
    ]
    
    matches = matches[is_wc].copy()
    
    # --- SECONDARY FILTER: REMOVE REGIONAL QUALIFIERS ---
    # Only keep matches where both teams are established World Cup participant nations
    wc_teams = [
        "India", "Pakistan", "Australia", "England", "South Africa", 
        "New Zealand", "West Indies", "Sri Lanka", "Bangladesh", 
        "Afghanistan", "Zimbabwe", "Ireland", "Scotland", "Netherlands",
        "Namibia", "United Arab Emirates", "Oman", "Nepal", "Hong Kong",
        "Papua New Guinea", "Uganda", "United States of America", "Canada", "Kenya"
    ]
    matches = matches[matches['team1'].isin(wc_teams) & matches['team2'].isin(wc_teams)].copy()
    
    t20_data = t20_data[t20_data['match_id'].isin(matches['match_id'])].copy()
    
    matches = matches.drop(columns=['temp_year', 'temp_month'])
    # ---------------------------------------

    # Pre-calculate match phases
    def get_phase(over):
        if over < 6:
            return 'Powerplay (1-6)'
        elif over < 15:
            return 'Middle Overs (7-15)'
        else:
            return 'Death Overs (16-20)'

    t20_data['phase'] = t20_data['over_number'].apply(get_phase)

    # Pre-calculate Modern Era Data (2023-2025) for global use
    target_seasons = [2023, 2024, 2025]
    new_t20_data = t20_data[t20_data['season_id'].isin(target_seasons)].copy()
    new_matches = matches[matches['season_id'].isin(target_seasons)].copy()

    return t20_data, matches, new_t20_data, new_matches


t20_data, matches, new_t20_data, new_matches = load_data()

# 3. SIDEBAR NAVIGATION SETUP
st.sidebar.title("🏏 T20 Dashboard")
st.sidebar.markdown("Navigate through the analytics:")
menu = st.sidebar.radio(
    "Select a Page:",
    [
        "Tournament Overview",
        "Venue Analytics",
        "Team & Toss Analysis",
        "Player Leaderboards",
        "Head-to-Head Comparisons",
        "In-Depth Match Analytics",
        "Modern Meta Analytics"
    ]
)

# ==========================================
# PAGE 1: TOURNAMENT OVERVIEW
# ==========================================
if menu == "Tournament Overview":
    # --- 1. ANIMATED HERO HEADER & TICKER ---
    st.markdown('<div class="animated-header">ICC T20 World Cup Analytics</div>', unsafe_allow_html=True)
    
    # Calculate Dynamic Insights
    match_scores = t20_data.groupby(['match_id', 'team_batting'])['total_runs'].sum().reset_index()
    highest_score = match_scores['total_runs'].max()
    highest_team = match_scores.loc[match_scores['total_runs'].idxmax()]['team_batting']
    total_sixes = t20_data[t20_data['batter_runs'] == 6].shape[0]
    
    st.markdown(f"""
    <div class="ticker-wrapper">
        <div class="ticker-content">
            <!-- FIRST SET -->
            <span class="ticker-item">🏆 <span class="ticker-highlight">Total World Cups:</span> {matches['season_id'].nunique()}</span>
            <span class="ticker-item">🔥 <span class="ticker-highlight">Highest Match Score:</span> {highest_score} by {highest_team}</span>
            <span class="ticker-item">🚀 <span class="ticker-highlight">Total Tournament Sixes:</span> {total_sixes:,}</span>
            <span class="ticker-item">🏏 <span class="ticker-highlight">Total Wickets Fallen:</span> {t20_data['is_wicket'].sum():,}</span>
            <!-- SECOND SET (MIRRORED FOR INFINITE LOOP) -->
            <span class="ticker-item">🏆 <span class="ticker-highlight">Total World Cups:</span> {matches['season_id'].nunique()}</span>
            <span class="ticker-item">🔥 <span class="ticker-highlight">Highest Match Score:</span> {highest_score} by {highest_team}</span>
            <span class="ticker-item">🚀 <span class="ticker-highlight">Total Tournament Sixes:</span> {total_sixes:,}</span>
            <span class="ticker-item">🏏 <span class="ticker-highlight">Total Wickets Fallen:</span> {t20_data['is_wicket'].sum():,}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 2. PREMIUM METRIC CARDS ---
    total_seasons = matches['season_id'].nunique()
    total_matches = matches['match_id'].size
    total_runs = t20_data['total_runs'].sum()
    total_wickets = t20_data['is_wicket'].sum()
    
    m1, m2, m3, m4 = st.columns(4)
    
    m1.markdown(f"""
    <div class="premium-card">
        <div class="card-title">World Cups Held</div>
        <div class="card-value">{total_seasons}</div>
    </div>
    """, unsafe_allow_html=True)
    
    m2.markdown(f"""
    <div class="premium-card" style="animation-delay: 0.1s;">
        <div class="card-title">Matches Played</div>
        <div class="card-value">{total_matches}</div>
    </div>
    """, unsafe_allow_html=True)
    
    m3.markdown(f"""
    <div class="premium-card" style="animation-delay: 0.2s;">
        <div class="card-title">Total Runs Scored</div>
        <div class="card-value">{total_runs:,}</div>
    </div>
    """, unsafe_allow_html=True)
    
    m4.markdown(f"""
    <div class="premium-card" style="animation-delay: 0.3s;">
        <div class="card-title">Wickets Taken</div>
        <div class="card-value">{total_wickets:,}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br><hr><br>", unsafe_allow_html=True)
    
    # --- 3. TWO-COLUMN CHART LAYOUT ---
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.subheader("Matches per Tournament")
        no_of_matches = matches.groupby('season_id')['match_id'].count().reset_index()
        fig1 = px.line(no_of_matches, x='season_id', y='match_id', labels={'season_id': 'Season', 'match_id': 'Matches'},
                       markers=True)
        # Force the x-axis to be categorical so it looks aligned
        fig1.update_layout(xaxis_type='category')
        st.plotly_chart(fig1, use_container_width=True)
        
    with chart_col2:
        st.subheader("Tie / Super Over Frequency")
        a1 = matches[matches['result'] == 'tie'].groupby('season_id')['result'].size().reset_index()
        # Create zeros for all known seasons dynamically so we don't hardcode
        all_seasons = matches['season_id'].unique()
        zero_df = pd.DataFrame({'season_id': all_seasons, 'result': np.zeros(len(all_seasons))})
        a2 = pd.concat([a1, zero_df]).groupby('season_id')['result'].sum().reset_index()
        
        fig2 = px.line(a2, x='season_id', y='result', markers=True,
                       labels={'season_id': 'Season', 'result': 'Super Overs'})
        fig2.update_layout(xaxis_type='category')
        st.plotly_chart(fig2, use_container_width=True)
        
    st.divider()

    st.subheader("Month-wise Match Distribution")
    
    # 1. Add filter options
    time_filter = st.radio(
        "Select Time Range:",
        ["Last 5 Years", "Last 10 Years", "All Time"],
        horizontal=True,
        key="month_dist_filter"
    )

    matches['match_date'] = pd.to_datetime(matches['match_date'])
    matches['month_name'] = matches['match_date'].dt.month_name()
    
    # 2. Filter logic based on the max season_id
    max_season = matches['season_id'].max()
    if time_filter == "Last 5 Years":
        filtered_matches = matches[matches['season_id'] >= (max_season - 4)]
    elif time_filter == "Last 10 Years":
        filtered_matches = matches[matches['season_id'] >= (max_season - 9)]
    else:
        filtered_matches = matches

    month_dist = filtered_matches.groupby(['season_id', 'month_name']).size().reset_index(name='match_count')
    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    
    # Sort seasons so they appear chronologically
    season_order = sorted(filtered_matches['season_id'].unique())
    
    fig3 = px.bar(month_dist, x='season_id', y='match_count', color='month_name', barmode='group',
                  category_orders={"month_name": month_order, "season_id": season_order})
    
    # Ensure chronological categorical x-axis
    fig3.update_layout(xaxis_type='category')
        
    st.plotly_chart(fig3, use_container_width=True)


    st.divider()

    st.subheader("🏵️ Global Tournament Hierarchy (Sunburst)")
    st.markdown("An interactive, multi-layered breakdown exploring where tournaments were hosted and who dominated those specific grounds. (Click a Season to zoom in!)")
    
    # Sunburst Chart shows Season -> City -> Match Winner
    # Filter out empty or NaN cities/winners.
    sunburst_data = matches.dropna(subset=['season_id', 'city', 'match_winner']).copy()
    sunburst_data['season_id'] = sunburst_data['season_id'].astype(str) # string for categorical
    
    # Calculate the size (Match Count)
    sb_counts = sunburst_data.groupby(['season_id', 'city', 'match_winner']).size().reset_index(name='Matches')
    
    fig_sunburst = px.sunburst(
        sb_counts,
        path=['season_id', 'city', 'match_winner'],
        values='Matches',
        color='Matches',
        color_continuous_scale=px.colors.sequential.Inferno,
        labels={'Matches': 'Games Played/Won'}
    )
    
    fig_sunburst.update_layout(
        height=700,
        margin=dict(t=0, l=0, r=0, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    fig_sunburst.update_traces(
        textinfo="label+value", 
        insidetextorientation='radial',
        marker=dict(line=dict(color='#0B0E14', width=1)) # Clean dark borders between segments
    )
    
    st.plotly_chart(fig_sunburst, use_container_width=True)


# ==========================================
# ==========================================
# PAGE 2: TEAM & TOSS ANALYSIS
# ==========================================
# ==========================================
# PAGE 2: VENUE ANALYTICS
# ==========================================
elif menu == "Venue Analytics":
    st.title("🏟️ Venue Analytics")
    st.markdown("Explore stadium fortresses and pitch DNA classification.")

    st.subheader("Venue Fortresses")
    
    # Calculate Total Wins per Venue for each Team
    venue_wins = matches.groupby(['venue', 'match_winner']).size().reset_index(name='total_wins')
    
    # Calculate Total Matches Played at each Venue for each Team
    team_venue_matches = matches.melt(id_vars=['match_id', 'venue'], value_vars=['team1', 'team2'], value_name='team')
    team_venue_played = team_venue_matches.groupby(['venue', 'team']).size().reset_index(name='matches_played')
    
    # Merge and calculate properties
    fortress_data = pd.merge(team_venue_played, venue_wins, left_on=['venue', 'team'], right_on=['venue', 'match_winner'], how='left')
    fortress_data['total_wins'] = fortress_data['total_wins'].fillna(0)
    fortress_data['win_percentage'] = (fortress_data['total_wins'] / fortress_data['matches_played']) * 100
    if 'match_winner' in fortress_data.columns:
        fortress_data = fortress_data.drop('match_winner', axis=1)
        
    tab1, tab2 = st.tabs(["🛡️ Team Fortress Finder", "🌋 Elite League Fortresses"])
    
    with tab1:
        # Filter for valid strings to avoid NaNs
        teams_list = sorted([t for t in fortress_data['team'].unique() if isinstance(t, str)])
        
        # Default to a highly popular team, or just the first if not available
        default_index = teams_list.index('India') if 'India' in teams_list else 0
        selected_team = st.selectbox("Select a Team to view their most dominant grounds:", teams_list, index=default_index)
        
        team_data = fortress_data[fortress_data['team'] == selected_team].copy()
        # Filter to places they've played a decent number of times
        team_data = team_data[team_data['matches_played'] >= 2]
        team_data = team_data.sort_values(by='total_wins', ascending=True).tail(10) # Top 10 by volume
        
        if not team_data.empty:
            fig_team = px.bar(
                team_data, x="total_wins", y="venue", orientation='h',
                color="win_percentage", color_continuous_scale="YlOrRd",
                text="total_wins",
                labels={"total_wins": "Total Wins", "venue": "Venue", "win_percentage": "Win %"},
                title=f"Top Grounds for {selected_team} (Min 2 Matches)"
            )
            fig_team.update_traces(textposition='outside')
            fig_team.update_layout(margin=dict(r=50))
            st.plotly_chart(fig_team, use_container_width=True)
        else:
            st.info("Not enough data to map fortresses for this team (minimum 2 matches required per venue).")
            
    with tab2:
        st.markdown("The most dominant **Team + Venue** combinations in history (Min. 3 home wins).")
        elite_fortresses = fortress_data[fortress_data['total_wins'] >= 3].copy()
        
        if not elite_fortresses.empty:
            elite_fortresses['hover_name'] = elite_fortresses['team'] + " at " + elite_fortresses['venue']
            fig_bubble = px.scatter(
                elite_fortresses, x='matches_played', y='win_percentage', size='total_wins',
                color='team', hover_name='hover_name',
                labels={'matches_played': 'Matches Played at Venue', 'win_percentage': 'Win Percentage (%)', 'total_wins': 'Total Wins'},
                size_max=40
            )
            # Add a baseline
            fig_bubble.add_hline(y=50, line_dash="dash", line_color="gray", annotation_text="50% Global Average")
            fig_bubble.update_layout(yaxis=dict(range=[0, 110]))
            st.plotly_chart(fig_bubble, use_container_width=True)
        else:
            st.info("No elite fortresses found.")

    st.subheader("🌋 Venue Pitch DNA Matrix (Top 20 Venues)")
    st.markdown("Classifying the world's most popular venues by Average 1st Innings Score vs Average Wickets Lost.")
    
    # 1. Get Top 20 Cities by Match Volume
    top_cities = matches['city'].value_counts().head(20).index.tolist()
    
    # 2. Filter matches and t20_data for these cities (1st innings only to gauge pitch baseline)
    matrix_matches = matches[matches['city'].isin(top_cities)][['match_id', 'city']]
    first_inn_data = t20_data[(t20_data['innings'] == 1)].merge(matrix_matches, on='match_id', how='inner')
    
    # 3. Calculate Average Runs and Wickets per Match per City
    match_totals = first_inn_data.groupby(['city', 'match_id']).agg({'total_runs': 'sum', 'is_wicket': 'sum'}).reset_index()
    city_dna = match_totals.groupby('city').agg({'total_runs': 'mean', 'is_wicket': 'mean'}).reset_index()
    city_dna.columns = ['City', 'Avg 1st Inn Score', 'Avg Wickets Lost']
    
    # Calculate totals for bubble size (Match Volume)
    city_volume = matches['city'].value_counts().reset_index()
    city_volume.columns = ['City', 'Match Count']
    city_dna = city_dna.merge(city_volume, on='City')
    
    med_score = city_dna['Avg 1st Inn Score'].median()
    med_wickets = city_dna['Avg Wickets Lost'].median()
    
    fig_matrix = px.scatter(
        city_dna, x='Avg 1st Inn Score', y='Avg Wickets Lost', size='Match Count', color='City',
        text='City', size_max=40,
        labels={'Avg 1st Inn Score': 'Average 1st Innings Score', 'Avg Wickets Lost': 'Average Wickets Fallen'}
    )
    
    # Draw Quadrants
    fig_matrix.add_hline(y=med_wickets, line_dash="dash", line_color="gray", opacity=0.5)
    fig_matrix.add_vline(x=med_score, line_dash="dash", line_color="gray", opacity=0.5)
    
    # Annotate Quadrants
    fig_matrix.add_annotation(x=city_dna['Avg 1st Inn Score'].max(), y=city_dna['Avg Wickets Lost'].min(), text="Batting Highways", showarrow=False, font=dict(color="green", size=14), opacity=0.6, yshift=-20)
    fig_matrix.add_annotation(x=city_dna['Avg 1st Inn Score'].min(), y=city_dna['Avg Wickets Lost'].max(), text="Bowling Minefields", showarrow=False, font=dict(color="red", size=14), opacity=0.6, yshift=20)
    fig_matrix.add_annotation(x=city_dna['Avg 1st Inn Score'].max(), y=city_dna['Avg Wickets Lost'].max(), text="Chaotic (High Runs & Wickets)", showarrow=False, font=dict(color="#f59e0b", size=14), opacity=0.6, yshift=20)
    fig_matrix.add_annotation(x=city_dna['Avg 1st Inn Score'].min(), y=city_dna['Avg Wickets Lost'].min(), text="Sluggish", showarrow=False, font=dict(color="#38BDF8", size=14), opacity=0.6, yshift=-20)
    
    fig_matrix.update_traces(textposition='top center', marker=dict(line=dict(width=1, color='DarkSlateGrey')))
    fig_matrix.update_layout(height=650, showlegend=False, margin=dict(t=20))
    
    st.plotly_chart(fig_matrix, use_container_width=True)


elif menu == "Team & Toss Analysis":
    st.title("🪙 Team & Toss Analysis")
    st.markdown("Deep dive into the psychological DNA of the defining World Cup teams.")

    # ==========================================
    # RESTORED FEATURE: TEAM PERFORMANCE STACKED BAR
    # ==========================================
    st.subheader("Team Performance (Matches Won by Season)")

    # 1. Group by both the winning team and the season
    team_season_wins = matches.groupby(['match_winner', 'season_id']).size().reset_index(name='matches_won')

    # 2. Convert season_id to a string for discrete colors
    team_season_wins['season_id'] = team_season_wins['season_id'].astype(str)

    # 3. Create a sorted list of all unique seasons to lock the legend order
    sorted_seasons = sorted(team_season_wins['season_id'].unique())

    # 4. Create the stacked bar chart with the category_orders parameter
    fig_stacked = px.bar(
        team_season_wins,
        x='match_winner',
        y='matches_won',
        color='season_id',
        barmode='stack',
        category_orders={'season_id': sorted_seasons},  # <-- This forces the sorted legend
        labels={'matches_won': 'Matches Won', 'match_winner': 'Team', 'season_id': 'Season'}
    )

    # Sort the x-axis bars by total wins descending
    fig_stacked.update_layout(xaxis={'categoryorder': 'total descending'})
    st.plotly_chart(fig_stacked, use_container_width=True)
    st.divider()



    # ==========================================
    # UPGRADE: CAPTAINS CHOICES
    # ==========================================
    st.header("⚖️ Captains' Choices Over Time")
    st.markdown("Has the global T20 meta shifted from batting first to chasing over the last 15 years?")
    choice_trends = matches.groupby(['season_id', 'toss_decision']).size().reset_index(name='count')
    fig_area = px.area(
        choice_trends, x='season_id', y='count', color='toss_decision',
        color_discrete_map={'field': '#3b82f6', 'bat': '#f59e0b'},
        labels={'season_id': 'Season', 'count': 'Number of Tosses'},
    )
    fig_area.update_layout(xaxis_type='category', height=400)
    st.plotly_chart(fig_area, use_container_width=True)


    # ==========================================
    # UPGRADE 3: TARGET SETTING VS CHASING (TORNADO CHART)
    # ==========================================
    st.header("🧬 Team DNA: Setting Targets vs Chasing")
    st.markdown("A psychological symmetry profile showing if a team wins more by setting targets (Left) or chasing them down (Right).")

    # Re-calculate major teams logic (must have won at least 2 matches)
    total_wins = matches['match_winner'].value_counts()
    major_teams = total_wins[total_wins >= 2].reset_index()
    major_teams.columns = ['Team', 'Matches Won']

    # Calculating win modes for major teams
    major_matches = matches[matches['match_winner'].isin(major_teams['Team'])].copy()
    defending_wins = major_matches.groupby('match_winner')['win_by_runs'].apply(lambda x: (x > 0).sum()).reset_index(name='Defending')
    chasing_wins = major_matches.groupby('match_winner')['win_by_wickets'].apply(lambda x: (x > 0).sum()).reset_index(name='Chasing')
    
    dna = pd.merge(defending_wins, chasing_wins, on='match_winner')
    
    # Sort by total volume
    dna['Total'] = dna['Defending'] + dna['Chasing']
    dna = dna.sort_values(by='Total', ascending=True).drop(columns=['Total'])
    
    # For tornado chart, we make the "Defending" values negative so they stretch to the left!
    dna['Defending'] = dna['Defending'] * -1
    
    # Melt it
    dna_melted = dna.melt(id_vars='match_winner', var_name='Method', value_name='Wins')
    
    fig_tornado = px.bar(
        dna_melted, 
        x='Wins', 
        y='match_winner', 
        color='Method',
        orientation='h',
        color_discrete_map={'Defending': '#f97316', 'Chasing': '#06b6d4'},
        barmode='relative',
        text=dna_melted['Wins'].abs() # Show absolute numbers on bars so they don't read nicely
    )
    
    fig_tornado.update_layout(
        xaxis_title="<────── Dominance Defending  |  Dominance Chasing ──────>",
        yaxis_title="",
        xaxis=dict(showticklabels=False), # Hide the confusing negative axes numbers
        margin=dict(l=0, r=0, t=30, b=50)
    )
    
    st.plotly_chart(fig_tornado, use_container_width=True)

    st.divider()

    # ==========================================
    # SHOWSTOPPER: ELITE TEAM ANALYTICS
    # ==========================================
    st.header("🧬 Elite Team Analytics")
    st.markdown("Modern T20 requires breaking down Teams into dynamic phases, risk dependency, and pure situational luck.")

    # 1. PHASE DOMINANCE RADAR
    st.subheader("1. Phase Dominance Radar")
    st.markdown("*Evaluating aggregate Run Rates across the 3 critical match phases.*")
    
    top_10_teams = sorted(["India", "Australia", "England", "South Africa", "New Zealand", "Pakistan", "West Indies", "Sri Lanka", "Afghanistan", "Bangladesh"])
    
    selected_radar_teams = st.multiselect(
        "Select Teams to Compare (Max 4 recommended):",
        options=top_10_teams,
        default=["India", "Australia", "England"],
        key="radar_team_select"
    )
    
    if not selected_radar_teams:
        st.warning("Please select at least one team to view Phase Dominance.")
    else:
        phase_df = t20_data[t20_data['team_batting'].isin(selected_radar_teams)]
        
        phase_runs = phase_df.groupby(['team_batting', 'phase'])['total_runs'].sum().reset_index()
        phase_balls = phase_df[(phase_df['is_wide_ball'] == False) & (phase_df['is_no_ball'] == False)].groupby(['team_batting', 'phase']).size().reset_index(name='legal_balls')
        phase_stats = pd.merge(phase_runs, phase_balls, on=['team_batting', 'phase'])
        phase_stats['Run_Rate'] = (phase_stats['total_runs'] / phase_stats['legal_balls']) * 6
        
        radar_df = phase_stats.pivot(index='team_batting', columns='phase', values='Run_Rate').reset_index()
        cols_needed = ['Powerplay (1-6)', 'Middle Overs (7-15)', 'Death Overs (16-20)']
        
        for col in cols_needed:
            if col not in radar_df.columns:
                radar_df[col] = 0
                
        radar_melt = radar_df.melt(id_vars='team_batting', value_vars=cols_needed, var_name='Phase', value_name='RR')
        
        fig_radar = px.line_polar(
            radar_melt, r='RR', theta='Phase', color='team_batting', line_close=True,
            color_discrete_sequence=px.colors.qualitative.Vivid
        )
        fig_radar.update_traces(fill='toself', opacity=0.45)
        
        max_rr = radar_melt['RR'].max() if not radar_melt.empty else 11
        max_val = max(11, max_rr + 0.5)
        
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[5, max_val])),
            showlegend=True, height=500, margin=dict(l=40, r=40, t=20, b=20)
        )
        st.plotly_chart(fig_radar, use_container_width=True)

    st.divider()

    # 2. TOSS LUCK VS MERIT GRID
    st.subheader("2. 'Toss Luck' vs Merit Grid")
    st.markdown("*Did you win because you were good, or because you called Head?*")
    
    luck_teams = matches['match_winner'].value_counts().head(12).index.tolist()
    
    luck_stats = []
    for team in luck_teams:
        team_matches = matches[(matches['team1'] == team) | (matches['team2'] == team)]
        total_matches = len(team_matches)
        toss_wins = len(team_matches[team_matches['toss_winner'] == team])
        match_wins = len(team_matches[team_matches['match_winner'] == team])
        
        toss_win_pct = (toss_wins / total_matches) * 100
        match_win_pct = (match_wins / total_matches) * 100
        luck_stats.append({'Team': team, 'Toss Win %': toss_win_pct, 'Match Win %': match_win_pct, 'Total Matches': total_matches})
        
    luck_df = pd.DataFrame(luck_stats)
    
    fig_luck = px.scatter(
        luck_df, x='Toss Win %', y='Match Win %', size='Total Matches', color='Team', text='Team', size_max=40,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig_luck.add_hline(y=50, line_dash="dash", line_color="gray", opacity=0.5)
    fig_luck.add_vline(x=50, line_dash="dash", line_color="gray", opacity=0.5)
    
    fig_luck.add_annotation(x=25, y=75, text="Unlucky but Dominant", showarrow=False, font=dict(color="green"), opacity=0.6)
    fig_luck.add_annotation(x=75, y=75, text="Lucky & Dominant", showarrow=False, font=dict(color="#3b82f6"), opacity=0.6)
    fig_luck.add_annotation(x=25, y=25, text="Unlucky & Bad", showarrow=False, font=dict(color="gray"), opacity=0.6)
    fig_luck.add_annotation(x=75, y=25, text="Lucky but Bad", showarrow=False, font=dict(color="red"), opacity=0.6)

    fig_luck.update_traces(textposition='top center', marker=dict(line=dict(width=1, color='DarkSlateGrey')))
    fig_luck.update_layout(height=500, showlegend=False, xaxis=dict(range=[10, 90]), yaxis=dict(range=[10, 90]), margin=dict(t=20))
    st.plotly_chart(fig_luck, use_container_width=True)

    st.divider()

    # 3. BOUNDARY DEPENDENCY MATRIX
    st.subheader("3. Team Dependency Matrix")
    st.markdown("*Boom or Bust? Boundary % vs Dot Ball %*")
    
    dep_teams = matches['match_winner'].value_counts().head(12).index.tolist()
    dep_df = t20_data[t20_data['team_batting'].isin(dep_teams)]
    
    dep_bounds = dep_df[dep_df['batter_runs'].isin([4, 6])].groupby('team_batting')['batter_runs'].sum().reset_index(name='boundary_runs')
    dep_total = dep_df.groupby('team_batting')['total_runs'].sum().reset_index(name='dt_runs') 
    dep_bound_merged = pd.merge(dep_bounds, dep_total, on='team_batting')
    dep_bound_merged['Boundary %'] = (dep_bound_merged['boundary_runs'] / dep_bound_merged['dt_runs']) * 100
    
    dep_balls = dep_df[(dep_df['is_wide_ball'] == False) & (dep_df['is_no_ball'] == False)]
    dep_dots = dep_balls[(dep_balls['batter_runs'] == 0) & (dep_balls['extra_runs'] == 0)].groupby('team_batting').size().reset_index(name='dots')
    dep_ball_total = dep_balls.groupby('team_batting').size().reset_index(name='total_balls')
    dep_dot_merged = pd.merge(dep_dots, dep_ball_total, on='team_batting')
    dep_dot_merged['Dot %'] = (dep_dot_merged['dots'] / dep_dot_merged['total_balls']) * 100
    
    matrix_df = pd.merge(dep_bound_merged, dep_dot_merged, on='team_batting')
    
    med_bound = matrix_df['Boundary %'].median()
    med_dot = matrix_df['Dot %'].median()
    
    fig_matrix = px.scatter(
        matrix_df, x='Dot %', y='Boundary %', color='team_batting', text='team_batting', size='dt_runs', size_max=40,
        color_discrete_sequence=px.colors.qualitative.Vivid
    )
    fig_matrix.add_hline(y=med_bound, line_dash="dash", line_color="gray", opacity=0.5)
    fig_matrix.add_vline(x=med_dot, line_dash="dash", line_color="gray", opacity=0.5)
    
    fig_matrix.add_annotation(x=matrix_df['Dot %'].max(), y=matrix_df['Boundary %'].max(), text="Boom or Bust", showarrow=False, font=dict(color="red"), opacity=0.6, yshift=20)
    fig_matrix.add_annotation(x=matrix_df['Dot %'].min(), y=matrix_df['Boundary %'].min(), text="Strike Rotators", showarrow=False, font=dict(color="green"), opacity=0.6, yshift=-20)
    
    fig_matrix.update_traces(textposition='top center', marker=dict(line=dict(width=1, color='DarkSlateGrey')))
    fig_matrix.update_layout(height=500, showlegend=False, margin=dict(t=20))
    st.plotly_chart(fig_matrix, use_container_width=True)

    st.divider()

    # 4. PAR SCORE DELTA (Instant Regret)
    st.subheader("4. Par Score Delta ('Instant Regret')")
    st.markdown("*When teams win the toss and BAT, do they actually read the pitch correctly?*")
    
    first_inn = t20_data[t20_data['innings'] == 1]
    
    # Calculate scores per match
    match_scores = first_inn.groupby('match_id')['total_runs'].sum().reset_index()
    
    # Merge with matches to acquire the 'city' column
    match_scores = pd.merge(match_scores, matches[['match_id', 'city']], on='match_id', how='inner')
    
    # Calculate venue average
    venue_avg = match_scores.groupby('city')['total_runs'].mean().reset_index(name='venue_par_score')
    
    bat_first_toss = matches[(matches['toss_decision'] == 'bat')].copy()
    
    bat_logic = pd.merge(bat_first_toss, venue_avg, on='city', how='inner')
    
    real_scores = first_inn.groupby(['match_id', 'team_batting'])['total_runs'].sum().reset_index()
    bat_logic = pd.merge(bat_logic, real_scores, left_on=['match_id', 'toss_winner'], right_on=['match_id', 'team_batting'], how='inner')
    
    bat_logic['Delta'] = bat_logic['total_runs'] - bat_logic['venue_par_score']
    
    delta_df = bat_logic.groupby('team_batting').agg({'Delta': 'mean', 'match_id': 'count'}).reset_index()
    delta_df = delta_df[delta_df['match_id'] >= 3] 
    delta_df = delta_df.sort_values(by='Delta', ascending=True)
    
    delta_df['Color'] = delta_df['Delta'].apply(lambda x: '#10b981' if x > 0 else '#ef4444')
    
    fig_delta = px.bar(
        delta_df, x='Delta', y='team_batting', orientation='h', color='Color',
        text=delta_df['Delta'].apply(lambda x: f"{'+' if x>0 else ''}{x:.1f} Runs"),
         color_discrete_map={'#10b981': '#10b981', '#ef4444': '#ef4444'}
    )
    fig_delta.update_layout(showlegend=False, height=500, margin=dict(l=0, r=0, t=20, b=20), xaxis_title="Average Runs Above/Below Venue Par Score")
    st.plotly_chart(fig_delta, use_container_width=True)


# ==========================================
# PAGE 3: PLAYER LEADERBOARDS
# ==========================================
elif menu == "Player Leaderboards":
    st.title("Player Leaderboards")

    # ==========================================
    # SHOWSTOPPER MODULE: MODERN IMPACT METRICS
    # ==========================================
    st.header("⚡ Modern Impact Analytics")
    st.markdown("Traditional metrics reward raw volume. Modern metrics reward **efficiency, pressure, and clutch performance**.")
    
    # ------------------------------------------
    # SEASON FILTERING LOGIC
    # ------------------------------------------
    st.markdown("---")
    season_col, _ = st.columns([1, 2])
    with season_col:
        available_seasons = sorted(t20_data['season_id'].unique(), reverse=True)
        season_options = ["All-Time"] + [str(s) for s in available_seasons]
        selected_season_str = st.selectbox("Select Season to Analyze:", season_options)
        
    if selected_season_str == "All-Time":
        plot_df = t20_data
        r_cut = 300
        death_cut = 50
        dot_cut = 200
        pp_cut = 100
        display_season = "All-Time"
    else:
        # User selected a specific year
        selected_year = int(selected_season_str)
        plot_df = t20_data[t20_data['season_id'] == selected_year]
        r_cut = 100
        death_cut = 15
        dot_cut = 48
        pp_cut = 30
        display_season = f"{selected_year}"
        st.info(f"Filters scale-down activated for a single tournament: Min Runs ({r_cut}), Min Death Balls ({death_cut}), Min Balls Bowled ({dot_cut}), Min PP Balls ({pp_cut})")

    # 1. TRUE IMPACT STRIKERS (Boundary %)
    st.subheader(f"1. The 'True Impact' Strikers ({display_season})")
    st.markdown(f"*Highest Boundary % (Min. {r_cut} Runs)*")
    
    batter_runs = plot_df.groupby('batter')['batter_runs'].sum().reset_index()
    valid_batters = batter_runs[batter_runs['batter_runs'] >= r_cut]['batter'].tolist()
    
    impact_df = plot_df[plot_df['batter'].isin(valid_batters)]
    boundary_runs = impact_df[impact_df['batter_runs'].isin([4, 6])].groupby('batter')['batter_runs'].sum().reset_index(name='boundary_runs')
    total_runs = impact_df.groupby('batter')['batter_runs'].sum().reset_index(name='total_runs')
    
    impact_board = pd.merge(total_runs, boundary_runs, on='batter')
    impact_board['Boundary %'] = (impact_board['boundary_runs'] / impact_board['total_runs']) * 100
    impact_board = impact_board.sort_values('Boundary %', ascending=False).head(10)
    
    if not impact_board.empty:
        fig_impact = px.bar(
            impact_board, x='Boundary %', y='batter', orientation='h',
            text=impact_board['Boundary %'].apply(lambda x: f"{x:.1f}%"),
            color='Boundary %', color_continuous_scale='Tealgrn'
        )
        fig_impact.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False, height=500, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_impact, use_container_width=True)
    else:
        st.warning(f"No batters met the {r_cut} run minimum criteria for {display_season}.")

    st.divider()

    # 2. ICE COLD FINISHERS
    st.subheader(f"2. The 'Ice-Cold' Finishers ({display_season})")
    st.markdown(f"*Highest Death Over Strike Rate (Min. {death_cut} Balls in Overs 16-20)*")
    
    death_data = plot_df[plot_df['phase'] == 'Death Overs (16-20)']
    legal_death = death_data[(death_data['is_wide_ball'] == False)]
    death_balls = legal_death.groupby('batter').size().reset_index(name='balls_faced')
    valid_death_batters = death_balls[death_balls['balls_faced'] >= death_cut]['batter'].tolist()
    
    finisher_df = death_data[death_data['batter'].isin(valid_death_batters)]
    if not finisher_df.empty:
        finisher_runs = finisher_df.groupby('batter')['batter_runs'].sum().reset_index()
        finisher_legal_balls = finisher_df[(finisher_df['is_wide_ball'] == False)].groupby('batter').size().reset_index(name='balls')
        
        finisher_board = pd.merge(finisher_runs, finisher_legal_balls, on='batter')
        finisher_board['Death SR'] = (finisher_board['batter_runs'] / finisher_board['balls']) * 100
        finisher_board = finisher_board.sort_values('Death SR', ascending=False).head(10)
        
        fig_finish = px.bar(
            finisher_board, x='Death SR', y='batter', orientation='h',
            text=finisher_board['Death SR'].apply(lambda x: f"{x:.0f}"),
            color='Death SR', color_continuous_scale='Reds'
        )
        fig_finish.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False, height=500, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_finish, use_container_width=True)
    else:
        st.warning(f"No batters faced {death_cut} balls in the Death Overs for {display_season}.")

    st.divider()

    # 3. DOT BALL STRANGLERS
    st.subheader(f"3. The 'Dot Ball Stranglers' ({display_season})")
    st.markdown(f"*Highest Dot Ball % (Min. {dot_cut} Balls Bowled)*")
    
    legal_bowls = plot_df[(plot_df['is_wide_ball'] == False) & (plot_df['is_no_ball'] == False)]
    bowler_balls = legal_bowls.groupby('bowler').size().reset_index(name='total_balls')
    valid_bowlers = bowler_balls[bowler_balls['total_balls'] >= dot_cut]['bowler'].tolist()
    
    strangle_df = legal_bowls[legal_bowls['bowler'].isin(valid_bowlers)]
    if not strangle_df.empty:
        dots = strangle_df[(strangle_df['batter_runs'] == 0) & (strangle_df['extra_runs'] == 0)].groupby('bowler').size().reset_index(name='dot_balls')
        totals = strangle_df.groupby('bowler').size().reset_index(name='total')
        
        dot_board = pd.merge(totals, dots, on='bowler')
        dot_board['Dot %'] = (dot_board['dot_balls'] / dot_board['total']) * 100
        dot_board = dot_board.sort_values('Dot %', ascending=False).head(10)
        
        fig_dot = px.bar(
            dot_board, x='Dot %', y='bowler', orientation='h',
            text=dot_board['Dot %'].apply(lambda x: f"{x:.1f}%"),
            color='Dot %', color_continuous_scale='ice'
        )
        fig_dot.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False, height=500, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_dot, use_container_width=True)
    else:
        st.warning(f"No bowlers bowled {dot_cut} legal deliveries for {display_season}.")


    st.divider()

    # 4. POWERPLAY ASSASSINS
    st.subheader(f"4. The 'Powerplay Assassins' ({display_season})")
    st.markdown(f"*Lowest Powerplay Economy (Min. {pp_cut} Balls in Overs 1-6)*")
    
    pp_data = plot_df[plot_df['phase'] == 'Powerplay (1-6)']
    legal_pp = pp_data[(pp_data['is_wide_ball'] == False) & (pp_data['is_no_ball'] == False)]
    pp_balls = legal_pp.groupby('bowler').size().reset_index(name='total_balls')
    valid_pp_bowlers = pp_balls[pp_balls['total_balls'] >= pp_cut]['bowler'].tolist()
    
    assassin_df = pp_data[pp_data['bowler'].isin(valid_pp_bowlers)]
    if not assassin_df.empty:
        pp_runs_conceded = assassin_df.groupby('bowler')['total_runs'].sum().reset_index()
        pp_legal_balls = assassin_df[(assassin_df['is_wide_ball'] == False) & (assassin_df['is_no_ball'] == False)].groupby('bowler').size().reset_index(name='balls')
        
        assassin_board = pd.merge(pp_runs_conceded, pp_legal_balls, on='bowler')
        assassin_board['Economy'] = assassin_board['total_runs'] / (assassin_board['balls'] / 6)
        assassin_board = assassin_board.sort_values('Economy', ascending=True).head(10)
        
        fig_assassin = px.bar(
            assassin_board, x='Economy', y='bowler', orientation='h',
            text=assassin_board['Economy'].apply(lambda x: f"{x:.2f}"),
            color='Economy', color_continuous_scale='Viridis_r' 
        )
        fig_assassin.update_layout(yaxis={'categoryorder':'total descending'}, showlegend=False, height=500, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_assassin, use_container_width=True)
    else:
        st.warning(f"No bowlers bowled {pp_cut} deliveries in the Powerplay for {display_season}.")

    st.divider()

    st.subheader("Top 10 All-Time Run Scorers (Seasonal Breakdown)")

    # Identify top 10 names first
    top_10_names = t20_data.groupby('batter')['batter_runs'].sum().nlargest(10).index

    # Filter and group
    top_10_data = t20_data[t20_data['batter'].isin(top_10_names)]
    df_stacked = top_10_data.groupby(['batter', 'season_id'])['batter_runs'].sum().reset_index()
    df_stacked['season_id'] = df_stacked['season_id'].astype(str)

    fig1 = px.bar(
        df_stacked,
        x='batter',
        y='batter_runs',
        color='season_id',
        barmode='stack',
        category_orders={'season_id': sorted(df_stacked['season_id'].unique())},
        labels={'batter_runs': 'Total Runs', 'batter': 'Player', 'season_id': 'Season'}
    )

    fig1.update_layout(xaxis={'categoryorder': 'total descending'})
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("Top 10 All-Time Wicket Takers (Seasonal Breakdown)")

    # 1. Filter for valid bowler wickets (excluding run outs, etc.)
    valid_wickets_df = t20_data[
        ~t20_data['wicket_kind'].isin(['run out', 'obstructing the field', 'retired out', 'retired hurt'])]
    bowler_wickets_df = valid_wickets_df[valid_wickets_df['is_wicket'] == True]

    # 2. Identify the Top 10 bowler names by total valid wickets
    top_10_bowler_names = bowler_wickets_df.groupby('bowler').size().nlargest(10).index

    # 3. Filter the dataframe for only these 10 bowlers and group by season
    top_10_bowler_data = bowler_wickets_df[bowler_wickets_df['bowler'].isin(top_10_bowler_names)]
    df_stacked_bowlers = top_10_bowler_data.groupby(['bowler', 'season_id']).size().reset_index(name='Wickets Taken')

    # 4. Convert season_id to string for discrete color mapping in the legend
    df_stacked_bowlers['season_id'] = df_stacked_bowlers['season_id'].astype(str)

    # 5. Create the stacked bar chart
    fig2 = px.bar(
        df_stacked_bowlers,
        x='bowler',
        y='Wickets Taken',
        color='season_id',
        barmode='stack',
        category_orders={'season_id': sorted(df_stacked_bowlers['season_id'].unique())},
        labels={'Wickets Taken': 'Total Wickets', 'bowler': 'Player', 'season_id': 'Season'}
    )

    # 6. Ensure the bars are sorted by total career wickets from left to right
    fig2.update_layout(xaxis={'categoryorder': 'total descending'})
    st.plotly_chart(fig2, use_container_width=True)

    st.divider()
    st.subheader("Top 15 Player of the Match Winners (Seasonal Breakdown)")

# 1. Identify the Top 15 POTM winners across all seasons
# Note: Assuming your column is named 'player_name' based on your previous code.
# If standard Kaggle data, it might be 'player_of_match'. Adjust if necessary.
    top_15_potm_names = matches['player_name'].value_counts().nlargest(15).index

# 2. Filter matches dataframe for only these 15 players
    top_15_matches = matches[matches['player_name'].isin(top_15_potm_names)]

# 3. Group by player and season to calculate the stack segments
    potm_stacked = top_15_matches.groupby(['player_name', 'season_id']).size().reset_index(name='POTM Awards')

# 4. Convert season_id to string for discrete color mapping in the legend
    potm_stacked['season_id'] = potm_stacked['season_id'].astype(str)
    sorted_seasons_potm = sorted(potm_stacked['season_id'].unique())

# 5. Create the horizontal stacked bar chart
    fig3 = px.bar(
        potm_stacked,
        x='POTM Awards',
        y='player_name',
        color='season_id',
        orientation='h',  # <-- This flips it to a horizontal bar chart
        barmode='stack',
        category_orders={'season_id': sorted_seasons_potm},
        labels={'POTM Awards': 'Total Awards', 'player_name': 'Player', 'season_id': 'Season'}
    )

# 6. Sort the y-axis so the player with the MOST awards is at the very top
# For horizontal charts, 'total ascending' builds from the bottom up, putting the max at the top.
    fig3.update_layout(yaxis={'categoryorder': 'total ascending'})

    st.plotly_chart(fig3, use_container_width=True)








# ==========================================
# PAGE 4: HEAD-TO-HEAD COMPARISONS (CONSOLIDATED)
# ==========================================
elif menu == "Head-to-Head Comparisons":
    st.title("⚔️ Head-to-Head Player Comparisons")
    st.markdown("A centralized hub to analyze players side-by-side across standard stats, phases, and modern eras.")

    tab_batters, tab_bowlers = st.tabs(
        ["🏏 Batters (All-Time)", "🥎 Bowlers (All-Time)"])

    # ----------------------------------------
    # TAB 1: BATTERS
    # ----------------------------------------
    # ----------------------------------------
    # TAB 1: BATTERS (ADVANCED SCOUTING)
    # ----------------------------------------
    # ----------------------------------------
    # TAB 1: BATTERS (ADVANCED SCOUTING)
    # ----------------------------------------
    # ----------------------------------------
    # TAB 1: BATTERS (ADVANCED SCOUTING)
    # ----------------------------------------
    # ----------------------------------------
    # TAB 1: BATTERS (ADVANCED SCOUTING)
    # ----------------------------------------
    with tab_batters:
        st.header("Advanced Head-to-Head Batter Comparison")
        st.markdown(
            "Evaluating batters using deep-dive metrics: scoring speed, boundary dependency, phase survival, and partnership dynamics.")

        batter_list = sorted(t20_data['batter'].unique())

        col1, col2 = st.columns(2)
        with col1:
            player_A = st.selectbox("Select Batter A", batter_list,
                                    index=batter_list.index('V Kohli') if 'V Kohli' in batter_list else 0,
                                    key="adv_bat_a")
        with col2:
            player_B = st.selectbox("Select Batter B", batter_list,
                                    index=batter_list.index('MS Dhoni') if 'MS Dhoni' in batter_list else 1,
                                    key="adv_bat_b")


        def get_advanced_batter_stats(player_name):
            b_df = t20_data[t20_data['batter'] == player_name].copy()
            # For a batter, No-Balls DO count as a ball faced. Only Wides do not.
            balls_faced_df = b_df[b_df['is_wide_ball'] == False]

            total_runs = b_df['batter_runs'].sum()
            total_balls_faced = balls_faced_df.shape[0]

            # Dismissals
            dismissals = b_df[b_df['is_wicket'] == True].shape[0]

            # 1. Standard Efficiency
            avg = total_runs / dismissals if dismissals > 0 else total_runs
            sr = (total_runs / total_balls_faced) * 100 if total_balls_faced > 0 else 0

            # 2. Milestones (50s and 100s)
            match_scores = b_df.groupby('match_id')['batter_runs'].sum()
            fifties = match_scores[(match_scores >= 50) & (match_scores < 100)].count()
            hundreds = match_scores[match_scores >= 100].count()

            # 3. Boundaries & Dots
            fours = b_df[b_df['batter_runs'] == 4].shape[0]
            sixes = b_df[b_df['batter_runs'] == 6].shape[0]
            boundary_runs = (fours * 4) + (sixes * 6)

            boundary_pct = (boundary_runs / total_runs) * 100 if total_runs > 0 else 0
            bpb = total_balls_faced / (fours + sixes) if (fours + sixes) > 0 else 0

            dots = b_df[b_df['batter_runs'] == 0].shape[0]
            dot_pct = (dots / total_balls_faced) * 100 if total_balls_faced > 0 else 0

            # 4. Survival (Balls Per Dismissal)
            bpd = total_balls_faced / dismissals if dismissals > 0 else total_balls_faced

            # 5. Winning Contribution
            b_merged = b_df.merge(matches[['match_id', 'match_winner']], on='match_id', how='left')
            win_df = b_merged[b_merged['team_batting'] == b_merged['match_winner']]
            win_runs = win_df['batter_runs'].sum()
            win_balls_faced = win_df[win_df['is_wide_ball'] == False].shape[0]
            win_dismissals = win_df[win_df['is_wicket'] == True].shape[0]

            win_avg = win_runs / win_dismissals if win_dismissals > 0 else win_runs
            win_sr = (win_runs / win_balls_faced) * 100 if win_balls_faced > 0 else 0

            # 6. Pace vs Spin Match-ups
            def categorize_bowler(b_type):
                b_type = str(b_type).lower()
                if any(k in b_type for k in ['fast', 'medium', 'pace']):
                    return 'Pace'
                elif any(k in b_type for k in ['spin', 'break', 'orthodox', 'chinaman', 'googly']):
                    return 'Spin'
                return 'Other'

            b_df['bowler_cat'] = b_df['bowler_type'].apply(categorize_bowler)

            def matchup_stat(cat):
                cat_df = b_df[b_df['bowler_cat'] == cat]
                c_runs = cat_df['batter_runs'].sum()
                c_balls = cat_df[cat_df['is_wide_ball'] == False].shape[0]
                c_diss = cat_df[cat_df['is_wicket'] == True].shape[0]
                m_avg = c_runs / c_diss if c_diss > 0 else c_runs
                m_sr = (c_runs / c_balls) * 100 if c_balls > 0 else 0
                return m_avg, m_sr

            pace_avg, pace_sr = matchup_stat('Pace')
            spin_avg, spin_sr = matchup_stat('Spin')

            # 7. Phase Specialist Stats
            def phase_stat(phase):
                p_df = b_df[b_df['phase'] == phase]
                p_runs = p_df['batter_runs'].sum()
                p_balls = p_df[p_df['is_wide_ball'] == False].shape[0]
                p_bounds = p_df[p_df['batter_runs'].isin([4, 6])]['batter_runs'].sum()

                phase_sr = (p_runs / p_balls) * 100 if p_balls > 0 else 0
                phase_bpct = (p_bounds / p_runs) * 100 if p_runs > 0 else 0
                return phase_sr, phase_bpct

            pp_sr, pp_bpct = phase_stat('Powerplay (1-6)')
            mid_sr, mid_bpct = phase_stat('Middle Overs (7-15)')
            death_sr, death_bpct = phase_stat('Death Overs (16-20)')

            return {
                "Total Runs": total_runs, "Batting Average": avg, "Overall Strike Rate": sr,
                "Milestones (50s / 100s)": f"{fifties} / {hundreds}", "Boundary %": boundary_pct,
                "Dot Ball %": dot_pct, "Balls Per Boundary (BpB)": bpb, "Balls Per Dismissal (BPD)": bpd,
                "Winning Contribution (Avg)": win_avg, "Winning Contribution (SR)": win_sr,
                "Pace Avg": pace_avg, "Pace SR": pace_sr, "Spin Avg": spin_avg, "Spin SR": spin_sr,
                "PP SR": pp_sr, "Mid SR": mid_sr, "Death SR": death_sr,
                "PP BPCT": pp_bpct, "Mid BPCT": mid_bpct, "Death BPCT": death_bpct
            }


        # Fetch stats
        stats_A = get_advanced_batter_stats(player_A)
        stats_B = get_advanced_batter_stats(player_B)

        # --- 1. TALE OF THE TAPE ---
        st.subheader("📊 Tale of the Tape")

        col_A, col_vs, col_B = st.columns([3, 2, 3])
        with col_A:
            st.markdown(f"<h3 style='text-align: center; color: #1f77b4;'>{player_A}</h3>", unsafe_allow_html=True)
        with col_vs:
            st.markdown("<h3 style='text-align: center; color: gray;'>VS</h3>", unsafe_allow_html=True)
        with col_B:
            st.markdown(f"<h3 style='text-align: center; color: #ff7f0e;'>{player_B}</h3>", unsafe_allow_html=True)

        st.markdown("<hr style='margin-top: 0; margin-bottom: 15px;'>", unsafe_allow_html=True)

        core_metrics = [
            ("Total Runs", "Total Runs"), ("Batting Average", "Batting Average"),
            ("Overall Strike Rate", "Overall Strike Rate"), ("Milestones (50s / 100s)", "Milestones (50s / 100s)"),
            ("Boundary Percentage (%)", "Boundary %"), ("Dot Ball Percentage (%)", "Dot Ball %"),
            ("Balls Per Boundary (BpB)", "Balls Per Boundary (BpB)"),
            ("Balls Per Dismissal (BPD)", "Balls Per Dismissal (BPD)"),
            ("Winning Contribution (Avg)", "Winning Contribution (Avg)"),
            ("Winning Contribution (SR)", "Winning Contribution (SR)")
        ]

        for display_name, dict_key in core_metrics:
            cA, cM, cB = st.columns([3, 2, 3])
            val_A = stats_A[dict_key]
            val_B = stats_B[dict_key]
            if isinstance(val_A, float): val_A = f"{val_A:.2f}"
            if isinstance(val_B, float): val_B = f"{val_B:.2f}"

            cA.markdown(f"<h4 style='text-align: center; margin: 0;'>{val_A}</h4>", unsafe_allow_html=True)
            cM.markdown(
                f"<p style='text-align: center; color: #888; font-size: 14px; font-weight: bold; margin: 0;'>{display_name}</p>",
                unsafe_allow_html=True)
            cB.markdown(f"<h4 style='text-align: center; margin: 0;'>{val_B}</h4>", unsafe_allow_html=True)
            st.markdown("<hr style='margin-top: 10px; margin-bottom: 10px; opacity: 0.2;'>", unsafe_allow_html=True)

        st.divider()

        # --- 2. MATCH-UP & PHASE CHARTS ---
        col3, col4 = st.columns(2)

        with col3:
            st.subheader("⚔️ Bowling Match-ups (Pace vs Spin)")
            matchup_data = pd.DataFrame({
                "Player": [player_A, player_A, player_B, player_B],
                "Bowling Type": ["Pace", "Spin", "Pace", "Spin"],
                "Strike Rate": [stats_A["Pace SR"], stats_A["Spin SR"], stats_B["Pace SR"], stats_B["Spin SR"]]
            })
            fig_matchup = px.bar(
                matchup_data, x="Player", y="Strike Rate", color="Bowling Type",
                barmode="group", text_auto=".1f", color_discrete_sequence=['#d62728', '#1f77b4']
            )
            fig_matchup.update_layout(yaxis_title="Strike Rate")
            st.plotly_chart(fig_matchup, use_container_width=True)

        with col4:
            st.subheader("🕸️ Overall Phase Dominance")
            radar_metrics = ['PP SR', 'Mid SR', 'Death SR', 'Overall Strike Rate']
            radar_df = pd.DataFrame({
                'Metric': [m.replace(' SR', ' Strike Rate') for m in radar_metrics] * 2,
                'Strike Rate': [stats_A[m] for m in radar_metrics] + [stats_B[m] for m in radar_metrics],
                'Player': [player_A] * 4 + [player_B] * 4
            })
            fig_radar = px.line_polar(
                radar_df, r='Strike Rate', theta='Metric', color='Player',
                line_close=True, color_discrete_sequence=['#1f77b4', '#ff7f0e'],
                range_r=[0, max(radar_df['Strike Rate'].max() + 20, 200)]
            )
            fig_radar.update_traces(fill='toself', opacity=0.5)
            st.plotly_chart(fig_radar, use_container_width=True)

        st.divider()

        # --- 3. THE PHASE SPECIALIST PREMIUM ---
        st.subheader("🔥 Phase Specialization")
        st.markdown("Comparing Strike Rate and Boundary Reliance across the three stages of the innings.")

        c_phase1, c_phase2 = st.columns(2)

        phase_compare_df = pd.DataFrame({
            "Player": [player_A] * 3 + [player_B] * 3,
            "Phase": ["Powerplay (1-6)", "Middle Overs (7-15)", "Death Overs (16-20)"] * 2,
            "Strike Rate": [stats_A['PP SR'], stats_A['Mid SR'], stats_A['Death SR'], stats_B['PP SR'],
                            stats_B['Mid SR'], stats_B['Death SR']],
            "Boundary %": [stats_A['PP BPCT'], stats_A['Mid BPCT'], stats_A['Death BPCT'], stats_B['PP BPCT'],
                           stats_B['Mid BPCT'], stats_B['Death BPCT']]
        })

        with c_phase1:
            fig_ps_sr = px.bar(
                phase_compare_df, x='Phase', y='Strike Rate', color='Player', barmode='group',
                text_auto='.1f', color_discrete_sequence=['#1f77b4', '#ff7f0e'],
                category_orders={"Phase": ["Powerplay (1-6)", "Middle Overs (7-15)", "Death Overs (16-20)"]}
            )
            fig_ps_sr.update_layout(xaxis_title="", yaxis_title="Strike Rate",
                                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig_ps_sr, use_container_width=True)

        with c_phase2:
            fig_ps_bpct = px.bar(
                phase_compare_df, x='Phase', y='Boundary %', color='Player', barmode='group',
                text_auto='.1f', color_discrete_sequence=['#1f77b4', '#ff7f0e'],
                category_orders={"Phase": ["Powerplay (1-6)", "Middle Overs (7-15)", "Death Overs (16-20)"]}
            )
            fig_ps_bpct.update_layout(xaxis_title="", yaxis_title="Boundary Percentage (%)",
                                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig_ps_bpct, use_container_width=True)

        st.divider()

        # --- 4. NON-STRIKER INFLUENCE ---
        st.subheader("🤝 Partnership Dependency (Non-Striker Influence)")
        st.markdown(
            "Does having an aggressive partner help them score faster, or do they prefer batting with an anchor?")

        # Classify all league non-strikers (Min 150 career balls to qualify)
        legal_balls_all = t20_data[(t20_data['is_wide_ball'] == False) & (t20_data['is_no_ball'] == False)]
        career_runs = t20_data.groupby('batter')['batter_runs'].sum()
        career_balls = legal_balls_all.groupby('batter').size()

        valid_batters = career_balls[career_balls >= 150].index
        career_sr = ((career_runs / career_balls) * 100).dropna()
        career_sr = career_sr[career_sr.index.isin(valid_batters)]

        aggressive_ns = career_sr[career_sr >= 140].index
        anchor_ns = career_sr[career_sr < 140].index


        def get_influence_stats(target_batter):
            p_df = t20_data[(t20_data['batter'] == target_batter) & (t20_data['non_striker'].isin(valid_batters))]

            def calc_partner_sr(partner_list):
                partner_df = p_df[p_df['non_striker'].isin(partner_list)]
                r = partner_df['batter_runs'].sum()
                b = partner_df[(partner_df['is_wide_ball'] == False) & (partner_df['is_no_ball'] == False)].shape[0]
                # Require at least 20 legal balls faced with this partner type
                return (r / b * 100) if b >= 20 else 0

            return calc_partner_sr(aggressive_ns), calc_partner_sr(anchor_ns)


        a_agg_sr, a_anc_sr = get_influence_stats(player_A)
        b_agg_sr, b_anc_sr = get_influence_stats(player_B)

        influence_data = pd.DataFrame({
            "Player": [player_A, player_A, player_B, player_B],
            "Partner Style": ["With Aggressor (Career SR ≥ 140)", "With Anchor (Career SR < 140)",
                              "With Aggressor (Career SR ≥ 140)", "With Anchor (Career SR < 140)"],
            "Strike Rate": [a_agg_sr, a_anc_sr, b_agg_sr, b_anc_sr]
        })

        influence_data = influence_data[influence_data['Strike Rate'] > 0]

        if not influence_data.empty:
            fig_influence = px.bar(
                influence_data,
                x='Partner Style',
                y='Strike Rate',
                color='Player',
                barmode='group',
                text_auto='.1f',
                color_discrete_sequence=['#1f77b4', '#ff7f0e']
            )
            fig_influence.update_layout(yaxis_title="Strike Rate", xaxis_title="")
            
            # Center the final chart and restrict to half-width to match the column sizes above
            _, center_col, _ = st.columns([1, 2, 1])
            with center_col:
                st.plotly_chart(fig_influence, use_container_width=True)
        else:
            st.info("Not enough data to calculate partnership influence for these specific players.")



    # ----------------------------------------
    # TAB 2: BOWLERS
    # ----------------------------------------
        # ----------------------------------------
        # TAB 2: BOWLERS (ADVANCED SCOUTING)
        # ----------------------------------------
    # ----------------------------------------
    # TAB 2: BOWLERS (ADVANCED SCOUTING)
    # ----------------------------------------
    with tab_bowlers:
        st.header("Advanced Head-to-Head Bowler Comparison")
        st.markdown(
            "Evaluating bowlers using deep-dive metrics: pressure building, leakage control, phase-wise survival, and clutch performance.")

        bowler_list = sorted(t20_data['bowler'].unique())

        col1, col2 = st.columns(2)
        with col1:
            bowler_A = st.selectbox("Select Bowler A", bowler_list,
                                    index=bowler_list.index('JJ Bumrah') if 'JJ Bumrah' in bowler_list else 0,
                                    key="adv_bowl_a")
        with col2:
            bowler_B = st.selectbox("Select Bowler B", bowler_list,
                                    index=bowler_list.index('Rashid Khan') if 'Rashid Khan' in bowler_list else 1,
                                    key="adv_bowl_b")


        def get_advanced_bowler_stats(player_name):
            b_df = t20_data[t20_data['bowler'] == player_name].copy()
            legal_balls = b_df[(b_df['is_wide_ball'] == False) & (b_df['is_no_ball'] == False)]

            total_legal_balls = legal_balls.shape[0]
            # Bowlers are NOT penalized for byes and leg byes
            bowler_runs_df = b_df[(b_df['is_bye'] == False) & (b_df['is_leg_bye'] == False)]
            total_runs_conceded = bowler_runs_df['total_runs'].sum()
            overs = total_legal_balls / 6

            # Wickets logic
            valid_wickets_list = ['caught', 'bowled', 'lbw', 'stumped', 'caught and bowled', 'hit wicket']
            all_wickets_df = b_df[b_df['is_wicket'] == True]
            actual_wickets_df = all_wickets_df[all_wickets_df['wicket_kind'].isin(valid_wickets_list)]
            total_wickets = actual_wickets_df.shape[0]

            # 1. Standard Efficiency
            avg = total_runs_conceded / total_wickets if total_wickets > 0 else total_runs_conceded
            eco = total_runs_conceded / overs if overs > 0 else 0
            sr = total_legal_balls / total_wickets if total_wickets > 0 else 0

            # 2. Pressure & Leakage
            dots = b_df[b_df['total_runs'] == 0].shape[0]
            dot_pct = (dots / total_legal_balls) * 100 if total_legal_balls > 0 else 0

            boundaries = b_df[b_df['batter_runs'].isin([4, 6])].shape[0]
            boundary_pct = (boundaries / total_legal_balls) * 100 if total_legal_balls > 0 else 0

            # 3. Pure Skill (Bowled/LBW vs total wickets)
            pure_wickets = actual_wickets_df[actual_wickets_df['wicket_kind'].isin(['bowled', 'lbw'])].shape[0]
            pure_pct = (pure_wickets / total_wickets) * 100 if total_wickets > 0 else 0

            # 4. Phase Economies
            def phase_eco(phase):
                p_df = bowler_runs_df[bowler_runs_df['phase'] == phase]
                p_legal = legal_balls[legal_balls['phase'] == phase].shape[0]
                p_runs = p_df['total_runs'].sum()
                p_overs = p_legal / 6
                return p_runs / p_overs if p_overs > 0 else 0

            return {
                "Total Wickets": total_wickets, "Bowling Average": avg, "Economy Rate": eco,
                "Bowling Strike Rate": sr, "Dot Ball Percentage (%)": dot_pct,
                "Boundary Conceded (%)": boundary_pct, "Pure Wicket % (Bowled/LBW)": pure_pct,
                "Powerplay Economy": phase_eco('Powerplay (1-6)'),
                "Middle Overs Economy": phase_eco('Middle Overs (7-15)'),
                "Death Overs Economy": phase_eco('Death Overs (16-20)')
            }


        # Fetch stats
        b_stats_A = get_advanced_bowler_stats(bowler_A)
        b_stats_B = get_advanced_bowler_stats(bowler_B)

        # --- 1. TALE OF THE TAPE ---
        st.subheader("📊 Tale of the Tape")

        col_A, col_vs, col_B = st.columns([3, 2, 3])
        with col_A:
            st.markdown(f"<h3 style='text-align: center; color: #1f77b4;'>{bowler_A}</h3>", unsafe_allow_html=True)
        with col_vs:
            st.markdown("<h3 style='text-align: center; color: gray;'>VS</h3>", unsafe_allow_html=True)
        with col_B:
            st.markdown(f"<h3 style='text-align: center; color: #ff7f0e;'>{bowler_B}</h3>", unsafe_allow_html=True)

        st.markdown("<hr style='margin-top: 0; margin-bottom: 15px;'>", unsafe_allow_html=True)

        bowler_metrics = [
            ("Total Wickets", "Total Wickets"), ("Bowling Average", "Bowling Average"),
            ("Economy Rate", "Economy Rate"), ("Bowling Strike Rate", "Bowling Strike Rate"),
            ("Dot Ball Percentage (%)", "Dot Ball Percentage (%)"), ("Boundary Conceded (%)", "Boundary Conceded (%)"),
            ("Pure Wicket % (Bowled/LBW)", "Pure Wicket % (Bowled/LBW)"), ("Powerplay Economy", "Powerplay Economy"),
            ("Middle Overs Economy", "Middle Overs Economy"), ("Death Overs Economy", "Death Overs Economy")
        ]

        for display_name, dict_key in bowler_metrics:
            cA, cM, cB = st.columns([3, 2, 3])

            val_A = b_stats_A[dict_key]
            val_B = b_stats_B[dict_key]
            if isinstance(val_A, float): val_A = f"{val_A:.2f}"
            if isinstance(val_B, float): val_B = f"{val_B:.2f}"
            if isinstance(val_A, int): val_A = str(val_A)
            if isinstance(val_B, int): val_B = str(val_B)

            cA.markdown(f"<h4 style='text-align: center; margin: 0;'>{val_A}</h4>", unsafe_allow_html=True)
            cM.markdown(
                f"<p style='text-align: center; color: #888; font-size: 14px; font-weight: bold; margin: 0;'>{display_name}</p>",
                unsafe_allow_html=True)
            cB.markdown(f"<h4 style='text-align: center; margin: 0;'>{val_B}</h4>", unsafe_allow_html=True)

            st.markdown("<hr style='margin-top: 10px; margin-bottom: 10px; opacity: 0.2;'>", unsafe_allow_html=True)

        st.divider()

        # --- 2. MATCH-UP & PHASE CHARTS ---
        col3, col4 = st.columns(2)

        with col3:
            st.subheader("🎯 Wicket Distribution (Phase)")
            st.markdown("Where do they strike the most?")

            valid_wickets = ['caught', 'bowled', 'lbw', 'stumped', 'caught and bowled', 'hit wicket']
            w_df = t20_data[(t20_data['is_wicket'] == True) & (t20_data['wicket_kind'].isin(valid_wickets))]


            def get_wicket_dist(name):
                df = w_df[w_df['bowler'] == name]
                dist = df['phase'].value_counts().reset_index()
                dist.columns = ['Phase', 'Wickets']
                dist['Player'] = name
                return dist


            combined_dist = pd.concat([get_wicket_dist(bowler_A), get_wicket_dist(bowler_B)])
            fig_w_phase = px.bar(
                combined_dist, x='Phase', y='Wickets', color='Player', barmode='group',
                category_orders={"Phase": ["Powerplay (1-6)", "Middle Overs (7-15)", "Death Overs (16-20)"]},
                text_auto=True, color_discrete_sequence=['#1f77b4', '#ff7f0e']
            )
            fig_w_phase.update_layout(showlegend=False)
            st.plotly_chart(fig_w_phase, use_container_width=True)

        with col4:
            st.subheader("🕸️ Phase Survival DNA (Economy)")
            st.markdown("**Note:** Smaller footprint = better economy.")

            radar_metrics_b = ['Powerplay Economy', 'Middle Overs Economy', 'Death Overs Economy', 'Economy Rate']

            radar_df_b = pd.DataFrame({
                'Metric': [m.replace(' Economy', ' Eco').replace('Rate', 'Overall') for m in radar_metrics_b] * 2,
                'Economy': [b_stats_A[m] for m in radar_metrics_b] + [b_stats_B[m] for m in radar_metrics_b],
                'Player': [bowler_A] * 4 + [bowler_B] * 4
            })

            max_r = min(max(radar_df_b['Economy'].max() + 2, 12), 18)

            fig_radar_b = px.line_polar(
                radar_df_b, r='Economy', theta='Metric', color='Player',
                line_close=True, color_discrete_sequence=['#1f77b4', '#ff7f0e'],
                range_r=[0, max_r]
            )
            fig_radar_b.update_traces(fill='toself', opacity=0.4)
            st.plotly_chart(fig_radar_b, use_container_width=True)

        st.divider()

        # --- 3. CLUTCH & PRESSURE DYNAMICS ---
        st.subheader("🔥 Clutch & Pressure Dynamics")
        st.markdown(
            "Evaluating how these bowlers handle scoreboard pressure in the Death Overs, and the true quality of the wickets they take.")

        c_clutch1, c_clutch2 = st.columns(2)


        # Function to calculate Scoreboard Pressure (Dot % in Death Overs)
        def get_scoreboard_pressure(name):
            pressure_df = t20_data[(t20_data['bowler'] == name) &
                              (t20_data['phase'] == 'Death Overs (16-20)') &
                              (t20_data['innings'].isin([1, 2]))]

            if pressure_df.empty:
                return pd.DataFrame()

            total_balls = pressure_df.groupby('innings').size().reset_index(name='Total Balls')
            dot_balls = pressure_df[pressure_df['total_runs'] == 0].groupby('innings').size().reset_index(
                name='Dot Balls')

            stats = pd.merge(total_balls, dot_balls, on='innings', how='left').fillna(0)
            stats['Dot Ball %'] = (stats['Dot Balls'] / stats['Total Balls']) * 100
            stats['Context'] = stats['innings'].map({1: 'Setting Target (1st Inn)', 2: 'Defending Target (2nd Inn)'})
            stats['Player'] = name
            return stats[['Player', 'Context', 'Dot Ball %']]


        # Function to calculate Wicket Quality
        def get_wicket_quality(name):
            w_df = t20_data[(t20_data['bowler'] == name) & (t20_data['is_wicket'] == True)].copy()

            def categorize(w_kind):
                if w_kind in ['bowled', 'lbw']:
                    return 'Bowled / LBW (Skill)'
                elif w_kind in ['caught', 'caught and bowled']:
                    return 'Caught (Mistake)'
                return 'Other'

            w_df['Quality'] = w_df['wicket_kind'].apply(categorize)
            valid_df = w_df[w_df['Quality'] != 'Other']

            counts = valid_df['Quality'].value_counts().reset_index()
            counts.columns = ['Wicket Quality', 'Count']
            total = counts['Count'].sum()
            counts['Percentage'] = (counts['Count'] / total * 100) if total > 0 else 0
            counts['Player'] = name
            return counts[['Player', 'Wicket Quality', 'Percentage']]


        with c_clutch1:
            pressure_A = get_scoreboard_pressure(bowler_A)
            pressure_B = get_scoreboard_pressure(bowler_B)
            combined_pressure = pd.concat([pressure_A, pressure_B])

            if not combined_pressure.empty:
                fig_pressure = px.bar(
                    combined_pressure, x='Context', y='Dot Ball %', color='Player',
                    barmode='group', text_auto='.1f', color_discrete_sequence=['#1f77b4', '#ff7f0e'],
                    title="Death Overs Dot % (Scoreboard Pressure)"
                )
                fig_pressure.update_layout(xaxis_title="", yaxis_title="Dot Ball Percentage (%)",
                                           legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig_pressure, use_container_width=True)
            else:
                st.info("Not enough Death Overs data to evaluate scoreboard pressure.")

        with c_clutch2:
            wq_A = get_wicket_quality(bowler_A)
            wq_B = get_wicket_quality(bowler_B)
            combined_wq = pd.concat([wq_A, wq_B])

            if not combined_wq.empty:
                fig_wq = px.bar(
                    combined_wq, x='Wicket Quality', y='Percentage', color='Player',
                    barmode='group', text_auto='.1f', color_discrete_sequence=['#1f77b4', '#ff7f0e'],
                    title="Wicket Quality Assessment"
                )
                fig_wq.update_layout(xaxis_title="", yaxis_title="% of Total Wickets",
                                     legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig_wq, use_container_width=True)
            else:
                st.info("Not enough wicket data to evaluate quality.")




# ==========================================
# PAGE 5: IN-DEPTH MATCH ANALYTICS
# ==========================================
elif menu == "In-Depth Match Analytics":
    st.title("In-Depth Match Analytics")


    st.subheader("Total Sixes Hit per Season")

    # 1. Group the data to count sixes per season
    sixes_in_each_season = t20_data[t20_data['batter_runs'] == 6].groupby('season_id').size().reset_index(name='sixes')

    # 2. Create a clean, standalone Plotly bar chart
    fig_sixes = px.bar(
        sixes_in_each_season,
        x='season_id',
        y='sixes',
        text_auto=True,  # Adds the exact number of sixes on top of each bar
        color_discrete_sequence=['#FF4B4B'],
        labels={'season_id': 'Season', 'sixes': 'Total Sixes'}
    )

    # 3. Force the x-axis to treat seasons as distinct categories (prevents decimal years like 2018.5)
    fig_sixes.update_layout(xaxis=dict(type='category'))

    # 4. Display the chart at full width without the dataframe
    st.plotly_chart(fig_sixes, use_container_width=True)

    st.divider()
    st.subheader("Extras Breakdown: The Discipline Metric")
    st.markdown(
        " **Average number of extra runs** a team gifts to the opposition per match, broken down by type.")

    # 1. Calculate total extras by type for each bowling team (ignoring penalty balls as they are incredibly rare)
    extras_df = t20_data.groupby('team_bowling')[['is_wide_ball', 'is_no_ball', 'is_leg_bye', 'is_bye']].sum().reset_index()

    # 2. Calculate the total matches played by each bowling team to normalize the data
    matches_bowled = t20_data.groupby('team_bowling')['match_id'].nunique().reset_index(name='Matches')

    # 3. Merge and calculate the average per match
    discipline_df = pd.merge(extras_df, matches_bowled, on='team_bowling')

    for col in ['is_wide_ball', 'is_no_ball', 'is_leg_bye', 'is_bye']:
        discipline_df[col] = discipline_df[col] / discipline_df['Matches']

    # 4. Rename columns for a clean legend
    discipline_df = discipline_df.rename(columns={
        'is_wide_ball': 'Wides',
        'is_no_ball': 'No Balls',
        'is_leg_bye': 'Leg Byes',
        'is_bye': 'Byes',
        'team_bowling': 'Team'
    })

    # 5. Create the upgraded stacked bar chart
    fig_extras = px.bar(
        discipline_df,
        x='Team',
        y=['Wides', 'No Balls', 'Leg Byes', 'Byes'],
        labels={'value': 'Average Extra Runs Per Match', 'variable': 'Extra Type'},
        color_discrete_sequence=['#1f77b4', '#d62728', '#2ca02c', '#ff7f0e'],  # Custom distinct colors
        text_auto='.1f'  # Shows 1 decimal place on the chart segments
    )

    # 6. Sort from most undisciplined (highest extras) to most disciplined
    fig_extras.update_layout(xaxis={'categoryorder': 'total descending'})

    st.plotly_chart(fig_extras, use_container_width=True)

    st.divider()
    st.subheader("The Evolution of Intent (Run Rate by Phase)")


    # 1. Calculate Total Runs per Phase per Season
    phase_runs = t20_data.groupby(['season_id', 'phase'])['total_runs'].sum().reset_index()

    # 2. Calculate Total LEGAL Overs per Phase per Season
    legal_balls = t20_data[(t20_data['is_wide_ball'] == False) & (t20_data['is_no_ball'] == False)]
    phase_balls = legal_balls.groupby(['season_id', 'phase']).size().reset_index(name='legal_balls')
    phase_balls['overs'] = phase_balls['legal_balls'] / 6

    # 3. Merge and Calculate Run Rate
    rr_df = pd.merge(phase_runs, phase_balls, on=['season_id', 'phase'])
    rr_df['run_rate'] = rr_df['total_runs'] / rr_df['overs']

    # 4. Create a Presentation-Quality Smoothed Line Chart
    fig_rr = px.line(
        rr_df,
        x="season_id",
        y="run_rate",
        color="phase",
        markers=True,
        category_orders={"phase": ["Powerplay (1-6)", "Middle Overs (7-15)", "Death Overs (16-20)"]},
        color_discrete_map={
            "Powerplay (1-6)": "#1f77b4",  # Professional Blue
            "Middle Overs (7-15)": "#ff7f0e",  # Warning Orange
            "Death Overs (16-20)": "#d62728"  # Danger Red
        },
        labels={'run_rate': 'Run Rate (Runs per Over)', 'season_id': 'Season', 'phase': 'Match Phase'}
    )

    # 5. Apply sleek formatting (Spline curves, unified hover tooltips)
    fig_rr.update_traces(line_shape='spline', line=dict(width=3), marker=dict(size=8))
    fig_rr.update_layout(
        hovermode="x unified",  # Shows all 3 phases in one clean box when hovering over a year
        xaxis=dict(tickmode='linear', dtick=1),  # Forces every single year to show on the X-axis
        yaxis_title="Run Rate (RPO)",
        legend=dict(title=None, orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        # Puts legend cleanly on top
    )

    st.plotly_chart(fig_rr, use_container_width=True)

    # ==========================================
    # HEAD-TO-HEAD: ULTIMATE TEAM CLASH
    # ==========================================
    st.header("⚔️ Ultimate Head-to-Head: Team Clash")
    st.markdown(
        "Dive deep into the historical rivalry. This module isolates every ball ever bowled between these two specific franchises to reveal their true matchup DNA.")

    team_list = sorted(t20_data['team_batting'].dropna().unique())

    col1, col2 = st.columns(2)
    with col1:
        team_A = st.selectbox("Select Team A", team_list,
                              index=team_list.index('Mumbai Indians') if 'Mumbai Indians' in team_list else 0,
                              key="h2h_team_a")
    with col2:
        # Default Team B to CSK if available
        default_b_idx = team_list.index('Chennai Super Kings') if 'Chennai Super Kings' in team_list else 1
        # Prevent selecting the same team twice
        if team_A == team_list[default_b_idx]: default_b_idx = (default_b_idx + 1) % len(team_list)
        team_B = st.selectbox("Select Team B", team_list, index=default_b_idx, key="h2h_team_b")

    if team_A == team_B:
        st.warning("Please select two different teams for a Head-to-Head comparison.")
    else:
        # --- 1. DATA ISOLATION (Filter for ONLY matches between A and B) ---
        # Assuming your matches dataset has 'team1' and 'team2' columns
        h2h_matches = matches[((matches['team1'] == team_A) & (matches['team2'] == team_B)) |
                              ((matches['team1'] == team_B) & (matches['team2'] == team_A))]

        if h2h_matches.empty:
            st.info(f"No historical matches found between {team_A} and {team_B}.")
        else:
            h2h_match_ids = h2h_matches['match_id'].unique()
            h2h_t20_data = t20_data[t20_data['match_id'].isin(h2h_match_ids)].copy()


            # --- 2. MASTER CALCULATION FUNCTION ---
            def get_team_h2h_stats(team_name, opp_name):
                # Batting stats (Team batting)
                bat_df = h2h_t20_data[h2h_t20_data['team_batting'] == team_name]
                legal_bat = bat_df[(bat_df['is_wide_ball'] == False) & (bat_df['is_no_ball'] == False)]

                # Bowling stats (Team bowling)
                bowl_df = h2h_t20_data[h2h_t20_data['team_bowling'] == team_name]
                legal_bowl = bowl_df[(bowl_df['is_wide_ball'] == False) & (bowl_df['is_no_ball'] == False)]

                total_matches = len(h2h_match_ids)
                wins = h2h_matches[h2h_matches['match_winner'] == team_name].shape[0]

                # Bat First vs Chase Wins
                bat_first_wins = h2h_matches[(h2h_matches['match_winner'] == team_name) &
                                             (((h2h_matches['toss_winner'] == team_name) & (
                                                         h2h_matches['toss_decision'] == 'bat')) |
                                              ((h2h_matches['toss_winner'] == opp_name) & (
                                                          h2h_matches['toss_decision'] == 'field')))].shape[0]
                chase_wins = wins - bat_first_wins

                # Innings Totals
                match_totals = bat_df.groupby('match_id')['total_runs'].sum()
                high_score = match_totals.max() if not match_totals.empty else 0
                low_score = match_totals.min() if not match_totals.empty else 0
                avg_score = match_totals.mean() if not match_totals.empty else 0

                # Batting Efficiency
                runs_scored = bat_df['total_runs'].sum()
                balls_faced = legal_bat.shape[0]
                wickets_lost = bat_df[bat_df['is_wicket'] == True].shape[0]
                bounds_hit = bat_df[bat_df['batter_runs'].isin([4, 6])]['total_runs'].sum()
                dots_faced = bat_df[bat_df['total_runs'] == 0].shape[0]

                bat_rr = (runs_scored / balls_faced) * 6 if balls_faced > 0 else 0
                bound_pct = (bounds_hit / runs_scored) * 100 if runs_scored > 0 else 0
                bat_dot_pct = (dots_faced / balls_faced) * 100 if balls_faced > 0 else 0
                bpw = balls_faced / wickets_lost if wickets_lost > 0 else balls_faced

                # Bowling Discipline
                runs_conceded = bowl_df['total_runs'].sum()
                balls_bowled = legal_bowl.shape[0]
                wickets_taken = bowl_df[(bowl_df['is_wicket'] == True) & (bowl_df['wicket_kind'].isin(
                    ['caught', 'bowled', 'lbw', 'stumped', 'caught and bowled', 'hit wicket']))].shape[0]
                dots_bowled = bowl_df[bowl_df['total_runs'] == 0].shape[0]
                extras_conceded = bowl_df[(bowl_df['is_wide_ball'] == True) | (bowl_df['is_no_ball'] == True)].shape[0]

                bowl_eco = (runs_conceded / balls_bowled) * 6 if balls_bowled > 0 else 0
                bowl_sr = balls_bowled / wickets_taken if wickets_taken > 0 else 0
                bowl_dot_pct = (dots_bowled / balls_bowled) * 100 if balls_bowled > 0 else 0
                extras_per_match = extras_conceded / total_matches if total_matches > 0 else 0

                # Tactical: Phase RR & Eco
                def phase_stats(df, phase_name, is_batting):
                    p_df = df[df['phase'] == phase_name]
                    p_legal = p_df[(p_df['is_wide_ball'] == False) & (p_df['is_no_ball'] == False)].shape[0]
                    p_runs = p_df['total_runs'].sum()
                    return (p_runs / p_legal) * 6 if p_legal > 0 else 0

                # Tactical: Pace vs Spin
                def matchup_stats(df, b_type_keyword, is_batting):
                    if 'bowler_type' in df.columns:
                        m_df = df[df['bowler_type'].astype(str).str.contains(b_type_keyword, case=False, na=False)]
                        m_legal = m_df[(m_df['is_wide_ball'] == False) & (m_df['is_no_ball'] == False)].shape[0]
                        m_runs = m_df['total_runs'].sum()
                        return (m_runs / m_legal) * 6 if m_legal > 0 else 0
                    return 0

                return {
                    "Wins": wins, "Bat First Wins": bat_first_wins, "Chase Wins": chase_wins,
                    "Highest Total": high_score, "Lowest Total": low_score, "Average Total": avg_score,
                    "Run Rate": bat_rr, "Boundary %": bound_pct, "Bat Dot %": bat_dot_pct, "Balls/Wicket": bpw,
                    "Economy": bowl_eco, "Bowling SR": bowl_sr, "Bowl Dot %": bowl_dot_pct,
                    "Extras/Match": extras_per_match,
                    "PP RR": phase_stats(bat_df, 'Powerplay (1-6)', True),
                    "Mid RR": phase_stats(bat_df, 'Middle Overs (7-15)', True),
                    "Death RR": phase_stats(bat_df, 'Death Overs (16-20)', True),
                    "PP Eco": phase_stats(bowl_df, 'Powerplay (1-6)', False),
                    "Mid Eco": phase_stats(bowl_df, 'Middle Overs (7-15)', False),
                    "Death Eco": phase_stats(bowl_df, 'Death Overs (16-20)', False),
                    "Bat vs Pace RR": matchup_stats(bat_df, 'fast|medium|pace', True),
                    "Bat vs Spin RR": matchup_stats(bat_df, 'spin|break|orthodox|chinaman|googly', True)
                }


            stats_A = get_team_h2h_stats(team_A, team_B)
            stats_B = get_team_h2h_stats(team_B, team_A)

            # Colors
            color_A = '#1f77b4'  # Blue
            color_B = '#ff7f0e'  # Orange

            # --- 3. UI RENDER: THE TALE OF THE TAPE ---
            st.divider()
            st.markdown(f"<h3 style='text-align: center; color: #555;'>Total Matches Played: {len(h2h_match_ids)}</h3>",
                        unsafe_allow_html=True)

            c_A, c_vs, c_B = st.columns([3, 1, 3])
            c_A.markdown(f"<h2 style='text-align: center; color: {color_A}; margin-bottom: 0;'>{team_A}</h2>",
                         unsafe_allow_html=True)
            c_A.markdown(
                f"<h1 style='text-align: center; color: {color_A}; font-size: 60px; margin-top: 0;'>{stats_A['Wins']}</h1>",
                unsafe_allow_html=True)

            c_vs.markdown("<h3 style='text-align: center; color: gray; margin-top: 40px;'>WINS</h3>",
                          unsafe_allow_html=True)

            c_B.markdown(f"<h2 style='text-align: center; color: {color_B}; margin-bottom: 0;'>{team_B}</h2>",
                         unsafe_allow_html=True)
            c_B.markdown(
                f"<h1 style='text-align: center; color: {color_B}; font-size: 60px; margin-top: 0;'>{stats_B['Wins']}</h1>",
                unsafe_allow_html=True)


            # Helper function for rendering HTML stat rows
            def render_stat_row(label, key_A, key_B, is_float=False):
                val_A = f"{stats_A[key_A]:.1f}" if is_float else str(int(stats_A[key_A]))
                val_B = f"{stats_B[key_B]:.1f}" if is_float else str(int(stats_B[key_B]))

                cA, cM, cB = st.columns([3, 2, 3])
                cA.markdown(f"<h4 style='text-align: center; margin: 0; color: {color_A};'>{val_A}</h4>",
                            unsafe_allow_html=True)
                cM.markdown(
                    f"<p style='text-align: center; color: #888; font-size: 14px; font-weight: bold; margin: 0;'>{label}</p>",
                    unsafe_allow_html=True)
                cB.markdown(f"<h4 style='text-align: center; margin: 0; color: {color_B};'>{val_B}</h4>",
                            unsafe_allow_html=True)
                st.markdown("<hr style='margin-top: 5px; margin-bottom: 10px; opacity: 0.1;'>", unsafe_allow_html=True)


            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### 🏛️ Historical Context")
            render_stat_row("Bat First Wins", "Bat First Wins", "Bat First Wins")
            render_stat_row("Chasing Wins", "Chase Wins", "Chase Wins")
            render_stat_row("Highest Total", "Highest Total", "Highest Total")
            render_stat_row("Average Total", "Average Total", "Average Total", is_float=True)

            st.markdown("#### 🏏 Batting Efficiency")
            render_stat_row("Overall Run Rate", "Run Rate", "Run Rate", is_float=True)
            render_stat_row("Boundary Reliance (%)", "Boundary %", "Boundary %", is_float=True)
            render_stat_row("Dot Ball Faced (%)", "Bat Dot %", "Bat Dot %", is_float=True)
            render_stat_row("Balls Per Wicket", "Balls/Wicket", "Balls/Wicket", is_float=True)

            st.markdown("#### 🎯 Bowling Discipline")
            render_stat_row("Overall Economy", "Economy", "Economy", is_float=True)
            render_stat_row("Bowling Strike Rate", "Bowling SR", "Bowling SR", is_float=True)
            render_stat_row("Dot Balls Bowled (%)", "Bowl Dot %", "Bowl Dot %", is_float=True)
            render_stat_row("Extras Per Match", "Extras/Match", "Extras/Match", is_float=True)

            # --- 4. TACTICAL VISUALIZATIONS ---
            st.divider()
            st.subheader("🧠 Tactical & Situational Breakdown")

            t_col1, t_col2 = st.columns(2)

            with t_col1:
                # Batting Phase Radar
                st.markdown("**Phase-wise Scoring Rate (Run Rate)**")
                radar_rr = pd.DataFrame([
                    {'Team': team_A, 'Phase': 'Powerplay', 'RR': stats_A['PP RR']},
                    {'Team': team_A, 'Phase': 'Middle Overs', 'RR': stats_A['Mid RR']},
                    {'Team': team_A, 'Phase': 'Death Overs', 'RR': stats_A['Death RR']},
                    {'Team': team_B, 'Phase': 'Powerplay', 'RR': stats_B['PP RR']},
                    {'Team': team_B, 'Phase': 'Middle Overs', 'RR': stats_B['Mid RR']},
                    {'Team': team_B, 'Phase': 'Death Overs', 'RR': stats_B['Death RR']}
                ])
                fig_rr_radar = px.line_polar(
                    radar_rr, r='RR', theta='Phase', color='Team', line_close=True,
                    color_discrete_map={team_A: color_A, team_B: color_B},
                    range_r=[0, max(12, radar_rr['RR'].max() + 1)]
                )
                fig_rr_radar.update_traces(fill='toself', opacity=0.4)
                fig_rr_radar.update_layout(
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
                st.plotly_chart(fig_rr_radar, use_container_width=True)

            with t_col2:
                # Bowling Phase Radar (Lower is better)
                st.markdown("**Phase-wise Restriction (Economy Rate)**")
                radar_eco = pd.DataFrame([
                    {'Team': team_A, 'Phase': 'Powerplay', 'Eco': stats_A['PP Eco']},
                    {'Team': team_A, 'Phase': 'Middle Overs', 'Eco': stats_A['Mid Eco']},
                    {'Team': team_A, 'Phase': 'Death Overs', 'Eco': stats_A['Death Eco']},
                    {'Team': team_B, 'Phase': 'Powerplay', 'Eco': stats_B['PP Eco']},
                    {'Team': team_B, 'Phase': 'Middle Overs', 'Eco': stats_B['Mid Eco']},
                    {'Team': team_B, 'Phase': 'Death Overs', 'Eco': stats_B['Death Eco']}
                ])
                fig_eco_radar = px.line_polar(
                    radar_eco, r='Eco', theta='Phase', color='Team', line_close=True,
                    color_discrete_map={team_A: color_A, team_B: color_B},
                    range_r=[0, max(12, radar_eco['Eco'].max() + 1)]
                )
                fig_eco_radar.update_traces(fill='toself', opacity=0.4)
                fig_eco_radar.update_layout(
                    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
                st.plotly_chart(fig_eco_radar, use_container_width=True)

            # Matchups & Wicket Distribution Bars
            t_col3, t_col4 = st.columns(2)

            with t_col3:
                st.markdown("**Pace vs Spin Dominance (Run Rate)**")
                matchup_df = pd.DataFrame([
                    {'Team': team_A, 'Bowling Type': 'Pace', 'Run Rate': stats_A['Bat vs Pace RR']},
                    {'Team': team_A, 'Bowling Type': 'Spin', 'Run Rate': stats_A['Bat vs Spin RR']},
                    {'Team': team_B, 'Bowling Type': 'Pace', 'Run Rate': stats_B['Bat vs Pace RR']},
                    {'Team': team_B, 'Bowling Type': 'Spin', 'Run Rate': stats_B['Bat vs Spin RR']}
                ])
                fig_matchup = px.bar(
                    matchup_df, x='Team', y='Run Rate', color='Bowling Type', barmode='group',
                    color_discrete_sequence=['#d62728', '#2ca02c'], text_auto='.1f'
                )
                fig_matchup.update_layout(xaxis_title="",
                                          legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig_matchup, use_container_width=True)

            with t_col4:
                st.markdown("**Wicket Distribution (When do they strike?)**")
                # Grabbing the valid wickets taken by each team in H2H
                valid_w = ['caught', 'bowled', 'lbw', 'stumped', 'caught and bowled', 'hit wicket']
                h2h_wickets = h2h_t20_data[(h2h_t20_data['is_wicket'] == True) & (h2h_t20_data['wicket_kind'].isin(valid_w))].copy()

                # We group by the bowling team and the phase they took the wicket in
                w_dist = h2h_wickets.groupby(['team_bowling', 'phase']).size().reset_index(name='Wickets')

                fig_w_dist = px.bar(
                    w_dist, x='team_bowling', y='Wickets', color='phase', barmode='stack',
                    category_orders={"phase": ["Powerplay (1-6)", "Middle Overs (7-15)", "Death Overs (16-20)"]},
                    color_discrete_map={"Powerplay (1-6)": "#1f77b4", "Middle Overs (7-15)": "#ff7f0e",
                                        "Death Overs (16-20)": "#2ca02c"},
                    text_auto=True
                )
                fig_w_dist.update_layout(xaxis_title="",
                                         legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig_w_dist, use_container_width=True)














# ==========================================
# PAGE 6: MODERN META ANALYTICS
# ==========================================
elif menu == "Modern Meta Analytics":
    st.title("Modern Meta Analytics (2023-2025)")

    st.divider()

    # --- 1. THE RUN INFLATION (ALL-TIME VS MODERN ERA) ---
    st.header("The Run Inflation: Average 1st Innings Score")
    st.markdown(
        "A historical view showing how modern rules (like the Impact Player) triggered an explosion in 1st innings totals.")

    # 1. Use the FULL 't20_data' dataset to calculate the historical trend
    first_innings_all = t20_data[t20_data['innings'] == 1].groupby(['season_id', 'match_id'])['total_runs'].sum().reset_index()
    avg_score_history = first_innings_all.groupby('season_id')['total_runs'].mean().reset_index()
    avg_score_history['total_runs'] = avg_score_history['total_runs'].round(1)

    # 2. Create a sleek Line + Area chart
    fig_inflation = px.line(
        avg_score_history,
        x='season_id',
        y='total_runs',
        markers=True,
        text='total_runs',
        labels={'total_runs': 'Average Score', 'season_id': 'Season'}
    )

    # 3. Professional Styling & Accents
    fig_inflation.update_traces(
        line_shape='spline',  # Smooth curves instead of jagged lines
        line=dict(color='#d62728', width=3),  # Bold red line
        marker=dict(size=8, color='white', line=dict(width=2, color='#d62728')),  # Custom distinct dots
        textposition="top center",
        fill='tozeroy',  # Creates the area chart effect
        fillcolor='rgba(214, 39, 40, 0.1)'  # A subtle, translucent red gradient below the line
    )

    # 4. Highlight the "Modern Meta" (2023+) with a background block
    # We use 2022.5 to start the highlight slightly before the 2023 dot for a clean look
    fig_inflation.add_vrect(
        x0=2022.5, x1=max(avg_score_history['season_id']) + 0.5,
        fillcolor="#ff7f0e", opacity=0.15,
        layer="below", line_width=0,
        annotation_text="🔥 Impact Player Era", annotation_position="top left",
        annotation_font_size=14, annotation_font_color="#ff7f0e"
    )

    # 5. Clean up the axes
    fig_inflation.update_layout(
        xaxis=dict(tickmode='linear', dtick=1),  # Force every single year to display on the X-axis
        yaxis_range=[130, max(avg_score_history['total_runs']) + 15],  # Lock Y-axis so the bottom isn't zero
        hovermode="x unified",
        margin=dict(t=30)
    )

    st.plotly_chart(fig_inflation, use_container_width=True)




    st.header("The Two-Bouncer Rule: Death Overs Survival")
    death_pace = new_t20_data[(new_t20_data['phase'] == 'Death Overs (16-20)') & (
        new_t20_data['bowler_type'].astype(str).str.lower().str.contains('fast|medium|pace', na=False))]


    def get_pace_stats(df, year):
        year_data = df[df['season_id'] == year]
        if year_data.empty: return 0, 0
        legal_balls = year_data[(year_data['is_wide_ball'] == False) & (year_data['is_no_ball'] == False)].shape[0]
        dot_balls = year_data[year_data['total_runs'] == 0].shape[0]
        runs_conceded = year_data['total_runs'].sum()
        return (dot_balls / legal_balls) * 100 if legal_balls > 0 else 0, (
                                                                                      runs_conceded / legal_balls) * 6 if legal_balls > 0 else 0


    dot_23, eco_23 = get_pace_stats(death_pace, 2023)
    dot_24, eco_24 = get_pace_stats(death_pace, 2024)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("2023 (One Bouncer)")
        st.metric("Pace Death Economy", f"{eco_23:.2f}")
        st.metric("Pace Death Dot Ball %", f"{dot_23:.1f}%")
    with col2:
        st.subheader("2024 (Two Bouncers)")
        st.metric("Pace Death Economy", f"{eco_24:.2f}", delta=f"{eco_24 - eco_23:.2f}", delta_color="inverse")
        st.metric("Pace Death Dot Ball %", f"{dot_24:.1f}%", delta=f"{dot_24 - dot_23:.1f}%")

    st.divider()



    # --- 3. THE INTENT MATRIX & GEAR-SHIFTING ---
    st.header("The Intent Matrix & Acceleration Curves")

    # 1. Prepare the Ball-by-Ball Sequence Data
    legal_t20_data = new_t20_data[(new_t20_data['is_wide_ball'] == False) & (new_t20_data['is_no_ball'] == False)].copy()
    legal_t20_data['batter_ball_number'] = legal_t20_data.groupby(['match_id', 'batter']).cumcount() + 1

    # 2. Calculate the League-Wide Matrix Data
    # Split into Initial (1-10) and Settled (11+)
    legal_t20_data['Intent Phase'] = np.where(legal_t20_data['batter_ball_number'] <= 10, 'Initial SR (Balls 1-10)',
                                         'Settled SR (Balls 11+)')

    # Calculate Runs and Balls per batter per phase
    matrix_runs = legal_t20_data.groupby(['batter', 'Intent Phase'])['batter_runs'].sum().unstack(fill_value=0)
    matrix_balls = legal_t20_data.groupby(['batter', 'Intent Phase']).size().unstack(fill_value=0)

    # Filter for batters with enough data (e.g., faced at least 30 initial balls and 30 settled balls in the modern era)
    valid_matrix_batters = matrix_balls[
        (matrix_balls['Initial SR (Balls 1-10)'] >= 30) & (matrix_balls['Settled SR (Balls 11+)'] >= 30)].index

    matrix_runs = matrix_runs.loc[valid_matrix_batters]
    matrix_balls = matrix_balls.loc[valid_matrix_batters]

    # Calculate Strike Rates
    matrix_sr = (matrix_runs / matrix_balls) * 100
    matrix_sr['Total Runs'] = matrix_runs['Initial SR (Balls 1-10)'] + matrix_runs['Settled SR (Balls 11+)']
    matrix_sr = matrix_sr.dropna().reset_index()

    # Calculate Medians to draw the Quadrant lines
    med_initial = matrix_sr['Initial SR (Balls 1-10)'].median()
    med_settled = matrix_sr['Settled SR (Balls 11+)'].median()

    # --- PART A: THE QUADRANT SCATTER PLOT ---
    st.subheader("League-Wide Intent Matrix (2023-2025)")


    fig_matrix = px.scatter(
        matrix_sr,
        x='Initial SR (Balls 1-10)',
        y='Settled SR (Balls 11+)',
        size='Total Runs',  # Bubble size reflects total runs scored
        color='Initial SR (Balls 1-10)',  # Color scale based on how fast they start
        color_continuous_scale='Inferno',
        hover_name='batter',
        labels={'Initial SR (Balls 1-10)': 'Initial Strike Rate (Balls 1-10)',
                'Settled SR (Balls 11+)': 'Settled Strike Rate (Balls 11+)'}
    )

    # Draw the Quadrant Crosshairs
    fig_matrix.add_hline(y=med_settled, line_dash="dash", line_color="gray", opacity=0.5)
    fig_matrix.add_vline(x=med_initial, line_dash="dash", line_color="gray", opacity=0.5)

    # Add subtle annotations for the quadrants
    fig_matrix.add_annotation(x=max(matrix_sr['Initial SR (Balls 1-10)']), y=max(matrix_sr['Settled SR (Balls 11+)']),
                              text="Elite Aggressors", showarrow=False, font=dict(color="green"), opacity=0.5)
    fig_matrix.add_annotation(x=min(matrix_sr['Initial SR (Balls 1-10)']), y=max(matrix_sr['Settled SR (Balls 11+)']),
                              text="Classic Anchors", showarrow=False, font=dict(color="white"), opacity=0.5)

    fig_matrix.update_layout(height=500, margin=dict(t=20))
    st.plotly_chart(fig_matrix, use_container_width=True)

    # --- PART B: THE PLAYER DEEP DIVE ---
    st.subheader("Player Gear-Shift Profile")

    dropdown_intent_batters = sorted(matrix_sr['batter'].unique())
    selected_intent_batter = st.selectbox("Select a Batter to view their acceleration curve:", dropdown_intent_batters,
                                          index=dropdown_intent_batters.index(
                                              'H Klaasen') if 'H Klaasen' in dropdown_intent_batters else 0)

    # Fetch stats for the selected player from our matrix
    player_matrix_data = matrix_sr[matrix_sr['batter'] == selected_intent_batter].iloc[0]
    init_sr = player_matrix_data['Initial SR (Balls 1-10)']
    set_sr = player_matrix_data['Settled SR (Balls 11+)']
    delta = set_sr - init_sr

    col_metrics1, col_metrics2, col_metrics3 = st.columns(3)
    with col_metrics1:
        st.metric("Initial SR (Balls 1-10)", f"{init_sr:.1f}")
    with col_metrics2:
        st.metric("Settled SR (Balls 11+)", f"{set_sr:.1f}")
    with col_metrics3:
        st.metric("Acceleration Delta", f"{delta:+.1f}", delta=f"{delta:+.1f}",
                  delta_color="normal" if delta > 0 else "inverse")


    # Generate the Gear-Shift Curve (10-ball brackets)
    def get_bracket(ball_num):
        if ball_num <= 10:
            return '1. First 10'
        elif ball_num <= 20:
            return '2. 11-20'
        elif ball_num <= 30:
            return '3. 21-30'
        else:
            return '4. 31+'


    player_balls = legal_t20_data[legal_t20_data['batter'] == selected_intent_batter].copy()
    player_balls['Bracket'] = player_balls['batter_ball_number'].apply(get_bracket)

    bracket_runs = player_balls.groupby('Bracket')['batter_runs'].sum()
    bracket_balls = player_balls.groupby('Bracket').size()

    bracket_df = pd.DataFrame({'Runs': bracket_runs, 'Balls': bracket_balls}).reset_index()
    bracket_df['Strike Rate'] = (bracket_df['Runs'] / bracket_df['Balls']) * 100

    # Filter out brackets with very low sample sizes (e.g., if they rarely face 31+ balls)
    bracket_df = bracket_df[bracket_df['Balls'] >= 10]

    fig_curve = px.line(
        bracket_df,
        x='Bracket',
        y='Strike Rate',
        markers=True,
        text=bracket_df['Strike Rate'].round(0).astype(int),  # Show integer SR on the points
        labels={'Bracket': 'Deliveries Faced', 'Strike Rate': 'Strike Rate'},
        title=f"The {selected_intent_batter} Acceleration Curve"
    )

    fig_curve.update_traces(
        line_shape='spline',
        line=dict(color='#ff7f0e', width=4),
        marker=dict(size=10, color='white', line=dict(width=2, color='#ff7f0e')),
        textposition="bottom right"
    )

    # Add a horizontal baseline for the league average modern SR
    league_avg_sr = (legal_t20_data['batter_runs'].sum() / legal_t20_data.shape[0]) * 100
    fig_curve.add_hline(y=league_avg_sr, line_dash="dot", annotation_text="League Avg SR", line_color="gray",
                        opacity=0.5)

    fig_curve.update_layout(yaxis_range=[min(bracket_df['Strike Rate']) - 20, max(bracket_df['Strike Rate']) + 30])

    st.plotly_chart(fig_curve, use_container_width=True)

    # ==========================================
    # MULTI-BATTER MODERN META COMPARISON (UP TO 4)
    # ==========================================
    # st.header(" Ultimate Multi-Batter Comparison")
    #
    #
    # batter_list = sorted(t20_data['batter'].unique())
    #
    # # 1. Multi-Select UI with a 4-player limit
    # selected_batters = st.multiselect(
    #     "Select Batters:",
    #     options=batter_list,
    #     default=['V Kohli', 'MS Dhoni', 'RG Sharma'],
    #     max_selections=4,
    #     key="multi_batter_select"
    # )
    #
    # if not selected_batters:
    #     st.warning("Please select at least one batter to compare.")
    # else:
    #     # Define a strict, premium color palette for up to 4 players
    #     theme_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    #     player_colors = {player: theme_colors[i] for i, player in enumerate(selected_batters)}
    #
    #
    #     # 2. Master Stat Processing Function
    #     @st.cache_data  # Caches the data so the app stays lightning fast when changing players
    #     def get_multi_batter_stats(player_names):
    #         all_stats = {}
    #         for player_name in player_names:
    #             b_df = t20_data[t20_data['batter'] == player_name].copy()
    #             legal_balls = b_df[(b_df['is_wide_ball'] == False) & (b_df['is_no_ball'] == False)]
    #
    #             total_runs = b_df['batter_runs'].sum()
    #             total_balls = legal_balls.shape[0]
    #             dismissals = b_df[b_df['is_wicket'] == True].shape[0]
    #
    #             # Efficiency & Milestones
    #             avg = total_runs / dismissals if dismissals > 0 else total_runs
    #             sr = (total_runs / total_balls) * 100 if total_balls > 0 else 0
    #             match_scores = b_df.groupby('match_id')['batter_runs'].sum()
    #             fifties = match_scores[(match_scores >= 50) & (match_scores < 100)].count()
    #             hundreds = match_scores[match_scores >= 100].count()
    #
    #             # Bounds & Dots
    #             fours = b_df[b_df['batter_runs'] == 4].shape[0]
    #             sixes = b_df[b_df['batter_runs'] == 6].shape[0]
    #             bound_runs = (fours * 4) + (sixes * 6)
    #             bound_pct = (bound_runs / total_runs) * 100 if total_runs > 0 else 0
    #             bpb = total_balls / (fours + sixes) if (fours + sixes) > 0 else 0
    #             dot_pct = (b_df[b_df['batter_runs'] == 0].shape[0] / total_balls) * 100 if total_balls > 0 else 0
    #             bpd = total_balls / dismissals if dismissals > 0 else total_balls
    #
    #             # Winning Contribution
    #             b_merged = b_df.merge(matches[['match_id', 'match_winner']], on='match_id', how='left')
    #             win_df = b_merged[b_merged['team_batting'] == b_merged['match_winner']]
    #             w_runs = win_df['batter_runs'].sum()
    #             w_balls = win_df[(win_df['is_wide_ball'] == False) & (win_df['is_no_ball'] == False)].shape[0]
    #             w_diss = win_df[win_df['is_wicket'] == True].shape[0]
    #             win_avg = w_runs / w_diss if w_diss > 0 else w_runs
    #             win_sr = (w_runs / w_balls) * 100 if w_balls > 0 else 0
    #
    #             # Matchups & Phases
    #             def cat_bowler(b_type):
    #                 t = str(b_type).lower()
    #                 if any(k in t for k in ['fast', 'medium', 'pace']):
    #                     return 'Pace'
    #                 elif any(k in t for k in ['spin', 'break', 'orthodox', 'chinaman', 'googly']):
    #                     return 'Spin'
    #                 return 'Other'
    #
    #             b_df['b_cat'] = b_df['bowler_type'].apply(cat_bowler)
    #
    #             def get_sr(df_slice):
    #                 r = df_slice['batter_runs'].sum()
    #                 b = df_slice[(df_slice['is_wide_ball'] == False) & (df_slice['is_no_ball'] == False)].shape[0]
    #                 return (r / b) * 100 if b > 0 else 0
    #
    #             all_stats[player_name] = {
    #                 "Batting Average": avg, "Overall SR": sr,
    #                 "Milestones (50s / 100s)": f"{fifties} / {hundreds}",
    #                 "Boundary %": bound_pct, "Dot Ball %": dot_pct,
    #                 "Balls Per Boundary (BpB)": bpb, "Balls Per Dismissal (BPD)": bpd,
    #                 "Win Avg": win_avg, "Win SR": win_sr,
    #                 "Pace SR": get_sr(b_df[b_df['b_cat'] == 'Pace']), "Spin SR": get_sr(b_df[b_df['b_cat'] == 'Spin']),
    #                 "PP SR": get_sr(b_df[b_df['phase'] == 'Powerplay (1-6)']),
    #                 "Mid SR": get_sr(b_df[b_df['phase'] == 'Middle Overs (7-15)']),
    #                 "Death SR": get_sr(b_df[b_df['phase'] == 'Death Overs (16-20)'])
    #             }
    #         return all_stats
    #
    #
    #     # Fetch Data
    #     stats_dict = get_multi_batter_stats(selected_batters)
    #
    #     st.divider()
    #
    #     # --- 3. PREMIUM HTML/CSS METRIC GRID (No DataFrames) ---
    #     st.subheader("📊 Core Metrics Board")
    #
    #     # Render Player Names Header dynamically
    #     cols = st.columns(len(selected_batters))
    #     for i, player in enumerate(selected_batters):
    #         cols[i].markdown(
    #             f"<h3 style='text-align: center; color: {player_colors[player]}; border-bottom: 2px solid {player_colors[player]}; padding-bottom: 5px;'>{player}</h3>",
    #             unsafe_allow_html=True)
    #
    #     st.markdown("<br>", unsafe_allow_html=True)
    #
    #     core_metrics = [
    #         ("Batting Average", "Batting Average"), ("Overall Strike Rate", "Overall SR"),
    #         ("Balls Per Dismissal (Crease Time)", "Balls Per Dismissal (BPD)"),
    #         ("Milestones (50s / 100s)", "Milestones (50s / 100s)"),
    #         ("Boundary Reliance (%)", "Boundary %"), ("Dot Ball Frequency (%)", "Dot Ball %"),
    #         ("Balls Per Boundary (BpB)", "Balls Per Boundary (BpB)")
    #     ]
    #
    #     # Render Metrics Row by Row
    #     for display_name, dict_key in core_metrics:
    #         # Title for the row
    #         st.markdown(
    #             f"<p style='text-align: center; color: #888; font-size: 13px; text-transform: uppercase; letter-spacing: 1px; font-weight: bold; margin-bottom: 5px;'>{display_name}</p>",
    #             unsafe_allow_html=True)
    #
    #         # Values for the row
    #         row_cols = st.columns(len(selected_batters))
    #         for i, player in enumerate(selected_batters):
    #             val = stats_dict[player][dict_key]
    #             if isinstance(val, float): val = f"{val:.2f}"
    #             row_cols[i].markdown(f"<h4 style='text-align: center; margin-top: 0;'>{val}</h4>",
    #                                  unsafe_allow_html=True)
    #
    #         st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px; opacity: 0.1;'>", unsafe_allow_html=True)
    #
    #     # --- 4. ADVANCED VISUALIZATIONS ---
    #     st.subheader("🕸️ Player DNA & Impact Analysis")
    #
    #     c1, c2 = st.columns(2)
    #
    #     with c1:
    #         # RADAR CHART: Phase & Matchup SR DNA
    #         st.markdown("**Strike Rate Profiling (Matchups & Phases)**")
    #         radar_axes = ['PP SR', 'Mid SR', 'Death SR', 'Pace SR', 'Spin SR']
    #         radar_data = []
    #         for p in selected_batters:
    #             for axis in radar_axes:
    #                 radar_data.append({'Player': p, 'Metric': axis, 'SR': stats_dict[p][axis]})
    #
    #         radar_df = pd.DataFrame(radar_data)
    #         fig_radar = px.line_polar(
    #             radar_df, r='SR', theta='Metric', color='Player',
    #             line_close=True, color_discrete_map=player_colors,
    #             range_r=[0, max(radar_df['SR'].max() + 20, 200)]
    #         )
    #         fig_radar.update_traces(fill='toself', opacity=0.3)
    #         # Moves legend to bottom so it doesn't squish the chart
    #         fig_radar.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
    #         st.plotly_chart(fig_radar, use_container_width=True)
    #
    #     with c2:
    #         # SCATTER CHART: Winning Contribution
    #         st.markdown("**Winning Contribution (Avg vs SR in Team Wins)**")
    #         win_data = []
    #         for p in selected_batters:
    #             win_data.append({'Player': p, 'Win Avg': stats_dict[p]['Win Avg'], 'Win SR': stats_dict[p]['Win SR']})
    #
    #         win_df = pd.DataFrame(win_data)
    #
    #         fig_win = px.scatter(
    #             win_df, x='Win Avg', y='Win SR', color='Player',
    #             size=[20] * len(win_df),  # Uniform large bubbles
    #             text='Player',
    #             color_discrete_map=player_colors,
    #         )
    #         fig_win.update_traces(textposition='top center', marker=dict(line=dict(width=2, color='DarkSlateGrey')))
    #
    #         # Draw baseline averages
    #         fig_win.add_hline(y=140, line_dash="dot", annotation_text="Elite Win SR", line_color="gray", opacity=0.5)
    #         fig_win.add_vline(x=35, line_dash="dot", annotation_text="Elite Win Avg", line_color="gray", opacity=0.5)
    #
    #         fig_win.update_layout(showlegend=False, xaxis_title="Batting Average (In Wins)",
    #                               yaxis_title="Strike Rate (In Wins)")
    #         st.plotly_chart(fig_win, use_container_width=True)

    # st.header("🏏 Ultimate Multi-Batter Comparison")
    #
    # # Assuming 't20_data' and 'matches' DataFrames are already loaded in your script
    # batter_list = sorted(t20_data['batter'].unique())
    #
    # # 1. Multi-Select UI with a 4-player limit
    # selected_batters = st.multiselect(
    #     "Select Batters:",
    #     options=batter_list,
    #     default=['V Kohli', 'MS Dhoni', 'RG Sharma'],
    #     max_selections=4,
    #     key="multi_batter_select"
    # )
    #
    # if not selected_batters:
    #     st.warning("Please select at least one batter to compare.")
    # else:
    #     # Define a strict, premium color palette for up to 4 players
    #     theme_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    #     player_colors = {player: theme_colors[i] for i, player in enumerate(selected_batters)}
    #
    #
    #     # 2. Master Stat Processing Function
    #     @st.cache_data  # Caches the data so the app stays lightning fast when changing players
    #     def get_multi_batter_stats(player_names):
    #         all_stats = {}
    #         for player_name in player_names:
    #             b_df = t20_data[t20_data['batter'] == player_name].copy()
    #             legal_balls = b_df[(b_df['is_wide_ball'] == False) & (b_df['is_no_ball'] == False)]
    #
    #             total_runs = b_df['batter_runs'].sum()
    #             total_balls = legal_balls.shape[0]
    #             dismissals = b_df[b_df['is_wicket'] == True].shape[0]
    #
    #             # Efficiency & Milestones
    #             avg = total_runs / dismissals if dismissals > 0 else total_runs
    #             sr = (total_runs / total_balls) * 100 if total_balls > 0 else 0
    #             match_scores = b_df.groupby('match_id')['batter_runs'].sum()
    #             fifties = match_scores[(match_scores >= 50) & (match_scores < 100)].count()
    #             hundreds = match_scores[match_scores >= 100].count()
    #
    #             # Bounds & Dots
    #             fours = b_df[b_df['batter_runs'] == 4].shape[0]
    #             sixes = b_df[b_df['batter_runs'] == 6].shape[0]
    #             bound_runs = (fours * 4) + (sixes * 6)
    #             bound_pct = (bound_runs / total_runs) * 100 if total_runs > 0 else 0
    #             bpb = total_balls / (fours + sixes) if (fours + sixes) > 0 else 0
    #             dot_pct = (b_df[b_df['batter_runs'] == 0].shape[0] / total_balls) * 100 if total_balls > 0 else 0
    #             bpd = total_balls / dismissals if dismissals > 0 else total_balls
    #
    #             # Winning Contribution
    #             b_merged = b_df.merge(matches[['match_id', 'match_winner']], on='match_id', how='left')
    #             win_df = b_merged[b_merged['team_batting'] == b_merged['match_winner']]
    #             w_runs = win_df['batter_runs'].sum()
    #             w_balls = win_df[(win_df['is_wide_ball'] == False) & (win_df['is_no_ball'] == False)].shape[0]
    #             w_diss = win_df[win_df['is_wicket'] == True].shape[0]
    #             win_avg = w_runs / w_diss if w_diss > 0 else w_runs
    #             win_sr = (w_runs / w_balls) * 100 if w_balls > 0 else 0
    #
    #             # Matchups & Phases
    #             def cat_bowler(b_type):
    #                 t = str(b_type).lower()
    #                 if any(k in t for k in ['fast', 'medium', 'pace']):
    #                     return 'Pace'
    #                 elif any(k in t for k in ['spin', 'break', 'orthodox', 'chinaman', 'googly']):
    #                     return 'Spin'
    #                 return 'Other'
    #
    #             b_df['b_cat'] = b_df['bowler_type'].apply(cat_bowler)
    #
    #             def get_sr(df_slice):
    #                 r = df_slice['batter_runs'].sum()
    #                 b = df_slice[(df_slice['is_wide_ball'] == False) & (df_slice['is_no_ball'] == False)].shape[0]
    #                 return (r / b) * 100 if b > 0 else 0
    #
    #             all_stats[player_name] = {
    #                 "Total Runs": total_runs,  # ADDED TOTAL RUNS HERE
    #                 "Batting Average": avg,
    #                 "Overall SR": sr,
    #                 "Milestones (50s / 100s)": f"{fifties} / {hundreds}",
    #                 "Boundary %": bound_pct,
    #                 "Dot Ball %": dot_pct,
    #                 "Balls Per Boundary (BpB)": bpb,
    #                 "Balls Per Dismissal (BPD)": bpd,
    #                 "Win Avg": win_avg,
    #                 "Win SR": win_sr,
    #                 "Pace SR": get_sr(b_df[b_df['b_cat'] == 'Pace']),
    #                 "Spin SR": get_sr(b_df[b_df['b_cat'] == 'Spin']),
    #                 "PP SR": get_sr(b_df[b_df['phase'] == 'Powerplay (1-6)']),
    #                 "Mid SR": get_sr(b_df[b_df['phase'] == 'Middle Overs (7-15)']),
    #                 "Death SR": get_sr(b_df[b_df['phase'] == 'Death Overs (16-20)'])
    #             }
    #         return all_stats
    #
    #
    #     # Fetch Data
    #     stats_dict = get_multi_batter_stats(selected_batters)
    #
    #     st.divider()
    #
    #     # --- 3. PREMIUM HTML/CSS METRIC GRID (No DataFrames) ---
    #     st.subheader("📊 Core Metrics Board")
    #
    #     # Render Player Names Header dynamically
    #     cols = st.columns(len(selected_batters))
    #     for i, player in enumerate(selected_batters):
    #         cols[i].markdown(
    #             f"<h3 style='text-align: center; color: {player_colors[player]}; border-bottom: 2px solid {player_colors[player]}; padding-bottom: 5px;'>{player}</h3>",
    #             unsafe_allow_html=True
    #         )
    #
    #     st.markdown("<br>", unsafe_allow_html=True)
    #
    #     # ADDED "Total Runs" TO THE METRICS LIST
    #     core_metrics = [
    #         ("Total Career Runs", "Total Runs"),
    #         ("Batting Average", "Batting Average"),
    #         ("Overall Strike Rate", "Overall SR"),
    #         ("Balls Per Dismissal (Crease Time)", "Balls Per Dismissal (BPD)"),
    #         ("Milestones (50s / 100s)", "Milestones (50s / 100s)"),
    #         ("Boundary Reliance (%)", "Boundary %"),
    #         ("Dot Ball Frequency (%)", "Dot Ball %"),
    #         ("Balls Per Boundary (BpB)", "Balls Per Boundary (BpB)")
    #     ]
    #
    #     # Render Metrics Row by Row
    #     for display_name, dict_key in core_metrics:
    #         # Title for the row
    #         st.markdown(
    #             f"<p style='text-align: center; color: #888; font-size: 13px; text-transform: uppercase; letter-spacing: 1px; font-weight: bold; margin-bottom: 5px;'>{display_name}</p>",
    #             unsafe_allow_html=True
    #         )
    #
    #         # Values for the row
    #         row_cols = st.columns(len(selected_batters))
    #         for i, player in enumerate(selected_batters):
    #             val = stats_dict[player][dict_key]
    #
    #             # Formatting to keep it clean: integers don't get decimals, floats get 2 decimals
    #             if isinstance(val, float):
    #                 val = f"{val:.2f}"
    #             elif isinstance(val, int) or str(val).isdigit():
    #                 val = f"{int(val):,}"  # Adds comma formatting for thousands (e.g., 7,000 runs)
    #
    #             row_cols[i].markdown(
    #                 f"<h4 style='text-align: center; margin-top: 0;'>{val}</h4>",
    #                 unsafe_allow_html=True
    #             )
    #
    #         st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px; opacity: 0.1;'>", unsafe_allow_html=True)
    #
    #     # --- 4. ADVANCED VISUALIZATIONS ---
    #     st.subheader("🕸️ Player DNA & Impact Analysis")
    #
    #     c1, c2 = st.columns(2)
    #
    #     with c1:
    #         # RADAR CHART: Phase & Matchup SR DNA
    #         st.markdown("**Strike Rate Profiling (Matchups & Phases)**")
    #         radar_axes = ['PP SR', 'Mid SR', 'Death SR', 'Pace SR', 'Spin SR']
    #         radar_data = []
    #         for p in selected_batters:
    #             for axis in radar_axes:
    #                 radar_data.append({'Player': p, 'Metric': axis, 'SR': stats_dict[p][axis]})
    #
    #         radar_df = pd.DataFrame(radar_data)
    #         fig_radar = px.line_polar(
    #             radar_df, r='SR', theta='Metric', color='Player',
    #             line_close=True, color_discrete_map=player_colors,
    #             range_r=[0, max(radar_df['SR'].max() + 20, 200)]
    #         )
    #         fig_radar.update_traces(fill='toself', opacity=0.3)
    #         # Moves legend to bottom so it doesn't squish the chart
    #         fig_radar.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
    #         st.plotly_chart(fig_radar, use_container_width=True)
    #
    #     with c2:
    #         # SCATTER CHART: Winning Contribution
    #         st.markdown("**Winning Contribution (Avg vs SR in Team Wins)**")
    #         win_data = []
    #         for p in selected_batters:
    #             win_data.append({'Player': p, 'Win Avg': stats_dict[p]['Win Avg'], 'Win SR': stats_dict[p]['Win SR']})
    #
    #         win_df = pd.DataFrame(win_data)
    #
    #         fig_win = px.scatter(
    #             win_df, x='Win Avg', y='Win SR', color='Player',
    #             size=[20] * len(win_df),  # Uniform large bubbles
    #             text='Player',
    #             color_discrete_map=player_colors,
    #         )
    #         fig_win.update_traces(textposition='top center', marker=dict(line=dict(width=2, color='DarkSlateGrey')))
    #
    #         # Draw baseline averages
    #         fig_win.add_hline(y=140, line_dash="dot", annotation_text="Elite Win SR", line_color="gray", opacity=0.5)
    #         fig_win.add_vline(x=35, line_dash="dot", annotation_text="Elite Win Avg", line_color="gray", opacity=0.5)
    #
    #         fig_win.update_layout(showlegend=False, xaxis_title="Batting Average (In Wins)",
    #                               yaxis_title="Strike Rate (In Wins)")
    #         st.plotly_chart(fig_win, use_container_width=True)

    st.header(" Ultimate Multi-Batter Comparison (Modern Meta: 2023-2025)")

    # --- NEW: FILTER FOR MODERN META (2023-2025) ---
    # Checking for both integer and string formats just to be safe with your dataset
    target_seasons = [2023, 2024, 2025, '2023', '2024', '2025']
    modern_t20_data = t20_data[t20_data['season_id'].isin(target_seasons)].copy()

    # Filter matches dataframe to only include matches from these seasons
    valid_match_ids = modern_t20_data['match_id'].unique()
    modern_matches = matches[matches['match_id'].isin(valid_match_ids)].copy()

    # Populate the list ONLY with batters who played in 2023-2025
    batter_list = sorted(modern_t20_data['batter'].dropna().unique())

    # 1. Multi-Select UI with a 4-player limit
    selected_batters = st.multiselect(
        "Select Batters (2023-2025 Form):",
        options=batter_list,
        default=[b for b in ['V Kohli', 'MS Dhoni', 'RG Sharma'] if b in batter_list],
        # Prevents error if default player didn't play in this window
        max_selections=4,
        key="multi_batter_select"
    )

    if not selected_batters:
        st.warning("Please select at least one batter to compare.")
    else:
        # Define a strict, premium color palette for up to 4 players
        theme_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        player_colors = {player: theme_colors[i] for i, player in enumerate(selected_batters)}


        # 2. Master Stat Processing Function
        @st.cache_data  # Caches the data so the app stays lightning fast when changing players
        def get_multi_batter_stats(player_names):
            all_stats = {}
            for player_name in player_names:
                # USING THE FILTERED MODERN DATASET
                b_df = modern_t20_data[modern_t20_data['batter'] == player_name].copy()
                # For a batter, No-Balls DO count as a ball faced. Only Wides do not.
                balls_faced_df = b_df[b_df['is_wide_ball'] == False]

                total_runs = b_df['batter_runs'].sum()
                total_balls = balls_faced_df.shape[0]
                dismissals = b_df[b_df['is_wicket'] == True].shape[0]

                # Efficiency & Milestones
                avg = total_runs / dismissals if dismissals > 0 else total_runs
                sr = (total_runs / total_balls) * 100 if total_balls > 0 else 0
                match_scores = b_df.groupby('match_id')['batter_runs'].sum()
                fifties = match_scores[(match_scores >= 50) & (match_scores < 100)].count()
                hundreds = match_scores[match_scores >= 100].count()

                # Bounds & Dots
                fours = b_df[b_df['batter_runs'] == 4].shape[0]
                sixes = b_df[b_df['batter_runs'] == 6].shape[0]
                bound_runs = (fours * 4) + (sixes * 6)
                bound_pct = (bound_runs / total_runs) * 100 if total_runs > 0 else 0
                bpb = total_balls / (fours + sixes) if (fours + sixes) > 0 else 0
                dot_pct = (b_df[b_df['batter_runs'] == 0].shape[0] / total_balls) * 100 if total_balls > 0 else 0
                bpd = total_balls / dismissals if dismissals > 0 else total_balls

                # Winning Contribution (Using filtered modern_matches)
                b_merged = b_df.merge(modern_matches[['match_id', 'match_winner']], on='match_id', how='left')
                win_df = b_merged[b_merged['team_batting'] == b_merged['match_winner']]
                w_runs = win_df['batter_runs'].sum()
                w_balls = win_df[win_df['is_wide_ball'] == False].shape[0]
                w_diss = win_df[win_df['is_wicket'] == True].shape[0]
                win_avg = w_runs / w_diss if w_diss > 0 else w_runs
                win_sr = (w_runs / w_balls) * 100 if w_balls > 0 else 0

                # Matchups & Phases
                def cat_bowler(b_type):
                    t = str(b_type).lower()
                    if any(k in t for k in ['fast', 'medium', 'pace']):
                        return 'Pace'
                    elif any(k in t for k in ['spin', 'break', 'orthodox', 'chinaman', 'googly']):
                        return 'Spin'
                    return 'Other'

                b_df['b_cat'] = b_df['bowler_type'].apply(cat_bowler)

                def get_sr(df_slice):
                    r = df_slice['batter_runs'].sum()
                    b = df_slice[(df_slice['is_wide_ball'] == False) & (df_slice['is_no_ball'] == False)].shape[0]
                    return (r / b) * 100 if b > 0 else 0

                all_stats[player_name] = {
                    "Total Runs": total_runs,
                    "Batting Average": avg,
                    "Overall SR": sr,
                    "Milestones (50s / 100s)": f"{fifties} / {hundreds}",
                    "Boundary %": bound_pct,
                    "Dot Ball %": dot_pct,
                    "Balls Per Boundary (BpB)": bpb,
                    "Balls Per Dismissal (BPD)": bpd,
                    "Win Avg": win_avg,
                    "Win SR": win_sr,
                    "Pace SR": get_sr(b_df[b_df['b_cat'] == 'Pace']),
                    "Spin SR": get_sr(b_df[b_df['b_cat'] == 'Spin']),
                    "PP SR": get_sr(b_df[b_df['phase'] == 'Powerplay (1-6)']),
                    "Mid SR": get_sr(b_df[b_df['phase'] == 'Middle Overs (7-15)']),
                    "Death SR": get_sr(b_df[b_df['phase'] == 'Death Overs (16-20)'])
                }
            return all_stats


        # Fetch Data
        stats_dict = get_multi_batter_stats(selected_batters)

        st.divider()

        # --- 3. PREMIUM HTML/CSS METRIC GRID (No DataFrames) ---
        st.subheader(" Core Metrics Board (2023-2025)")

        # Render Player Names Header dynamically
        cols = st.columns(len(selected_batters))
        for i, player in enumerate(selected_batters):
            cols[i].markdown(
                f"<h3 style='text-align: center; color: {player_colors[player]}; border-bottom: 2px solid {player_colors[player]}; padding-bottom: 5px;'>{player}</h3>",
                unsafe_allow_html=True
            )

        st.markdown("<br>", unsafe_allow_html=True)

        core_metrics = [
            ("Runs (2023-25)", "Total Runs"),
            ("Batting Average", "Batting Average"),
            ("Overall Strike Rate", "Overall SR"),
            ("Balls Per Dismissal", "Balls Per Dismissal (BPD)"),
            ("Milestones (50s / 100s)", "Milestones (50s / 100s)"),
            ("Boundary Reliance (%)", "Boundary %"),
            ("Dot Ball Frequency (%)", "Dot Ball %"),
            ("Balls Per Boundary (BpB)", "Balls Per Boundary (BpB)")
        ]

        # Render Metrics Row by Row
        for display_name, dict_key in core_metrics:
            # Title for the row
            st.markdown(
                f"<p style='text-align: center; color: #888; font-size: 13px; text-transform: uppercase; letter-spacing: 1px; font-weight: bold; margin-bottom: 5px;'>{display_name}</p>",
                unsafe_allow_html=True
            )

            # Values for the row
            row_cols = st.columns(len(selected_batters))
            for i, player in enumerate(selected_batters):
                val = stats_dict[player][dict_key]

                # Formatting to keep it clean
                if isinstance(val, float):
                    val = f"{val:.2f}"
                elif isinstance(val, int) or str(val).isdigit():
                    val = f"{int(val):,}"

                row_cols[i].markdown(
                    f"<h4 style='text-align: center; margin-top: 0;'>{val}</h4>",
                    unsafe_allow_html=True
                )

            st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px; opacity: 0.1;'>", unsafe_allow_html=True)

        # --- 4. ADVANCED VISUALIZATIONS ---
        st.subheader(" Player DNA & Impact Analysis (Modern Meta)")

        c1, c2 = st.columns(2)

        with c1:
            # RADAR CHART: Phase & Matchup SR DNA
            st.markdown("**Strike Rate Profiling (Matchups & Phases)**")
            radar_axes = ['PP SR', 'Mid SR', 'Death SR', 'Pace SR', 'Spin SR']
            radar_data = []
            for p in selected_batters:
                for axis in radar_axes:
                    radar_data.append({'Player': p, 'Metric': axis, 'SR': stats_dict[p][axis]})

            radar_df = pd.DataFrame(radar_data)
            fig_radar = px.line_polar(
                radar_df, r='SR', theta='Metric', color='Player',
                line_close=True, color_discrete_map=player_colors,
                range_r=[0, max(radar_df['SR'].max() + 20, 200)]
            )
            fig_radar.update_traces(fill='toself', opacity=0.3)
            # Moves legend to bottom so it doesn't squish the chart
            fig_radar.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
            st.plotly_chart(fig_radar, use_container_width=True)

        with c2:
            # SCATTER CHART: Winning Contribution
            st.markdown("**Winning Contribution (Avg vs SR in Team Wins)**")
            win_data = []
            for p in selected_batters:
                win_data.append({'Player': p, 'Win Avg': stats_dict[p]['Win Avg'], 'Win SR': stats_dict[p]['Win SR']})

            win_df = pd.DataFrame(win_data)

            fig_win = px.scatter(
                win_df, x='Win Avg', y='Win SR', color='Player',
                size=[20] * len(win_df),  # Uniform large bubbles
                text='Player',
                color_discrete_map=player_colors,
            )
            fig_win.update_traces(textposition='top center', marker=dict(line=dict(width=2, color='DarkSlateGrey')))

            # Draw baseline averages (adjusted slightly for modern meta which is more aggressive)
            fig_win.add_hline(y=150, line_dash="dot", annotation_text="Elite Win SR (Modern)", line_color="gray",
                              opacity=0.5)
            fig_win.add_vline(x=35, line_dash="dot", annotation_text="Elite Win Avg", line_color="gray", opacity=0.5)

            fig_win.update_layout(showlegend=False, xaxis_title="Batting Average (In Wins)",
                                  yaxis_title="Strike Rate (In Wins)")
            st.plotly_chart(fig_win, use_container_width=True)



    # ==========================================
    # MULTI-BOWLER MODERN META COMPARISON (UP TO 4)
    # ==========================================
    st.header(" Ultimate Multi-Bowler Scouting Dashboard")


    # Get the definitive list of bowlers from your dataset
    bowler_list = sorted(t20_data['bowler'].dropna().unique())

    # --- CRASH-PROOF DEFAULT CHECK ---
    preferred_defaults = ['JJ Bumrah', 'Rashid Khan', 'YS Chahal', 'SP Narine', 'Sunil Narine', 'B Kumar']
    safe_defaults = [b for b in preferred_defaults if b in bowler_list]
    safe_defaults = safe_defaults[:4] if len(safe_defaults) > 0 else bowler_list[:3]

    # 1. Multi-Select UI with a 4-player limit
    selected_bowlers = st.multiselect(
        "Select Bowlers:",
        options=bowler_list,
        default=safe_defaults,
        max_selections=4,
        key="multi_bowler_select"
    )

    if not selected_bowlers:
        st.warning("Please select at least one bowler to compare.")
    else:
        # Premium scouting color palette for up to 4 players
        theme_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        player_colors = {player: theme_colors[i] for i, player in enumerate(selected_bowlers)}


        @st.cache_data
        def get_multi_bowler_stats(player_names):
            all_stats = {}
            for name in player_names:
                b_df = t20_data[t20_data['bowler'] == name].copy()
                legal_balls = b_df[(b_df['is_wide_ball'] == False) & (b_df['is_no_ball'] == False)]

                total_legal = legal_balls.shape[0]
                # Bowlers are NOT penalized for byes and leg byes
                bowler_runs_df = b_df[(b_df['is_bye'] == False) & (b_df['is_leg_bye'] == False)]
                runs = bowler_runs_df['total_runs'].sum()
                overs = total_legal / 6

                # Wickets (Only counting bowler-credited wickets)
                valid_kinds = ['caught', 'bowled', 'lbw', 'stumped', 'caught and bowled', 'hit wicket']
                w_df = b_df[(b_df['is_wicket'] == True) & (b_df['wicket_kind'].isin(valid_kinds))]
                total_w = w_df.shape[0]

                # 1. Efficiency Metrics
                avg = runs / total_w if total_w > 0 else runs
                eco = runs / overs if overs > 0 else 0
                sr = total_legal / total_w if total_w > 0 else 0

                # 2. Hauls (Group by Match)
                match_wickets = w_df.groupby('match_id').size()
                hauls = f"{match_wickets[match_wickets == 4].count()} / {match_wickets[match_wickets >= 5].count()}"

                # 3. Pressure & Discipline
                dots = b_df[b_df['total_runs'] == 0].shape[0]
                dot_pct = (dots / total_legal) * 100 if total_legal > 0 else 0

                bound_runs = b_df[b_df['batter_runs'].isin([4, 6])]['total_runs'].sum()
                bound_pct_conceded = (bound_runs / runs) * 100 if runs > 0 else 0

                extras = b_df[(b_df['is_wide_ball'] == True) | (b_df['is_no_ball'] == True)].shape[0]
                extras_rate = (extras / total_legal) * 100 if total_legal > 0 else 0

                # 4. Top Order % (Safely bypasses if batting_position is missing)
                if 'batting_position' in b_df.columns:
                    top_order_w = w_df[w_df['batting_position'] <= 4].shape[0]
                    top_order_pct = (top_order_w / total_w) * 100 if total_w > 0 else 0
                else:
                    top_order_pct = 0.0

                    # 5. Situation/DNA Stats

                def get_phase_eco(phase):
                    p_df = b_df[b_df['phase'] == phase]
                    p_legal = legal_balls[legal_balls['phase'] == phase].shape[0]
                    p_runs = p_df['total_runs'].sum()
                    return p_runs / (p_legal / 6) if p_legal > 0 else 0

                def get_matchup_eco(hand):
                    # Using batsman_type as provided in your columns
                    if 'batsman_type' in b_df.columns:
                        h_df = b_df[b_df['batsman_type'].astype(str).str.contains(hand, case=False, na=False)]
                        h_legal = h_df[(h_df['is_wide_ball'] == False) & (h_df['is_no_ball'] == False)].shape[0]
                        h_runs = h_df['total_runs'].sum()
                        return h_runs / (h_legal / 6) if h_legal > 0 else 0
                    else:
                        return 0.0

                all_stats[name] = {
                    "Total Wickets": total_w, "Bowling Average": avg, "Economy Rate": eco,
                    "Bowling Strike Rate": sr, "4W / 5W Hauls": hauls,
                    "Dot Ball %": dot_pct, "Boundary % Conceded": bound_pct_conceded,
                    "Extras Rate (per 100b)": extras_rate, "Top-Order Wicket %": top_order_pct,
                    "PP Eco": get_phase_eco('Powerplay (1-6)'),
                    "Mid Eco": get_phase_eco('Middle Overs (7-15)'),
                    "Death Eco": get_phase_eco('Death Overs (16-20)'),
                    "vs LHB Eco": get_matchup_eco('Left'),
                    "vs RHB Eco": get_matchup_eco('Right')
                }
            return all_stats


        # Fetch Data
        stats_dict = get_multi_bowler_stats(selected_bowlers)

        st.divider()

        # --- SECTION 1: PREMIUM HTML/CSS TALE OF THE TAPE ---
        st.subheader(" Primary Efficiency Board")

        cols = st.columns(len(selected_bowlers))
        for i, player in enumerate(selected_bowlers):
            cols[i].markdown(
                f"<h3 style='text-align: center; color: {player_colors[player]}; border-bottom: 2px solid {player_colors[player]}; padding-bottom: 5px;'>{player}</h3>",
                unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        core_metrics = [
            ("Total Wickets", "Total Wickets"), ("Bowling Average", "Bowling Average"),
            ("Economy Rate", "Economy Rate"), ("Bowling Strike Rate", "Bowling Strike Rate"),
            ("4W / 5W Hauls", "4W / 5W Hauls"), ("Dot Ball Percentage (%)", "Dot Ball %")
        ]

        for display_name, dict_key in core_metrics:
            st.markdown(
                f"<p style='text-align: center; color: #888; font-size: 13px; text-transform: uppercase; letter-spacing: 1px; font-weight: bold; margin-bottom: 5px;'>{display_name}</p>",
                unsafe_allow_html=True)
            row_cols = st.columns(len(selected_bowlers))
            for i, player in enumerate(selected_bowlers):
                val = stats_dict[player][dict_key]
                if isinstance(val, float): val = f"{val:.2f}"
                row_cols[i].markdown(f"<h4 style='text-align: center; margin-top: 0;'>{val}</h4>",
                                     unsafe_allow_html=True)
            st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px; opacity: 0.1;'>", unsafe_allow_html=True)

        # --- SECTION 2: THE BOWLING DNA (SITUATIONAL RADAR) ---
        st.subheader(" Situational DNA (Economy Profiling)")


        radar_axes = ['PP Eco', 'Mid Eco', 'Death Eco', 'vs LHB Eco', 'vs RHB Eco']
        radar_data = []
        for p in selected_bowlers:
            for axis in radar_axes:
                radar_data.append({'Player': p, 'Situation': axis.replace(' Eco', ''), 'Economy': stats_dict[p][axis]})

        radar_df = pd.DataFrame(radar_data)

        fig_radar = px.line_polar(
            radar_df, r='Economy', theta='Situation', color='Player',
            line_close=True, color_discrete_map=player_colors,
            range_r=[0, max(12, radar_df['Economy'].max() + 2)]
        )
        fig_radar.update_traces(fill='toself', opacity=0.3)
        fig_radar.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
        st.plotly_chart(fig_radar, use_container_width=True)

        st.divider()

        # --- SECTION 3: DISCIPLINE & QUALITY ---
        st.subheader(" Discipline & Wicket Quality")


        st.markdown("**Extras Rate vs Boundary Control**")
        discipline_data = [{'Player': p, 'Extras Rate': stats_dict[p]['Extras Rate (per 100b)'],
                                'Boundary %': stats_dict[p]['Boundary % Conceded']} for p in selected_bowlers]
        fig_disc = px.scatter(
                pd.DataFrame(discipline_data), x='Extras Rate', y='Boundary %', color='Player',
                size=[25] * len(selected_bowlers), text='Player', color_discrete_map=player_colors
            )
        fig_disc.update_traces(textposition='top center', marker=dict(line=dict(width=2, color='DarkSlateGrey')))
        fig_disc.update_layout(showlegend=False, xaxis_title="Extras per 100 Balls (Lower is better)",
                                   yaxis_title="Boundary % Conceded")

            # Add a baseline for elite accuracy
        fig_disc.add_vline(x=3.0, line_dash="dot", annotation_text="Elite Accuracy", line_color="gray", opacity=0.5)

        st.plotly_chart(fig_disc, use_container_width=True)

    # --- NEW UPGRADED SECTION: THE 200+ NORMALIZATION (ALL-TIME) ---
    st.divider()
    st.header(" The 200+ Normalization & Its Devaluation (2007-2026)")


    # --- 1. DATA PREPARATION (The Insight Engine) ---
    # Isolate 1st innings totals
    first_inn = t20_data[t20_data['innings'] == 1].groupby(['season_id', 'match_id', 'team_batting'])[
        'total_runs'].sum().reset_index()

    # Merge with match results to see if the team batting first won
    first_inn = first_inn.merge(matches[['match_id', 'match_winner']], on='match_id', how='left')
    first_inn['won_match'] = first_inn['team_batting'] == first_inn['match_winner']

    # Calculate seasonal stats across ALL YEARS
    season_stats = []
    for year in sorted(first_inn['season_id'].unique()):
        df_year = first_inn[first_inn['season_id'] == year]
        total_matches = len(df_year)

        # Isolate scores of 200 or more
        over_200 = df_year[df_year['total_runs'] >= 200]
        count_200 = len(over_200)

        # Calculate Win Probability when scoring 200+
        win_rate_200 = (over_200['won_match'].sum() / count_200 * 100) if count_200 > 0 else 0

        season_stats.append({
            'Season': year,
            'Total Matches': total_matches,
            '200+ Scores': count_200,
            'Win Rate': win_rate_200
        })

    stats_df = pd.DataFrame(season_stats)

    # --- 2. PREMIUM UI: TOP KPI METRICS ---
    # Dynamically grab 2022 (Pre-Impact) and the latest available year in your dataset
    stats_22 = stats_df[stats_df['Season'] == 2022].iloc[0]
    latest_year = stats_df['Season'].max()
    stats_latest = stats_df[stats_df['Season'] == latest_year].iloc[0]

    # Custom HTML/CSS Grid for a sleek look
    st.markdown("<br>", unsafe_allow_html=True)


    st.markdown("<br>", unsafe_allow_html=True)

    # --- 3. THE DUAL-AXIS PRESENTATION CHART ---
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # 1. Bar Chart: Volume of 200+ Scores
    fig.add_trace(
        go.Bar(
            x=stats_df['Season'],
            y=stats_df['200+ Scores'],
            name="Volume of 200+ Scores",
            marker_color='#ff7f0e',
            marker_line_color='white',
            marker_line_width=1.5,
            opacity=0.85,
            text=stats_df['200+ Scores'],
            textposition='auto',
            hoverinfo='x+y'
        ),
        secondary_y=False,
    )

    # 2. Line Chart: Win Probability
    fig.add_trace(
        go.Scatter(
            x=stats_df['Season'],
            y=stats_df['Win Rate'],
            name="Win Probability (%)",
            mode='lines+markers',
            line=dict(color='#00d2ff', width=4, shape='spline'),  # Premium neon blue, curved line
            marker=dict(size=8, color='white', line=dict(width=2, color='#00d2ff')),
            hovertemplate="Win Rate: %{y:.1f}%<extra></extra>"
        ),
        secondary_y=True,
    )

    # 3. Aesthetics & Layout
    # 3. Aesthetics & Layout
    fig.update_layout(
        title=dict(
            text="The Volume Surge vs. The Value Collapse (2007-2026)",
            font=dict(size=20, color='white'),
            y=0.98  # Explicitly anchors the title near the top
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        hovermode="x unified",

        # Pushed the legend down slightly (y=1.01 instead of 1.05)
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1),

        # MASSIVE fix here: Increased top margin (t=100) to give both title and legend breathing room
        margin=dict(l=20, r=20, t=100, b=20)
    )

    fig.update_xaxes(
        tickmode='linear',
        dtick=1,
        tickangle=-45, # Angles the text so all 18 years fit cleanly
        showgrid=False,
        title_text="Season"
    )
    fig.update_yaxes(
        title_text="Number of 200+ Scores",
        showgrid=True,
        gridcolor='rgba(255,255,255,0.1)',
        secondary_y=False
    )
    fig.update_yaxes(
        title_text="Win Probability (%)",
        range=[0, 110],
        showgrid=False,
        secondary_y=True
    )

    # 4. Impact Player Annotation (Extended to cover up to 2025)
    fig.add_vrect(
        x0=2022.5, x1=latest_year + 0.5,
        fillcolor="gray", opacity=0.1,
        layer="below", line_width=0,
        annotation_text="Impact Player Era", annotation_position="top left",
        annotation_font_size=12, annotation_font_color="white"
    )

    st.plotly_chart(fig, use_container_width=True)

    # ==========================================
    # SHOWSTOPPER UI: THE RUN INFLATION (NEON THEME)
    # ==========================================






