# YouTube API Quick Reference

## YouTube Data API v3

### Channels
```
GET /channels?part=snippet,statistics,contentDetails&mine=true
```
Returns: title, description, customUrl, subscriberCount, viewCount, videoCount, uploads playlist ID

### Videos
```
GET /videos?part=snippet,statistics,contentDetails&id=VIDEO_ID
```
Returns: title, description, tags, publishedAt, duration, viewCount, likeCount, commentCount

### Playlist Items (for listing uploads)
```
GET /playlistItems?part=snippet,contentDetails&playlistId=UPLOADS_PLAYLIST_ID&maxResults=50
```
Returns: video IDs, titles, publish dates

### Search (100 quota units!)
```
GET /search?part=snippet&channelId=CHANNEL_ID&q=query&type=video&maxResults=25
```
Returns: video IDs, titles, descriptions

### Comments
```
GET /commentThreads?part=snippet&videoId=VIDEO_ID&maxResults=100&order=relevance
```
Returns: author, text, likeCount, publishedAt

### Captions
```
GET /captions?part=snippet&videoId=VIDEO_ID
```
Returns: caption track IDs, languages, trackKind (standard/ASR)

```
GET /captions/CAPTION_ID?tfmt=srt
```
Returns: caption content in SRT format

## YouTube Analytics API v2

### Base Query Structure
```
GET /reports?ids=channel==CHANNEL_ID
    &startDate=YYYY-MM-DD
    &endDate=YYYY-MM-DD
    &metrics=METRIC_LIST
    &dimensions=DIMENSION
    &filters=FILTER
    &sort=-METRIC
    &maxResults=N
```

### Common Metrics
| Metric | Description |
|--------|-------------|
| views | Total views |
| estimatedMinutesWatched | Total watch time in minutes |
| averageViewDuration | Avg view duration in seconds |
| subscribersGained | New subscribers |
| subscribersLost | Lost subscribers |
| likes | Likes received |
| comments | Comments received |
| shares | Shares |
| estimatedRevenue | Revenue in USD (monetized only) |
| cpm | Cost per mille (revenue per 1000 views) |

### Common Dimensions
| Dimension | Values |
|-----------|--------|
| video | Video ID |
| country | 2-letter country code (US, GB, AU, etc.) |
| ageGroup | age13-17, age18-24, age25-34, age35-44, age45-54, age55-64, age65- |
| gender | male, female |
| insightTrafficSourceType | YT_SEARCH, RELATED_VIDEO, EXT_URL, SUBSCRIBER, etc. |
| day | YYYY-MM-DD |

### Common Filters
```
video==VIDEO_ID           # Single video
country==US               # Single country
```

### Example Queries

**Channel overview:**
```
metrics=views,estimatedMinutesWatched,subscribersGained,subscribersLost,estimatedRevenue
```

**Top videos by views:**
```
dimensions=video
metrics=views,estimatedMinutesWatched,estimatedRevenue
sort=-views
maxResults=10
```

**Demographics:**
```
dimensions=ageGroup,gender
metrics=viewerPercentage
```

**Traffic sources:**
```
dimensions=insightTrafficSourceType
metrics=views
sort=-views
```

**Daily breakdown:**
```
dimensions=day
metrics=views,estimatedMinutesWatched
```

## Quota Costs (Data API)

| Operation | Cost |
|-----------|------|
| channels.list | 1 |
| videos.list | 1 |
| playlistItems.list | 1 |
| commentThreads.list | 1 |
| captions.list | 50 |
| captions.download | 200 |
| **search.list** | **100** |

Daily limit: 10,000 units

## OAuth Scopes

| Scope | Access |
|-------|--------|
| youtube.readonly | Read channel, videos, playlists |
| youtube.force-ssl | Download captions |
| yt-analytics.readonly | Read analytics |
| yt-analytics-monetary.readonly | Read revenue data |

## Error Codes

| Code | Meaning |
|------|---------|
| 403 forbidden | Missing scope or not video owner |
| 404 notFound | Video/channel doesn't exist |
| 400 commentsDisabled | Comments turned off |
| 403 quotaExceeded | Daily quota hit |
