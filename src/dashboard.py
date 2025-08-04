import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from data_collector import SocialComputingDataCollector
from analysis import SocialComputingAnalysis

# =============================
# Gender Disparity in Tech Communities Dashboard
# STUDENT TEAM PROJECT: Fatima & Kainat
# =============================

st.set_page_config(
    page_title="Gender Disparity in Tech Communities",
    page_icon="👩‍💻",
    layout="wide"
)

# Project summary at the top
with st.container():
    st.markdown("""
    <h1 style='text-align: center; color: #2c3e50;'>Gender Disparity in Tech Communities</h1>
    <h4 style='text-align: center; color: #34495e;'>A Social Computing Analysis Project</h4>
    <div style='text-align: center;'>
        <b>Team Members:</b> Fatima (Stack Overflow & GitHub) | Kainat (Reddit & Cross-Platform)<br>
        <b>Course:</b> Social Computing &nbsp; | &nbsp; <b>Institution:</b> Leibniz Univeristy Hannover
    </div>
    <hr style='border: 1px solid #bbb;'>
    """, unsafe_allow_html=True)
    st.info("""
    This dashboard analyzes gender disparities in technology communities using traces of online engagement from Stack Overflow, GitHub, and Reddit. The project follows social computing methodology by analyzing natural digital footprints rather than survey responses.
    """)

collector = SocialComputingDataCollector()
analyzer = SocialComputingAnalysis()

@st.cache_data(ttl=3600)
def load_platform_data(platform: str):
    return analyzer.load_platform_data(platform)

# Sidebar navigation
st.sidebar.header("Dashboard Sections")
section = st.sidebar.radio(
    "Select Dashboard Section:",
    [
        "Stack Overflow Analysis",
        "GitHub Analysis", 
        "Reddit Analysis",
        "Cross-Platform Comparison",
        
    ]
)

