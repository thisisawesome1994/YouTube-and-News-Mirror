# YouTube-and-News-Mirror
A Webpage That Mirrors your Favourite YouTube Channels and RSS Feeds in an aggregated manner

<h2>YouTube Video Downloader and RSS Feed Generator</h2>

<h3>Overview</h3>

This project provides a Python Flask web application that automatically downloads new YouTube videos from a list of channels and generates RSS feeds for the downloaded videos. The application also combines multiple RSS feeds and sorts entries by their published date and time.

<h3>Features</h3>

- Automatic Video Downloading: Downloads new YouTube videos from specified channels every hour.
- Video Storage: Organizes downloaded videos into folders based on the channel name and year of publication.
- RSS Feed Generation: Generates an RSS feed for the downloaded videos and another combined RSS feed from multiple sources.
- Web Interface: Provides a web interface to view and watch downloaded videos.
- Network and Disk Usage Statistics: Displays current disk usage, network traffic statistics, and average data usage.
- Time and Location Information: Shows current time, GPS coordinates, and local currency for specified locations.
- Video Cleanup: Automatically deletes videos older than 7 days to save disk space.

  <h3>Prerequisites</h3>

- Python 3.x
- pip

<h3>Installation</h3>

1. Clone the repository:

```


```

2. Install dependencies:
```
pip install -r requirements.txt

```

3. Create necessary files:

- channel_ids.txt: Add YouTube channel IDs (one per line) to this file.
- rss_feeds.txt: Add RSS feed URLs (one per line) to this file.

4. Run the application:
```
python app.py

```

<h3>Usage</h3>

* Access the web interface at http://127.0.0.1:8000/ to view and watch downloaded videos.
* View the RSS feed for downloaded videos at http://127.0.0.1:8000/rss.
* View the combined RSS feed at http://127.0.0.1:8000/mixed-rss.

<h3>Project Structure</h3>

```
yt-video-downloader/
├── app.py              # Main application file
├── channel_ids.txt     # List of YouTube channel IDs
├── rss_feeds.txt       # List of RSS feed URLs
├── requirements.txt    # Python dependencies
├── youtube_videos/     # Directory where videos are downloaded
└── templates/
    └── index.html      # HTML template for the web interface
```

<h3>Configuration</h3>

- Video Downloading: The application checks for new videos every hour and downloads them to the youtube_videos directory.
- RSS Feeds: The RSS feeds are updated every hour.
- Video Cleanup: Videos older than 7 days are automatically deleted at midnight every day.

<h3>Contributing</h3>
Contributions are welcome! Please fork the repository and submit a pull request for any improvements or bug fixes.

Note: I made this by using chatgpt and asking the right questions, while having limited knowledge of coding. Any bugfixes are welcome. I might discontinue this project any time, rendering the file as is for archival or reference use.
