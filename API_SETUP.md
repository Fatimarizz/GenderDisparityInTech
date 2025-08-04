# API Setup Guide for Social Computing Data Collection

This guide explains how to set up API keys for collecting traces of online engagement from various tech platforms.

## Required API Keys

### 1. Stack Exchange API (Optional)
- **Purpose**: Collect Stack Overflow user activity and question data
- **Setup**: 
  1. Go to [Stack Exchange API](https://api.stackexchange.com/)
  2. Register your application
  3. Get your API key
- **Note**: Works without key but with rate limits

### 2. GitHub API (Required)
- **Purpose**: Collect repository and user activity data
- **Setup**:
  1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
  2. Generate a new token with `public_repo` and `read:user` permissions
  3. Copy the token

### 3. Reddit API (Required)
- **Purpose**: Collect posts and comments from tech subreddits
- **Setup**:
  1. Go to [Reddit App Preferences](https://www.reddit.com/prefs/apps)
  2. Create a new app (select "script")
  3. Note the client ID and client secret

## Environment Configuration

Create a `.env` file in the project root with the following content:

```
# Stack Exchange API (Optional)
STACK_EXCHANGE_API_KEY=your_stack_exchange_api_key_here

# GitHub API (Required)
GITHUB_TOKEN=your_github_personal_access_token_here

# Reddit API (Required)
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
```

## Rate Limits and Best Practices

### Stack Exchange API
- **Rate Limit**: 10,000 requests per day (with API key)
- **Best Practice**: Add delays between requests (0.1 seconds)

### GitHub API
- **Rate Limit**: 5,000 requests per hour (authenticated)
- **Best Practice**: Use personal access token for higher limits

### Reddit API
- **Rate Limit**: 60 requests per minute
- **Best Practice**: Add delays between requests (1 second per 10 requests)

## Ethical Considerations

- **Public Data Only**: Only collect publicly available information
- **Respect Rate Limits**: Follow API guidelines and terms of service
- **User Privacy**: Anonymize data where possible
- **Terms of Service**: Ensure compliance with platform terms

## Troubleshooting

### Common Issues

1. **GitHub API Rate Limit Exceeded**
   - Solution: Use a personal access token
   - Wait for rate limit reset

2. **Reddit API Authentication Failed**
   - Solution: Check client ID and secret
   - Ensure app is configured as "script"

3. **Stack Exchange API Errors**
   - Solution: Check API key format
   - Verify site parameter is correct

### Testing API Connections

Run the following to test your API connections:

```bash
python src/data_collector.py
```

This will attempt to collect a small sample of data from each platform to verify your configuration. 