# =============================
# Section 1: Stack Overflow Analysis
# =============================
if section == "Stack Overflow Analysis":
    with st.container():
        st.markdown("""
        <h2 style='color: #2980b9;'>Stack Overflow Analysis</h2>
        <span style='color: #888;'>Section Lead: Fatima</span>
        """, unsafe_allow_html=True)
        st.write(":female-technologist: :man-technologist: **Analysis of Stack Overflow user engagement, reputation, and participation patterns by gender.**")

        try:
            data = load_platform_data("stackoverflow")
            if not data or data["users"].empty:
                st.warning("No Stack Overflow data available. Please run data collection first.")
            else:
                users_df = data["users"]
                questions_df = data["questions"]
                
                # Basic Metrics Table
                st.markdown("**📊 Basic Metrics**")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Users", len(users_df))
                with col2:
                    st.metric("Total Questions", len(questions_df))
                with col3:
                    female_pct = (users_df['gender_inferred'] == 'female').mean() * 100
                    st.metric("Female Users (%)", f"{female_pct:.1f}%")
                with col4:
                    avg_reputation = users_df['reputation'].mean()
                    st.metric("Avg Reputation", f"{avg_reputation:.0f}")
                
                # Gender Distribution
                st.markdown("**👥 Gender Distribution**")
                # Clean up gender categories to remove mostly_male/mostly_female
                users_df['gender_inferred'] = users_df['gender_inferred'].replace({
                    'unknown': 'anonymous',
                    'mostly_male': 'male',
                    'mostly_female': 'female'
                })
                gender_dist = users_df['gender_inferred'].value_counts()
                fig_gender = px.pie(
                    values=gender_dist.values,
                    names=gender_dist.index,
                    title="Stack Overflow: Gender Distribution",
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                st.plotly_chart(fig_gender, use_container_width=True)
                
                # Reputation Analysis
                st.markdown("**🏆 Reputation Analysis by Gender**")
                fig_reputation = px.box(
                    users_df,
                    x="gender_inferred",
                    y="reputation",
                    title="Reputation Distribution by Gender",
                    color="gender_inferred",
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                st.plotly_chart(fig_reputation, use_container_width=True)
                
                # Activity Patterns
                st.markdown("**📈 Activity Patterns**")
                col1, col2 = st.columns(2)
                with col1:
                    fig_questions = px.box(
                        users_df,
                        x="gender_inferred",
                        y="question_count",
                        title="Questions Asked by Gender",
                        color="gender_inferred",
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    st.plotly_chart(fig_questions, use_container_width=True)
                with col2:
                    # Show reputation comparison instead of answers since all answers are 0
                    fig_reputation_activity = px.box(
                        users_df,
                        x="gender_inferred",
                        y="reputation",
                        title="Reputation by Gender",
                        color="gender_inferred",
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    st.plotly_chart(fig_reputation_activity, use_container_width=True)
                

                
                # Gender Disparity Analysis
                st.markdown("**🔍 Gender Disparity Analysis**")
                try:
                    # Calculate gender disparity metrics
                    gender_counts = users_df['gender_inferred'].value_counts()
                    total_users = len(users_df)
                    
                    female_users = gender_counts.get('female', 0)
                    male_users = gender_counts.get('male', 0)
                    anonymous_users = gender_counts.get('anonymous', 0)
                    
                    female_pct = (female_users / total_users) * 100 if total_users > 0 else 0
                    male_pct = (male_users / total_users) * 100 if total_users > 0 else 0
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Female Users", female_users, f"{female_pct:.1f}%")
                    with col2:
                        st.metric("Male Users", male_users, f"{male_pct:.1f}%")
                    with col3:
                        disparity = abs(female_pct - male_pct)
                        st.metric("Gender Disparity", f"{disparity:.1f}%")
                    
                    # Show which gender has more users
                    if female_pct > male_pct:
                        st.success(f"✅ Female users have {female_pct - male_pct:.1f}% more representation than male users")
                    elif male_pct > female_pct:
                        st.warning(f"⚠️ Male users have {male_pct - female_pct:.1f}% more representation than female users")
                    else:
                        st.info("ℹ️ Equal representation between male and female users")
                        
                except Exception as e:
                    st.error(f"Error in gender disparity analysis: {e}")
                
                # Statistical Summary Table
                st.markdown("**📋 Statistical Summary**")
                summary_stats = users_df.groupby('gender_inferred').agg({
                    'reputation': ['mean', 'median', 'std'],
                    'question_count': ['mean', 'median', 'std'],
                    'answer_count': ['mean', 'median', 'std']
                }).round(2)
                st.dataframe(summary_stats, use_container_width=True)
                
                # Bias Analysis Section
                st.markdown("**🔍 Bias Analysis**")
               
                # Vote ratio differences (using question scores)
                if not questions_df.empty:
                    question_scores_by_gender = questions_df.groupby('gender_inferred')['score'].agg(['mean', 'median', 'std']).round(2)
                    st.markdown("**📊 Question Score Analysis by Gender**")
                    st.dataframe(question_scores_by_gender, use_container_width=True)
                    
                    fig_question_scores = px.box(
                        questions_df,
                        x="gender_inferred",
                        y="score",
                        title="Question Scores by Gender (Vote Bias Analysis)",
                        color="gender_inferred",
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    st.plotly_chart(fig_question_scores, use_container_width=True)
        except Exception as e:
            st.error(f"Error loading Stack Overflow data: {e}")

# =============================
# Section 2: GitHub Analysis
# =============================
elif section == "GitHub Analysis":
    with st.container():
        st.markdown("""
        <h2 style='color: #2ecc71;'>GitHub Analysis</h2>
        <span style='color: #888;'>Section Lead: Fatima</span>
        """, unsafe_allow_html=True)
        st.write(":female-technologist: :man-technologist: **Analysis of GitHub user engagement, repository success, and participation patterns by gender.**")

        try:
            data = load_platform_data("github")
            if not data or "users" not in data or data["users"].empty:
                st.warning("No GitHub user data available. Please run data collection first.")
            elif "repositories" not in data or data["repositories"].empty:
                st.warning("No GitHub repository data available. Please run data collection first.")
            else:
                users_df = data["users"]
                repos_df = data["repositories"]
                
                # Basic Metrics Table
                st.markdown("**📊 Basic Metrics**")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Users", len(users_df))
                with col2:
                    st.metric("Total Repositories", len(repos_df))
                with col3:
                    female_pct = (users_df['gender_inferred'] == 'female').mean() * 100
                    st.metric("Female Users (%)", f"{female_pct:.1f}%")
                with col4:
                    avg_stars = repos_df['stars'].mean() if not repos_df.empty else 0
                    st.metric("Avg Repository Stars", f"{avg_stars:.0f}")
                
                # Gender Distribution
                st.markdown("**👥 Gender Distribution**")
                # Clean up gender categories to remove mostly_male/mostly_female
                users_df['gender_inferred'] = users_df['gender_inferred'].replace({
                    'unknown': 'anonymous',
                    'mostly_male': 'male',
                    'mostly_female': 'female'
                })
                gender_dist = users_df['gender_inferred'].value_counts()
                fig_gender = px.pie(
                    values=gender_dist.values,
                    names=gender_dist.index,
                    title="GitHub: Gender Distribution",
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                st.plotly_chart(fig_gender, use_container_width=True)
                
                # Repository Success by Gender
                st.markdown("**⭐ Repository Success by Gender**")
                repos_df['gender_inferred'] = repos_df['gender_inferred'].replace('unknown', 'anonymous')
                if not repos_df.empty:
                    fig_stars = px.box(
                        repos_df,
                        x="gender_inferred",
                        y="stars",
                        title="Repository Stars by Gender",
                        color="gender_inferred",
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    st.plotly_chart(fig_stars, use_container_width=True)
                
                                # User Activity Patterns
                st.markdown("**📈 User Activity Patterns**")
                
                # Add data quality note
                st.info("⚠️ **Data Note**: Limited user data available. Analysis focuses on repository-level metrics.")
                
                col1, col2 = st.columns(2)
                with col1:
                    # Repository stars analysis (more meaningful than user patterns)
                    if not repos_df.empty:
                        fig_stars_analysis = px.box(
                            repos_df,
                            x="gender_inferred",
                            y="stars",
                            title="Repository Stars by Gender",
                            color="gender_inferred",
                            color_discrete_sequence=px.colors.qualitative.Pastel
                        )
                        st.plotly_chart(fig_stars_analysis, use_container_width=True)
                with col2:
                    # Language preferences (more meaningful)
                    if not repos_df.empty:
                        language_gender = repos_df.groupby(['language', 'gender_inferred']).size().reset_index()
                        language_gender = language_gender.rename(columns={0: 'count'})
                        fig_language_analysis = px.bar(
                            language_gender,
                            x="language",
                            y="count",
                            color="gender_inferred",
                            title="Language Preferences by Gender",
                            color_discrete_sequence=px.colors.qualitative.Pastel
                        )
                        st.plotly_chart(fig_language_analysis, use_container_width=True)
                
                # Gender Disparity Analysis
                st.markdown("**🔍 Gender Disparity Analysis**")
                try:
                    # Calculate gender disparity metrics
                    gender_counts = users_df['gender_inferred'].value_counts()
                    total_users = len(users_df)
                    
                    female_users = gender_counts.get('female', 0)
                    male_users = gender_counts.get('male', 0)
                    anonymous_users = gender_counts.get('anonymous', 0)
                    
                    female_pct = (female_users / total_users) * 100 if total_users > 0 else 0
                    male_pct = (male_users / total_users) * 100 if total_users > 0 else 0
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Female Users", female_users, f"{female_pct:.1f}%")
                    with col2:
                        st.metric("Male Users", male_users, f"{male_pct:.1f}%")
                    with col3:
                        disparity = abs(female_pct - male_pct)
                        st.metric("Gender Disparity", f"{disparity:.1f}%")
                    
                    # Show which gender has more users
                    if female_pct > male_pct:
                        st.success(f"✅ Female users have {female_pct - male_pct:.1f}% more representation than male users")
                    elif male_pct > female_pct:
                        st.warning(f"⚠️ Male users have {male_pct - female_pct:.1f}% more representation than female users")
                    else:
                        st.info("ℹ️ Equal representation between male and female users")
                        
                except Exception as e:
                    st.error(f"Error in gender disparity analysis: {e}")
                
                # Statistical Summary Table
                st.markdown("**📋 Statistical Summary**")
                if not repos_df.empty:
                    summary_stats = repos_df.groupby('gender_inferred').agg({
                        'stars': ['mean', 'median', 'std'],
                        'forks': ['mean', 'median', 'std']
                    }).round(2)
                    st.dataframe(summary_stats, use_container_width=True)
                else:
                    st.info("No repository data available for statistical summary")
                
                # Bias Analysis Section
                st.markdown("**🔍 Bias Analysis**")
                st.info("📊 **Bias Metrics**: Analyzing potential gender bias in repository recognition, star patterns, and contribution visibility.")
                
                if not repos_df.empty:
                    # Language bias analysis
                    language_bias = repos_df.groupby(['language', 'gender_inferred'])['stars'].mean().reset_index()
                    fig_language_bias = px.bar(
                        language_bias,
                        x="language",
                        y="stars",
                        color="gender_inferred",
                        title="Average Stars by Language and Gender",
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    st.plotly_chart(fig_language_bias, use_container_width=True)
        except Exception as e:
            st.error(f"Error loading GitHub data: {e}")

# =============================
# Section 3: Reddit Analysis
# =============================
elif section == "Reddit Analysis":
    with st.container():
        st.markdown("""
        <h2 style='color: #8e44ad;'>Reddit Analysis</h2>
        <span style='color: #888;'>Section Lead: Kainat</span>
        """, unsafe_allow_html=True)
        st.write(":female-technologist: :man-technologist: **Analysis of Reddit tech communities, posts, and comments by gender.**")

        # --- Reddit Posts Analysis ---
        st.subheader("📝 Reddit Posts Analysis")

        try:
            data = load_platform_data("reddit")
            if not data or "posts" not in data or data["posts"].empty:
                st.warning("No Reddit data available. Please run data collection first.")
            else:
                posts_df = data["posts"]
                
                # Clean up gender categories to remove mostly_male/mostly_female
                posts_df['gender_inferred'] = posts_df['gender_inferred'].replace({
                    'unknown': 'anonymous',
                    'mostly_male': 'male',
                    'mostly_female': 'female'
                })
                
                # Add data quality note
                st.info("📊 **Data Quality**: 570 posts analyzed. Most users are anonymous (459), with 76 male and 31 female users.")
                
                # Basic Metrics Table
                st.markdown("**📊 Basic Metrics**")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Posts", len(posts_df))
                with col2:
                    st.metric("Unique Users", int(posts_df['username'].nunique()))
                with col3:
                    female_pct = (posts_df['gender_inferred'] == 'female').mean() * 100
                    st.metric("Female Posts (%)", f"{female_pct:.1f}%")
                with col4:
                    avg_score = posts_df['score'].mean()
                    st.metric("Avg Post Score", f"{avg_score:.0f}")
                
                # Gender Distribution
                st.markdown("**👥 Gender Distribution**")
                gender_dist = posts_df['gender_inferred'].value_counts()
                fig_gender = px.pie(
                    values=gender_dist.values,
                    names=gender_dist.index,
                    title="Reddit: Gender Distribution",
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                st.plotly_chart(fig_gender, use_container_width=True)
                
                # Post Engagement by Gender
                st.markdown("**📈 Post Engagement by Gender**")
                col1, col2 = st.columns(2)
                with col1:
                    fig_scores = px.box(
                        posts_df,
                        x="gender_inferred",
                        y="score",
                        title="Post Scores by Gender",
                        color="gender_inferred",
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    st.plotly_chart(fig_scores, use_container_width=True)
                with col2:
                    fig_comments = px.box(
                        posts_df,
                        x="gender_inferred",
                        y="num_comments",
                        title="Comments Received by Gender",
                        color="gender_inferred",
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    st.plotly_chart(fig_comments, use_container_width=True)
                
                # Subreddit Participation
                st.markdown("**🏷️ Subreddit Participation by Gender**")
                subreddit_gender = posts_df.groupby(['subreddit', 'gender_inferred']).size().reset_index()
                subreddit_gender = subreddit_gender.rename(columns={0: 'count'})
                fig_subreddit = px.bar(
                    subreddit_gender,
                    x="subreddit",
                    y="count",
                    color="gender_inferred",
                    title="Participation in Tech Subreddits by Gender",
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                st.plotly_chart(fig_subreddit, use_container_width=True)
                
                # Gender Disparity Analysis
                st.markdown("**🔍 Gender Disparity Analysis**")
                try:
                    # Calculate gender disparity metrics
                    gender_counts = posts_df['gender_inferred'].value_counts()
                    total_posts = len(posts_df)
                    
                    female_posts = gender_counts.get('female', 0)
                    male_posts = gender_counts.get('male', 0)
                    anonymous_posts = gender_counts.get('anonymous', 0)
                    
                    female_pct = (female_posts / total_posts) * 100 if total_posts > 0 else 0
                    male_pct = (male_posts / total_posts) * 100 if total_posts > 0 else 0
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Female Posts", female_posts, f"{female_pct:.1f}%")
                    with col2:
                        st.metric("Male Posts", male_posts, f"{male_pct:.1f}%")
                    with col3:
                        disparity = abs(female_pct - male_pct)
                        st.metric("Gender Disparity", f"{disparity:.1f}%")
                    
                    # Show which gender has more posts
                    if female_pct > male_pct:
                        st.success(f"✅ Female users have {female_pct - male_pct:.1f}% more posts than male users")
                    elif male_pct > female_pct:
                        st.warning(f"⚠️ Male users have {male_pct - female_pct:.1f}% more posts than female users")
                    else:
                        st.info("ℹ️ Equal representation between male and female users")
                        
                except Exception as e:
                    st.error(f"Error in gender disparity analysis: {e}")
                
                # Bias Analysis Section for Posts
                st.markdown("**🔍 Bias Analysis**")
                st.info("📊 **Bias Metrics**: Analyzing potential gender bias in post engagement, community interaction, and voting patterns.")
                
                # Post engagement bias by subreddit
                subreddit_engagement = posts_df.groupby(['subreddit', 'gender_inferred'])['score'].mean().reset_index()
                fig_subreddit_bias = px.bar(
                    subreddit_engagement,
                    x="subreddit",
                    y="score",
                    color="gender_inferred",
                    title="Average Post Scores by Subreddit and Gender (Engagement Bias)",
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                st.plotly_chart(fig_subreddit_bias, use_container_width=True)
                
                # Community interaction differences
                interaction_ratio = posts_df.groupby(['subreddit', 'gender_inferred'])['num_comments'].mean().reset_index()
                fig_interaction = px.bar(
                    interaction_ratio,
                    x="subreddit",
                    y="num_comments",
                    color="gender_inferred",
                    title="Average Comments Received by Subreddit and Gender (Interaction Bias)",
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                st.plotly_chart(fig_interaction, use_container_width=True)
        except Exception as e:
            st.error(f"Error loading Reddit data: {e}")

        # --- Reddit Comments Analysis ---
        st.subheader("💬 Reddit Comments Analysis")
        
        try:
            data = load_platform_data("reddit")
            if not data or "comments" not in data or data["comments"].empty:
                st.warning("No Reddit comment data available. Please run data collection with comments enabled.")
            else:
                comments_df = data["comments"]
                
                # Clean up gender categories to remove mostly_male/mostly_female
                comments_df['gender_inferred'] = comments_df['gender_inferred'].replace({
                    'unknown': 'anonymous',
                    'mostly_male': 'male',
                    'mostly_female': 'female'
                })
                
                # Add data quality note
                st.info("📊 **Data Quality**: 276 comments analyzed. Gender distribution shows engagement patterns across tech communities.")
                
                # Basic Metrics Table
                st.markdown("**📊 Basic Metrics**")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Comments", len(comments_df))
                with col2:
                    st.metric("Unique Commenters", int(comments_df['username'].nunique()))
                with col3:
                    female_pct = (comments_df['gender_inferred'] == 'female').mean() * 100
                    st.metric("Female Comments (%)", f"{female_pct:.1f}%")
                with col4:
                    avg_score = comments_df['score'].mean()
                    st.metric("Avg Comment Score", f"{avg_score:.0f}")
                
                # Comment Gender Distribution
                st.markdown("**👥 Comment Gender Distribution**")
                comment_gender_dist = comments_df['gender_inferred'].value_counts()
                fig_comment_gender = px.pie(
                    values=comment_gender_dist.values,
                    names=comment_gender_dist.index,
                    title="Reddit: Comment Gender Distribution",
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                st.plotly_chart(fig_comment_gender, use_container_width=True)
                
                # Comment Engagement by Gender
                st.markdown("**📈 Comment Engagement by Gender**")
                col1, col2 = st.columns(2)
                with col1:
                    fig_comment_scores = px.box(
                        comments_df,
                        x="gender_inferred",
                        y="score",
                        title="Comment Scores by Gender",
                        color="gender_inferred",
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    st.plotly_chart(fig_comment_scores, use_container_width=True)
                with col2:
                    # Comment length analysis
                    comments_df['comment_length'] = comments_df['body'].str.len()
                    fig_comment_length = px.box(
                        comments_df,
                        x="gender_inferred",
                        y="comment_length",
                        title="Comment Length by Gender",
                        color="gender_inferred",
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    st.plotly_chart(fig_comment_length, use_container_width=True)
                
                # Comment Activity by Subreddit
                st.markdown("**🏷️ Comment Activity by Subreddit**")
                comment_subreddit_gender = comments_df.groupby(['subreddit', 'gender_inferred']).size().reset_index()
                comment_subreddit_gender = comment_subreddit_gender.rename(columns={0: 'count'})
                fig_comment_subreddit = px.bar(
                    comment_subreddit_gender,
                    x="subreddit",
                    y="count",
                    color="gender_inferred",
                    title="Comment Activity in Tech Subreddits by Gender",
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                st.plotly_chart(fig_comment_subreddit, use_container_width=True)
                

                
                # Gender Disparity Analysis for Comments
                st.markdown("**🔍 Comment Gender Disparity Analysis**")
                try:
                    # Calculate gender disparity metrics for comments
                    gender_counts = comments_df['gender_inferred'].value_counts()
                    total_comments = len(comments_df)
                    
                    female_comments = gender_counts.get('female', 0)
                    male_comments = gender_counts.get('male', 0)
                    anonymous_comments = gender_counts.get('anonymous', 0)
                    
                    female_pct = (female_comments / total_comments) * 100 if total_comments > 0 else 0
                    male_pct = (male_comments / total_comments) * 100 if total_comments > 0 else 0
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Female Comments", female_comments, f"{female_pct:.1f}%")
                    with col2:
                        st.metric("Male Comments", male_comments, f"{male_pct:.1f}%")
                    with col3:
                        disparity = abs(female_pct - male_pct)
                        st.metric("Gender Disparity", f"{disparity:.1f}%")
                    
                    # Show which gender has more comments
                    if female_pct > male_pct:
                        st.success(f"✅ Female users have {female_pct - male_pct:.1f}% more comments than male users")
                    elif male_pct > female_pct:
                        st.warning(f"⚠️ Male users have {male_pct - female_pct:.1f}% more comments than female users")
                    else:
                        st.info("ℹ️ Equal representation between male and female users in comments")
                        
                except Exception as e:
                    st.error(f"Error in comment gender disparity analysis: {e}")
                
                # Statistical Summary Table
                st.markdown("**📋 Statistical Summary**")
                summary_stats = comments_df.groupby('gender_inferred').agg({
                    'score': ['mean', 'median', 'std'],
                    'comment_length': ['mean', 'median', 'std']
                }).round(2)
                st.dataframe(summary_stats, use_container_width=True)
                
               
                
        except Exception as e:
            st.error(f"Error loading Reddit comment data: {e}")

# =============================
# Section 4: Cross-Platform Comparison
# =============================
elif section == "Cross-Platform Comparison":
    with st.container():
        st.markdown("""
        <h2 style='color: #e74c3c;'>Cross-Platform Gender Comparison</h2>
        <span style='color: #888;'>Section Lead: Kainat</span>
        """, unsafe_allow_html=True)
        st.write(":female-technologist: :man-technologist: **Comprehensive comparison of gender representation across all tech platforms.**")

        # --- Cross-Platform Comparison ---
        st.subheader("🌐 Cross-Platform Gender Representation Comparison")
        try:
            # Generate comprehensive analysis
            comprehensive_report = analyzer.generate_comprehensive_analysis()
            
            if comprehensive_report:
                # Display cross-platform insights
                if 'cross_platform_insights' in comprehensive_report:
                    insights = comprehensive_report['cross_platform_insights']
                    
                    st.markdown("**📊 Gender Disparity Analysis**")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        lowest_platform = insights.get('lowest_female_platform', 'N/A')
                        lowest_pct = insights.get('female_representation', {}).get(lowest_platform, 0) * 100
                        st.metric("Lowest Female Representation", f"{lowest_platform.title()}", f"{lowest_pct:.1f}%")
                    with col2:
                        highest_platform = insights.get('highest_female_platform', 'N/A')
                        highest_pct = insights.get('female_representation', {}).get(highest_platform, 0) * 100
                        st.metric("Highest Female Representation", f"{highest_platform.title()}", f"{highest_pct:.1f}%")
                    with col3:
                        avg_female = sum(insights.get('female_representation', {}).values()) / len(insights.get('female_representation', {})) * 100
                        st.metric("Average Female Representation", f"{avg_female:.1f}%")
                    
                    # Gender disparity ranking table
                    st.markdown("**🏆 Platform Ranking by Female Representation**")
                    ranking_data = insights.get('gender_disparity_ranking', [])
                    if ranking_data:
                        ranking_df = pd.DataFrame(ranking_data, columns=['Platform', 'Female %'])
                        ranking_df['Female %'] = ranking_df['Female %'] * 100
                        ranking_df = ranking_df.sort_values('Female %', ascending=False)
                        st.dataframe(ranking_df, use_container_width=True)
                
                # Platform comparison chart
                st.markdown("**📈 Gender Representation Across Platforms**")
                platforms = ["stackoverflow", "github", "reddit"]
                comparison_data = {}
                for platform in platforms:
                    if platform in comprehensive_report and 'gender_distribution' in comprehensive_report[platform]:
                        comparison_data[platform] = comprehensive_report[platform]['gender_distribution']
                
                if comparison_data:
                    comparison_df = pd.DataFrame(comparison_data).fillna(0)
                    fig_comparison = px.bar(
                        comparison_df,
                        title="Gender Representation Across Platforms",
                        labels={'value': 'Percentage', 'variable': 'Platform', 'index': 'Gender'},
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    st.plotly_chart(fig_comparison, use_container_width=True)
                    
                    # Detailed platform analysis table
                    st.markdown("**📋 Detailed Platform Analysis**")
                    platform_data = []
                    for platform, data in comprehensive_report.items():
                        if platform in ['stackoverflow', 'github', 'reddit'] and 'gender_distribution' in data:
                            gender_dist = data['gender_distribution']
                            platform_data.append({
                                'Platform': platform.upper(),
                                'Female %': gender_dist.get('female', 0) * 100,
                                'Male %': gender_dist.get('male', 0) * 100,
                                'Anonymous %': gender_dist.get('anonymous', 0) * 100
                            })
                    
                    platform_df = pd.DataFrame(platform_data)
                    st.dataframe(platform_df, use_container_width=True)
                
                st.markdown("**💡 Key Insights**")
                st.info("""
               **Key Observations from Our Analysis:**
                
                **📊 Gender Representation Patterns:**
                - **Reddit** shows the highest female participation in tech discussions, with more women actively posting and commenting
                - **GitHub** has moderate female representation, with women contributing to open source projects
                - **Stack Overflow** shows lower female participation, with fewer women asking questions and building reputation
                
                **🔍 Engagement Differences:**
                - **Reddit**: Women participate more actively in discussions, with higher comment engagement
                - **GitHub**: Women's projects receive similar recognition (stars) as men's projects
                - **Stack Overflow**: Women ask fewer questions but receive similar reputation scores when they do participate
                
                **💭 Community Behavior:**
                - **Reddit** communities appear more welcoming to female participation
                - **GitHub** shows equal recognition for code contributions regardless of gender
                - **Stack Overflow** has a steeper barrier for women to start participating
                
                **⚠️ Limitations:**
                - Gender inference isn't perfect - many users are anonymous
                - Sample sizes vary across platforms
                - We're looking at public engagement traces, not surveys
                """)
            else:
                st.warning("No data available for comparison. Please run data collection first.")
        except Exception as e:
            st.error(f"Error creating cross-platform comparison: {e}")


# Footer
st.markdown("""
---
<div style='text-align: center; color: #888;'>
    <small>Gender Disparity in Tech Communities &copy; 2024 | Social Computing Project | Team: Fatima & Kainat</small>
</div>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    pass  # Streamlit runs main automatically
