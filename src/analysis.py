import pandas as pd
import numpy as np
import sqlite3
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import plotly.express as px
import gender_guesser.detector as gender

class SocialComputingAnalysis:
    """
    Class to perform analysis on gender disparity in tech communities
    using traces of online engagement
    """
    def __init__(self, db_path: str = "data/social_computing.db", output_dir: str = "visualizations"):
        self.db_path = Path(db_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.detector = gender.Detector()
        
    def load_platform_data(self, platform: str) -> Dict[str, pd.DataFrame]:
        """Load data from SQLite database for a specific platform"""
        print("Requested platform:", platform)
        print("Platform type:", type(platform))
        print("Platform comparison with 'reddit':", platform == "reddit")
        
        conn = sqlite3.connect(self.db_path)
        if platform == "stackoverflow":
            print("Loading Stack Overflow data...")
            users_df = pd.read_sql_query("SELECT * FROM stackoverflow_users", conn)
            users_df['gender_inferred'] = users_df['gender_inferred'].replace('unknown', 'anonymous')
            questions_df = pd.read_sql_query("SELECT * FROM stackoverflow_questions", conn)
            questions_df['gender_inferred'] = questions_df['gender_inferred'].replace('unknown', 'anonymous')

            # Compute question_count and answer_count for each user
            print("Computing question_count and answer_count for each user...")
            question_counts = questions_df.groupby('user_id').size().to_frame('question_count')
            print(f"Question counts shape: {question_counts.shape}")
            print(f"Question counts head: {question_counts.head()}")
            
            # Note: answer_count cannot be computed from current data structure
            # as we don't have answer_user_id column
            answer_counts = pd.DataFrame({'answer_count': 0}, index=question_counts.index)
            print(f"Answer counts shape: {answer_counts.shape}")
            
            # Check if columns already exist in users_df
            print(f"Users_df shape before merge: {users_df.shape}")
            print(f"Users_df columns before merge: {list(users_df.columns)}")
            
            # If question_count already exists, update it; otherwise add it
            if 'question_count' in users_df.columns:
                print("question_count column already exists, updating values...")
                # Create a mapping from user_id to question_count
                question_map = question_counts['question_count'].to_dict()
                users_df['question_count'] = users_df['user_id'].map(question_map).fillna(0).astype(int)
            else:
                print("Adding question_count column...")
                users_df = users_df.merge(question_counts, how='left', left_on='user_id', right_index=True)
                users_df['question_count'] = users_df['question_count'].fillna(0).astype(int)
            
            # If answer_count already exists, update it; otherwise add it
            if 'answer_count' in users_df.columns:
                print("answer_count column already exists, setting to 0...")
                users_df['answer_count'] = 0
            else:
                print("Adding answer_count column...")
                users_df = users_df.merge(answer_counts, how='left', left_on='user_id', right_index=True)
                users_df['answer_count'] = users_df['answer_count'].fillna(0).astype(int)
            
            print(f"Final users_df columns: {list(users_df.columns)}")
            print(f"Question count sample: {users_df['question_count'].head()}")
            print(f"Answer count sample: {users_df['answer_count'].head()}")

            result = {"users": users_df, "questions": questions_df}
            print("Stack Overflow result keys:", list(result.keys()))
            conn.close()
            return result
        elif platform == "github":
            print("Loading GitHub data...")
            users_df = pd.read_sql_query("SELECT * FROM github_users", conn)
            users_df['gender_inferred'] = users_df['gender_inferred'].replace('unknown', 'anonymous')
            repos_df = pd.read_sql_query("SELECT * FROM github_repositories", conn)
            repos_df['gender_inferred'] = repos_df['gender_inferred'].replace('unknown', 'anonymous')
            result = {"users": users_df, "repositories": repos_df}
            print("GitHub result keys:", list(result.keys()))
            conn.close()
            return result
        elif platform == "reddit":
            print("Loading Reddit data...")
            posts_df = pd.read_sql_query("SELECT * FROM reddit_posts", conn)
            posts_df['gender_inferred'] = posts_df['gender_inferred'].replace('unknown', 'anonymous')
            
            # Load comments if they exist
            try:
                comments_df = pd.read_sql_query("SELECT * FROM reddit_comments", conn)
                comments_df['gender_inferred'] = comments_df['gender_inferred'].replace('unknown', 'anonymous')
                result = {"posts": posts_df, "comments": comments_df}
                print("Reddit result keys:", list(result.keys()))
                print("Reddit posts shape:", posts_df.shape)
                print("Reddit comments shape:", comments_df.shape)
            except Exception as e:
                print(f"No comments table found: {e}")
                result = {"posts": posts_df}
                print("Reddit result keys:", list(result.keys()))
                print("Reddit posts shape:", posts_df.shape)
            
            conn.close()
            return result
        else:
            print(f"Unknown platform: '{platform}'")
            conn.close()
            return {}
    
    def infer_gender_enhanced(self, username: str) -> str:
        """
        Enhanced gender inference using multiple methods
        Based on comment_gender_analysis.py logic
        """
        if pd.isna(username) or username == 'None' or username.lower() in ['deleted', 'anonymous', 'unknown', 'none']:
            return 'anonymous'
        
        username_lower = username.lower()
        
        # Method 1: Use gender_guesser library (from comment_gender_analysis.py)
        name_parts = username.replace('_', ' ').replace('-', ' ').split()
        
        for part in name_parts:
            cleaned = ''.join(filter(str.isalpha, part))  # Keep letters only
            if len(cleaned) >= 3:
                guess = self.detector.get_gender(cleaned.lower().capitalize())
                if guess not in ['unknown', 'andy']:
                    return guess
        
        # Method 2: Pattern matching
        female_indicators = [
            'sarah', 'emma', 'olivia', 'ava', 'isabella', 'sophia', 'charlotte', 'mia', 
            'amelia', 'harper', 'evelyn', 'abigail', 'emily', 'elizabeth', 'sofia', 
            'madison', 'avery', 'ella', 'scarlett', 'grace', 'chloe', 'camila', 'penelope',
            'layla', 'riley', 'lillian', 'nora', 'zoey', 'mila', 'aubrey', 'hannah',
            'lily', 'addison', 'eleanor', 'natalie', 'luna', 'savannah', 'brooklyn',
            'leah', 'zoe', 'stella', 'hazel', 'ellie', 'paisley', 'audrey', 'skylar',
            'violet', 'claire', 'bella', 'aurora', 'lucy', 'anna', 'samantha'
        ]
        
        male_indicators = [
            'james', 'john', 'robert', 'michael', 'william', 'david', 'richard', 
            'joseph', 'thomas', 'christopher', 'charles', 'daniel', 'matthew', 
            'anthony', 'mark', 'donald', 'steven', 'paul', 'andrew', 'joshua',
            'kenneth', 'kevin', 'brian', 'george', 'edward', 'ronald', 'timothy',
            'jason', 'jeffrey', 'ryan', 'jacob', 'gary', 'nicholas', 'eric',
            'jonathan', 'stephen', 'larry', 'justin', 'scott', 'brandon', 'benjamin',
            'samuel', 'frank', 'gregory', 'raymond', 'alexander', 'patrick', 'jack',
            'dennis', 'jerry', 'tyler', 'aaron', 'jose', 'adam', 'nathan', 'henry',
            'douglas', 'zachary', 'peter', 'kyle', 'walter', 'ethan', 'jeremy',
            'harold', 'carl', 'keith', 'roger', 'gerald', 'christian', 'terry',
            'sean', 'arthur', 'austin', 'noah', 'lawrence', 'jesse', 'joe', 'bryan',
            'billy', 'jordan', 'albert', 'dylan', 'bruce', 'willie', 'gabriel',
            'logan', 'alan', 'juan', 'wayne', 'roy', 'ralph', 'randy', 'eugene',
            'vincent', 'russell', 'elijah', 'louis', 'bobby', 'philip', 'johnny'
        ]
        
        if any(indicator in username_lower for indicator in female_indicators):
            return 'female'
        elif any(indicator in username_lower for indicator in male_indicators):
            return 'male'
        
        # Method 3: Gender-specific patterns
        if any(pattern in username_lower for pattern in ['girl', 'woman', 'lady', 'ms', 'miss', 'mrs', 'she', 'her']):
            return 'female'
        elif any(pattern in username_lower for pattern in ['guy', 'man', 'mr', 'dude', 'he', 'his', 'boy']):
            return 'male'
        
        # Method 4: Check for gender-specific usernames
        if any(pattern in username_lower for pattern in ['queen', 'princess', 'goddess', 'diva']):
            return 'female'
        elif any(pattern in username_lower for pattern in ['king', 'prince', 'god', 'dude']):
            return 'male'
        
        return 'anonymous'
    
    def analyze_comment_gender_patterns(self, comments_df: pd.DataFrame) -> Dict:
        """
        Analyze comment gender patterns based on comment_gender_charts.py logic
        """
        if comments_df.empty:
            return {}
        
        # Filter to only include male, female, and anonymous (our three categories)
        # Also filter out any mostly_male/mostly_female and convert to male/female
        df_filtered = comments_df.copy()
        df_filtered['gender_inferred'] = df_filtered['gender_inferred'].replace({
            'mostly_male': 'male',
            'mostly_female': 'female',
            'unknown': 'anonymous'
        })
        df_filtered = df_filtered[df_filtered['gender_inferred'].isin(['male', 'female', 'anonymous'])]
        
        if df_filtered.empty:
            return {}
        
        # Count genders
        gender_counts = df_filtered['gender_inferred'].value_counts()
        
        # Average score by gender
        score_by_gender = df_filtered.groupby('gender_inferred')['score'].mean()
        
        # Comment length analysis
        df_filtered['comment_length'] = df_filtered['body'].str.len()
        length_by_gender = df_filtered.groupby('gender_inferred')['comment_length'].mean()
        
        return {
            'gender_counts': gender_counts.to_dict(),
            'score_by_gender': score_by_gender.to_dict(),
            'length_by_gender': length_by_gender.to_dict(),
            'total_comments': len(df_filtered),
            'unique_commenters': df_filtered['username'].nunique()
        }
    
    def analyze_post_gender_patterns(self, posts_df: pd.DataFrame) -> Dict:
        """
        Analyze post gender patterns based on gender_analysis_charts.py logic
        """
        if posts_df.empty:
            return {}
        
        # Count how many of each gender
        gender_counts = posts_df['gender_inferred'].value_counts()
        
        # Group by gender and calculate average post score
        score_by_gender = posts_df.groupby('gender_inferred')['score'].mean()
        
        # Additional analysis
        engagement_by_gender = posts_df.groupby('gender_inferred').agg({
            'score': ['mean', 'median', 'std'],
            'num_comments': ['mean', 'median', 'std']
        }).round(2)
        
        return {
            'gender_counts': gender_counts.to_dict(),
            'score_by_gender': score_by_gender.to_dict(),
            'engagement_by_gender': engagement_by_gender.to_dict(),
            'total_posts': len(posts_df),
            'unique_authors': posts_df['username'].nunique()
        }
    
    def update_gender_inference_enhanced(self):
        """
        Update all tables with enhanced gender inference
        """
        conn = sqlite3.connect(self.db_path)
        
        # Update Reddit posts
        posts_df = pd.read_sql_query("SELECT * FROM reddit_posts", conn)
        posts_df['gender_inferred_enhanced'] = posts_df['username'].apply(self.infer_gender_enhanced)
        
        for idx, row in posts_df.iterrows():
            conn.execute(
                "UPDATE reddit_posts SET gender_inferred = ? WHERE post_id = ?",
                (row['gender_inferred_enhanced'], row['post_id'])
            )
        
        # Update Reddit comments if they exist
        try:
            comments_df = pd.read_sql_query("SELECT * FROM reddit_comments", conn)
            comments_df['gender_inferred_enhanced'] = comments_df['username'].apply(self.infer_gender_enhanced)
            
            for idx, row in comments_df.iterrows():
                conn.execute(
                    "UPDATE reddit_comments SET gender_inferred = ? WHERE comment_id = ?",
                    (row['gender_inferred_enhanced'], row['comment_id'])
                )
        except Exception as e:
            print(f"No comments table found: {e}")
        
        # Update Stack Overflow users
        try:
            users_df = pd.read_sql_query("SELECT * FROM stackoverflow_users", conn)
            users_df['gender_inferred_enhanced'] = users_df['username'].apply(self.infer_gender_enhanced)
            
            for idx, row in users_df.iterrows():
                conn.execute(
                    "UPDATE stackoverflow_users SET gender_inferred = ? WHERE user_id = ?",
                    (row['gender_inferred_enhanced'], row['user_id'])
                )
        except Exception as e:
            print(f"Error updating Stack Overflow users: {e}")
        
        # Update GitHub users
        try:
            gh_users_df = pd.read_sql_query("SELECT * FROM github_users", conn)
            gh_users_df['gender_inferred_enhanced'] = gh_users_df['username'].apply(self.infer_gender_enhanced)
            
            for idx, row in gh_users_df.iterrows():
                conn.execute(
                    "UPDATE github_users SET gender_inferred = ? WHERE user_id = ?",
                    (row['gender_inferred_enhanced'], row['user_id'])
                )
        except Exception as e:
            print(f"Error updating GitHub users: {e}")
        
        conn.commit()
        conn.close()
        print("✅ Enhanced gender inference applied to all tables")
    
    def analyze_engagement_patterns(self, platform: str) -> Dict:
        """Analyze engagement patterns by gender across platforms"""
        data = self.load_platform_data(platform)
        
        if platform == "stackoverflow":
            return self._analyze_stackoverflow_engagement(data)
        elif platform == "github":
            return self._analyze_github_engagement(data)
        elif platform == "reddit":
            return self._analyze_reddit_engagement(data)
        
        return {}
    
    def _analyze_stackoverflow_engagement(self, data: Dict) -> Dict:
        """Analyze Stack Overflow engagement patterns using enhanced gender analysis"""
        users_df = data["users"]
        questions_df = data["questions"]
        
        # Apply enhanced gender inference and clean up gender categories
        users_df['gender_inferred'] = users_df['username'].apply(self.infer_gender_enhanced)
        users_df['gender_inferred'] = users_df['gender_inferred'].replace({
            'mostly_male': 'male',
            'mostly_female': 'female',
            'unknown': 'anonymous'
        })
        questions_df['gender_inferred'] = questions_df['user_id'].map(users_df.set_index('user_id')['gender_inferred'])
        
        # Gender distribution
        gender_dist = users_df['gender_inferred'].value_counts(normalize=True)
        
        # Activity patterns by gender
        activity_by_gender = users_df.groupby('gender_inferred').agg({
            'reputation': ['mean', 'median', 'std'],
            'question_count': ['mean', 'median', 'std'],
            'answer_count': ['mean', 'median', 'std'],
            'badge_count': ['mean', 'median', 'std']
        }).round(2)
        
        return {
            'gender_distribution': gender_dist.to_dict(),
            'user_activity': activity_by_gender.to_dict()
        }
    
    def _analyze_github_engagement(self, data: Dict) -> Dict:
        """Analyze GitHub engagement patterns using enhanced gender analysis"""
        users_df = data["users"]
        repos_df = data["repositories"]
        
        # Apply enhanced gender inference and clean up gender categories
        users_df['gender_inferred'] = users_df['username'].apply(self.infer_gender_enhanced)
        users_df['gender_inferred'] = users_df['gender_inferred'].replace({
            'mostly_male': 'male',
            'mostly_female': 'female',
            'unknown': 'anonymous'
        })
        repos_df['gender_inferred'] = repos_df['user_id'].map(users_df.set_index('user_id')['gender_inferred'])
        
        # Gender distribution
        gender_dist = users_df['gender_inferred'].value_counts(normalize=True)
        
        # User activity patterns
        user_activity = users_df.groupby('gender_inferred').agg({
            'public_repos': ['mean', 'median', 'std'],
            'followers': ['mean', 'median', 'std'],
            'following': ['mean', 'median', 'std']
        }).round(2)
        
        # Repository stars by gender
        repo_stars = None
        language_gender = None
        if not repos_df.empty:
            repo_stars = repos_df.groupby('gender_inferred')['stars'].agg(['mean', 'median', 'std']).round(2).to_dict()
            # Language trends by gender
            language_gender = repos_df.groupby(['language', 'gender_inferred']).size().unstack(fill_value=0).to_dict()
        
        return {
            'gender_distribution': gender_dist.to_dict(),
            'user_activity': user_activity.to_dict(),
            'repo_stars': repo_stars,
            'language_gender': language_gender
        }
    
    def _analyze_reddit_engagement(self, data: Dict) -> Dict:
        """Analyze Reddit engagement patterns using enhanced gender analysis"""
        if not data or "posts" not in data or data["posts"].empty:
            return {}
        
        posts_df = data["posts"]
        
        # Apply enhanced gender inference and clean up gender categories
        posts_df['gender_inferred'] = posts_df['username'].apply(self.infer_gender_enhanced)
        posts_df['gender_inferred'] = posts_df['gender_inferred'].replace({
            'mostly_male': 'male',
            'mostly_female': 'female',
            'unknown': 'anonymous'
        })
        
        # Analyze post patterns using gender_analysis_charts.py logic
        post_analysis = self.analyze_post_gender_patterns(posts_df)
        
        result = {
            'gender_distribution': posts_df['gender_inferred'].value_counts(normalize=True).to_dict(),
            'post_analysis': post_analysis
        }
        
        # Add comment analysis if available
        if "comments" in data and not data["comments"].empty:
            comments_df = data["comments"]
            
            # Apply enhanced gender inference to comments and clean up gender categories
            comments_df['gender_inferred'] = comments_df['username'].apply(self.infer_gender_enhanced)
            comments_df['gender_inferred'] = comments_df['gender_inferred'].replace({
                'mostly_male': 'male',
                'mostly_female': 'female',
                'unknown': 'anonymous'
            })
            
            # Analyze comment patterns using comment_gender_charts.py logic
            comment_analysis = self.analyze_comment_gender_patterns(comments_df)
            
            result.update({
                'comment_analysis': comment_analysis,
                'comment_gender_distribution': comments_df['gender_inferred'].value_counts(normalize=True).to_dict()
            })
        
        return result
    
    def create_visualizations(self, platform: str):
        """Create visualizations for engagement patterns"""
        data = self.load_platform_data(platform)
        
        if platform == "stackoverflow":
            self._create_stackoverflow_visualizations(data)
        elif platform == "github":
            self._create_github_visualizations(data)
        elif platform == "reddit":
            self._create_reddit_visualizations(data)
    
    def _create_stackoverflow_visualizations(self, data: Dict):
        """Create Stack Overflow visualizations"""
        users_df = data["users"]
        
        # Gender distribution pie chart
        fig_gender = px.pie(
            values=users_df['gender_inferred'].value_counts().values,
            names=users_df['gender_inferred'].value_counts().index,
            title="Stack Overflow: Gender Distribution"
        )
        fig_gender.write_html(self.output_dir / "stackoverflow_gender_distribution.html")
        
        # Reputation distribution by gender
        fig_reputation = px.box(
            users_df, 
            x="gender_inferred", 
            y="reputation",
            title="Stack Overflow: Reputation Distribution by Gender"
        )
        fig_reputation.write_html(self.output_dir / "stackoverflow_reputation_distribution.html")
    
    def _create_github_visualizations(self, data: Dict):
        """Create GitHub visualizations"""
        users_df = data["users"]
        repos_df = data["repositories"]
        
        # Gender distribution
        fig_gender = px.pie(
            values=users_df['gender_inferred'].value_counts().values,
            names=users_df['gender_inferred'].value_counts().index,
            title="GitHub: Gender Distribution"
        )
        fig_gender.write_html(self.output_dir / "github_gender_distribution.html")
        
        # Repository stars by gender
        fig_stars = px.box(
            repos_df,
            x="gender_inferred",
            y="stars",
            title="GitHub: Repository Stars by Gender"
        )
        fig_stars.write_html(self.output_dir / "github_stars_distribution.html")
    
    def _create_reddit_visualizations(self, data: Dict):
        """Create Reddit visualizations"""
        posts_df = data["posts"]
        
        # Gender distribution
        fig_gender = px.pie(
            values=posts_df['gender_inferred'].value_counts().values,
            names=posts_df['gender_inferred'].value_counts().index,
            title="Reddit: Gender Distribution"
        )
        fig_gender.write_html(self.output_dir / "reddit_gender_distribution.html")
        
        # Post scores by gender
        fig_scores = px.box(
            posts_df,
            x="gender_inferred",
            y="score",
            title="Reddit: Post Scores by Gender"
        )
        fig_scores.write_html(self.output_dir / "reddit_scores_distribution.html")
        
        # Comment visualizations if available
        if "comments" in data and not data["comments"].empty:
            comments_df = data["comments"]
            
            # Comment gender distribution
            fig_comment_gender = px.pie(
                values=comments_df['gender_inferred'].value_counts().values,
                names=comments_df['gender_inferred'].value_counts().index,
                title="Reddit: Comment Gender Distribution"
            )
            fig_comment_gender.write_html(self.output_dir / "reddit_comment_gender_distribution.html")
            
            # Comment scores by gender
            fig_comment_scores = px.box(
                comments_df,
                x="gender_inferred",
                y="score",
                title="Reddit: Comment Scores by Gender"
            )
            fig_comment_scores.write_html(self.output_dir / "reddit_comment_scores_distribution.html")
    
    def generate_report(self) -> Dict:
        """Generate a comprehensive analysis report"""
        report = {
            'stackoverflow': self.analyze_engagement_patterns("stackoverflow"),
            'github': self.analyze_engagement_patterns("github"),
            'reddit': self.analyze_engagement_patterns("reddit")
        }
        
        # Create visualizations
        for platform in ["stackoverflow", "github", "reddit"]:
            self.create_visualizations(platform)
        
        return report
    
    def generate_comprehensive_analysis(self) -> Dict:
        """
        Generate comprehensive analysis with detailed insights
        """
        report = {}
        
        # Analyze each platform
        for platform in ["stackoverflow", "github", "reddit"]:
            data = self.load_platform_data(platform)
            analysis = self.analyze_engagement_patterns(platform)
            
            if platform == "reddit":
                # Add comment analysis for Reddit
                if "comments" in data and not data["comments"].empty:
                    comments_df = data["comments"]
                    comments_df['comment_length'] = comments_df['body'].str.len()
                    
                    comment_analysis = {
                        'total_comments': len(comments_df),
                        'unique_commenters': comments_df['username'].nunique(),
                        'gender_distribution': comments_df['gender_inferred'].value_counts(normalize=True).to_dict(),
                        'score_by_gender': comments_df.groupby('gender_inferred')['score'].mean().to_dict(),
                        'length_by_gender': comments_df.groupby('gender_inferred')['comment_length'].mean().to_dict(),
                        'subreddit_activity': comments_df.groupby(['subreddit', 'gender_inferred']).size().unstack(fill_value=0).to_dict()
                    }
                    analysis['comment_analysis'] = comment_analysis
            
            report[platform] = analysis
        
        # Cross-platform comparison
        platform_comparison = {}
        for platform, data in report.items():
            if 'gender_distribution' in data:
                platform_comparison[platform] = data['gender_distribution']
        
        # Find platform with lowest female representation
        female_representation = {}
        for platform, gender_dist in platform_comparison.items():
            female_pct = gender_dist.get('female', 0)
            female_representation[platform] = female_pct
        
        if female_representation:
            lowest_female_platform = min(female_representation, key=female_representation.get)
            highest_female_platform = max(female_representation, key=female_representation.get)
            
            report['cross_platform_insights'] = {
                'female_representation': female_representation,
                'lowest_female_platform': lowest_female_platform,
                'highest_female_platform': highest_female_platform,
                'gender_disparity_ranking': sorted(female_representation.items(), key=lambda x: x[1])
            }
        
        return report

def main():
    """Main function to run analysis"""
    analyzer = SocialComputingAnalysis()
    
    print("Generating analysis report...")
    report = analyzer.generate_report()
    
    print("\n=== KEY FINDINGS ===")
    for platform, data in report.items():
        print(f"\n{platform.upper()}:")
        if 'gender_distribution' in data:
            print(f"  Gender Distribution: {data['gender_distribution']}")
    
    print(f"\nVisualizations saved to: {analyzer.output_dir}")

if __name__ == "__main__":
    main()
