import requests
import pandas as pd
import sqlite3
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import os
from dotenv import load_dotenv
import praw
from github import Github
import json
from pathlib import Path
import numpy as np

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SocialComputingDataCollector:
    """
    Collects traces of online engagement from various tech platforms
    following social computing methodology
    """
    
    def __init__(self, db_path: str = "data/social_computing.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.setup_database()
        
        # Initialize API clients
        self.setup_api_clients()
        
      
        
    def setup_database(self):
        """Initialize SQLite database for storing collected traces"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables for different platforms
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stackoverflow_users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                reputation INTEGER,
                creation_date TEXT,
                last_access_date TEXT,
                question_count INTEGER,
                answer_count INTEGER,
                badge_count INTEGER,
                gender_inferred TEXT,
                collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stackoverflow_questions (
                question_id INTEGER PRIMARY KEY,
                user_id INTEGER,
                title TEXT,
                tags TEXT,
                score INTEGER,
                view_count INTEGER,
                answer_count INTEGER,
                creation_date TEXT,
                gender_inferred TEXT,
                collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES stackoverflow_users (user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS github_users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                public_repos INTEGER,
                followers INTEGER,
                following INTEGER,
                created_at TEXT,
                updated_at TEXT,
                bio TEXT,
                location TEXT,
                gender_inferred TEXT,
                collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS github_repositories (
                repo_id INTEGER PRIMARY KEY,
                user_id INTEGER,
                name TEXT,
                description TEXT,
                language TEXT,
                stars INTEGER,
                forks INTEGER,
                created_at TEXT,
                updated_at TEXT,
                gender_inferred TEXT,
                collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES github_users (user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reddit_posts (
                post_id TEXT PRIMARY KEY,
                username TEXT,
                subreddit TEXT,
                title TEXT,
                selftext TEXT,
                score INTEGER,
                num_comments INTEGER,
                created_utc INTEGER,
                gender_inferred TEXT,
                collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reddit_comments (
                comment_id TEXT PRIMARY KEY,
                post_id TEXT,
                username TEXT,
                subreddit TEXT,
                body TEXT,
                score INTEGER,
                created_utc INTEGER,
                gender_inferred TEXT,
                collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES reddit_posts (post_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def setup_api_clients(self):
        """Initialize API clients for different platforms"""
        # Stack Exchange API
        self.stack_exchange_key = os.getenv('STACK_EXCHANGE_API_KEY')
        self.stack_exchange_base_url = "https://api.stackexchange.com/2.3"
        
        # GitHub API
        github_token = os.getenv('GITHUB_TOKEN')
        if github_token:
            self.github_client = Github(github_token)
        else:
            self.github_client = None
            logger.warning("GitHub token not found. GitHub data collection will be limited.")
        
        # Reddit API
        reddit_client_id = os.getenv('REDDIT_CLIENT_ID')
        reddit_client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        if reddit_client_id and reddit_client_secret:
            self.reddit_client = praw.Reddit(
                client_id=reddit_client_id,
                client_secret=reddit_client_secret,
                user_agent="GenderDisparityAnalysis/1.0"
            )
        else:
            self.reddit_client = None
            logger.warning("Reddit credentials not found. Reddit data collection will be limited.")
    
    def collect_stackoverflow_data(self, tags: Optional[List[str]] = None, max_users: int = 500):
        """
        Collect Stack Overflow user activity traces
        """
        logger.info("Starting Stack Overflow data collection...")
        
        if not tags:
            tags = ['python', 'javascript', 'java', 'c++', 'c#']
        
        user_count = 0
        for tag in tags:
            if user_count >= max_users:
                break
            logger.info(f"Collecting data for tag: {tag}")
            
            # Get questions for the tag
            questions_url = f"{self.stack_exchange_base_url}/questions"
            params = {
                'tagged': tag,
                'site': 'stackoverflow',
                'pagesize': 100,
                'sort': 'votes',
                'order': 'desc',
                'key': self.stack_exchange_key
            }
            
            try:
                response = requests.get(questions_url, params=params)
                response.raise_for_status()
                data = response.json()
               
                for question in data['items']:
                    owner = question.get('owner', {})
                    user_id = owner.get('user_id')
                    if not user_id:
                        continue
                    if user_count >= max_users:
                        break
                    self._collect_stackoverflow_user(user_id)
                    self._store_stackoverflow_question(question)
                    user_count += 1
                    time.sleep(0.1)  # Respect rate limits
                
            except Exception as e:
                logger.error(f"Error collecting Stack Overflow data for tag {tag}: {e}")
    
    def _collect_stackoverflow_user(self, user_id: int):
        """Collect individual Stack Overflow user data"""
        user_url = f"{self.stack_exchange_base_url}/users/{user_id}"
        params = {
            'site': 'stackoverflow',
            'key': self.stack_exchange_key
        }
        
        try:
            response = requests.get(user_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['items']:
                user = data['items'][0]
                
                # Infer gender from username/profile
                gender_inferred = self._infer_gender_from_username(user['display_name'])
                
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO stackoverflow_users 
                    (user_id, username, reputation, creation_date, last_access_date, 
                     question_count, answer_count, badge_count, gender_inferred)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user['user_id'],
                    user['display_name'],
                    user.get('reputation', 0),
                    datetime.fromtimestamp(user['creation_date']).isoformat(),
                    datetime.fromtimestamp(user['last_access_date']).isoformat(),
                    user.get('question_count', 0),
                    user.get('answer_count', 0),
                    user.get('badge_counts', {}).get('total', 0),
                    gender_inferred
                ))
                
                conn.commit()
                conn.close()
                
        except Exception as e:
            logger.error(f"Error collecting user {user_id}: {e}")
    
    def _store_stackoverflow_question(self, question: Dict):
        """Store Stack Overflow question data"""
        try:
            owner = question.get('owner', {})
            user_id = owner.get('user_id')
            if not user_id:
                logger.warning(f"Skipping question without user_id: {json.dumps(question, indent=2)}")
                return
            gender_inferred = self._infer_gender_from_username(owner.get('display_name', ''))
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO stackoverflow_questions 
                (question_id, user_id, title, tags, score, view_count, 
                 answer_count, creation_date, gender_inferred)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                question['question_id'],
                user_id,
                question['title'],
                ','.join(question['tags']),
                question['score'],
                question['view_count'],
                question['answer_count'],
                datetime.fromtimestamp(question['creation_date']).isoformat(),
                gender_inferred
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing question {question.get('question_id', 'unknown')}: {e}")
    
    def collect_github_data(self, languages: Optional[List[str]] = None, max_repos: int = 500):
        """
        Collect GitHub repository and user activity traces
        """
        if not self.github_client:
            logger.error("GitHub client not initialized")
            return
            
        logger.info("Starting GitHub data collection...")
        
        if not languages:
            languages = ['Python', 'JavaScript', 'Java', 'C++', 'C#']
        
        for language in languages:
            logger.info(f"Collecting GitHub data for language: {language}")
            
            try:
                # Search for repositories in the language
                query = f"language:{language} stars:>10"
                repos = self.github_client.search_repositories(query=query, sort='stars', order='desc')
                
                count = 0
                for repo in repos:
                    if count >= max_repos // len(languages):
                        break
                    
                    # Collect repository data
                    self._store_github_repository(repo)
                    
                    # Collect owner data
                    self._collect_github_user(repo.owner)
                    
                    count += 1
                    time.sleep(0.1)  # Respect rate limits
                    
            except Exception as e:
                logger.error(f"Error collecting GitHub data for language {language}: {e}")
    
    def _collect_github_user(self, user):
        """Collect GitHub user data"""
        try:
            # Infer gender from username/profile
            gender_inferred = self._infer_gender_from_username(user.login)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO github_users 
                (user_id, username, public_repos, followers, following, 
                 created_at, updated_at, bio, location, gender_inferred)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user.id,
                user.login,
                user.public_repos,
                user.followers,
                user.following,
                user.created_at.isoformat(),
                user.updated_at.isoformat(),
                user.bio,
                user.location,
                gender_inferred
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error collecting GitHub user {user.login}: {e}")
    
    def _store_github_repository(self, repo):
        """Store GitHub repository data"""
        try:
            # Print repo data for debugging
            print(f"GitHub repo debug:{repo} id={repo.id}, owner_id={repo.owner.id}, name={repo.name}, language={repo.language}, stars={repo.stargazers_count}")
            gender_inferred = self._infer_gender_from_username(repo.owner.login)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO github_repositories 
                (repo_id, user_id, name, description, language, stars, 
                 forks, created_at, updated_at, gender_inferred)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                repo.id,
                repo.owner.id,
                repo.name,
                repo.description,
                repo.language,
                repo.stargazers_count,
                repo.forks_count,
                repo.created_at.isoformat(),
                repo.updated_at.isoformat(),
                gender_inferred
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error storing GitHub repository {repo.name}: {e}")
    
    def collect_reddit_data(self, subreddits: Optional[List[str]] = None, max_posts: int = 1000, collect_comments: bool = True):
        """
        Collect Reddit post and comment activity traces from tech communities
        """
        if not self.reddit_client:
            logger.error("Reddit client not initialized")
            return
            
        logger.info("Starting Reddit data collection...")
        
        if not subreddits:
            subreddits = ['programming', 'cscareerquestions', 'learnprogramming', 'technology']
        
        for subreddit_name in subreddits:
            logger.info(f"Collecting Reddit data from r/{subreddit_name}")
            
            try:
                subreddit = self.reddit_client.subreddit(subreddit_name)
                
                count = 0
                for post in subreddit.hot(limit=max_posts // len(subreddits)):
                    # Store post data
                    self._store_reddit_post(post)
                    
                    # Collect comments if enabled
                    if collect_comments:
                        self._collect_reddit_comments(post)
                    
                    count += 1
                    if count % 10 == 0:
                        time.sleep(1)  # Respect rate limits
                        
            except Exception as e:
                logger.error(f"Error collecting Reddit data from r/{subreddit_name}: {e}")
    
    def _store_reddit_post(self, post):
        """Store Reddit post data"""
        try:
            gender_inferred = self._infer_gender_from_username(post.author.name if post.author else "deleted")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO reddit_posts 
                (post_id, username, subreddit, title, selftext, score, 
                 num_comments, created_utc, gender_inferred)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                post.id,
                post.author.name if post.author else "deleted",
                post.subreddit.display_name,
                post.title,
                post.selftext,
                post.score,
                post.num_comments,
                post.created_utc,
                gender_inferred
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing Reddit post {post.id}: {e}")
    
    def _collect_reddit_comments(self, post, max_comments: int = 50):
        """Collect comments from a Reddit post"""
        try:
            # Replace more=True to get all comments
            post.comments.replace_more(limit=0)
            comments = post.comments.list()
            
            count = 0
            for comment in comments:
                if count >= max_comments:
                    break
                    
                # Store comment data
                self._store_reddit_comment(comment, post.id)
                count += 1
                
        except Exception as e:
            logger.error(f"Error collecting comments for post {post.id}: {e}")
    
    def _store_reddit_comment(self, comment, post_id: str):
        """Store Reddit comment data"""
        try:
            gender_inferred = self._infer_gender_from_username(comment.author.name if comment.author else "deleted")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO reddit_comments 
                (comment_id, post_id, username, subreddit, body, score, 
                 created_utc, gender_inferred)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                comment.id,
                post_id,
                comment.author.name if comment.author else "deleted",
                comment.subreddit.display_name,
                comment.body,
                comment.score,
                comment.created_utc,
                gender_inferred
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing Reddit comment {comment.id}: {e}")
    
    def _infer_gender_from_username(self, username: str) -> str:
        """
        Infer gender from username using various heuristics
        This is a simplified approach - in practice, more sophisticated methods would be used
        """
        if not username or username.lower() in ['deleted', 'anonymous', 'unknown']:
            return 'anonymous'
        username_lower = username.lower()
        female_indicators = ['sarah', 'emma', 'olivia', 'ava', 'isabella', 'sophia', 'charlotte', 'mia', 'amelia', 'harper']
        male_indicators = ['james', 'john', 'robert', 'michael', 'william', 'david', 'richard', 'joseph', 'thomas', 'christopher']
        if any(indicator in username_lower for indicator in female_indicators):
            return 'female'
        elif any(indicator in username_lower for indicator in male_indicators):
            return 'male'
        if any(pattern in username_lower for pattern in ['girl', 'woman', 'lady', 'ms', 'miss', 'mrs']):
            return 'female'
        elif any(pattern in username_lower for pattern in ['guy', 'man', 'mr', 'dude']):
            return 'male'
        return 'anonymous'
    
    def get_collected_data_summary(self) -> Dict:
        """Get summary of collected data"""
        conn = sqlite3.connect(self.db_path)
        
        summary = {}
        
        # Stack Overflow summary
        so_users = pd.read_sql_query("SELECT COUNT(*) as count FROM stackoverflow_users", conn)
        so_questions = pd.read_sql_query("SELECT COUNT(*) as count FROM stackoverflow_questions", conn)
        so_gender_dist = pd.read_sql_query(
            "SELECT gender_inferred, COUNT(*) as count FROM stackoverflow_users GROUP BY gender_inferred", 
            conn
        )
        
        # GitHub summary
        gh_users = pd.read_sql_query("SELECT COUNT(*) as count FROM github_users", conn)
        gh_repos = pd.read_sql_query("SELECT COUNT(*) as count FROM github_repositories", conn)
        gh_gender_dist = pd.read_sql_query(
            "SELECT gender_inferred, COUNT(*) as count FROM github_users GROUP BY gender_inferred", 
            conn
        )
        
        # Reddit summary
        reddit_posts = pd.read_sql_query("SELECT COUNT(*) as count FROM reddit_posts", conn)
        reddit_gender_dist = pd.read_sql_query(
            "SELECT gender_inferred, COUNT(*) as count FROM reddit_posts GROUP BY gender_inferred", 
            conn
        )
        
        conn.close()
        
        summary = {
            'stackoverflow': {
                'total_users': so_users['count'].iloc[0],
                'total_questions': so_questions['count'].iloc[0],
                'gender_distribution': so_gender_dist.to_dict('records')
            },
            'github': {
                'total_users': gh_users['count'].iloc[0],
                'total_repositories': gh_repos['count'].iloc[0],
                'gender_distribution': gh_gender_dist.to_dict('records')
            },
            'reddit': {
                'total_posts': reddit_posts['count'].iloc[0],
                'gender_distribution': reddit_gender_dist.to_dict('records')
            }
        }
        
        return summary

def main():
    """Main function to run data collection"""
    collector = SocialComputingDataCollector()
    
    # Collect data from all platforms
    print("Starting comprehensive data collection...")
    
    # Stack Overflow data collection
    print("Collecting Stack Overflow data...")
    collector.collect_stackoverflow_data(max_users=500)
    
    # GitHub data collection
    print("Collecting GitHub data...")
    collector.collect_github_data(max_repos=300)
    
    # Reddit data collection
    print("Collecting Reddit data...")
    collector.collect_reddit_data(max_posts=500)
    
    # Print summary
    summary = collector.get_collected_data_summary()
    print("\nData Collection Summary:")
    
    def convert(o):
        if isinstance(o, np.generic):
            return o.item()
        raise TypeError

    print(json.dumps(summary, indent=2, default=convert))

if __name__ == "__main__":
    main()
