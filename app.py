import os
import feedparser
from pytube import YouTube
import schedule
import time
from datetime import datetime, timedelta, timezone
from flask import Flask, render_template, send_from_directory, url_for, Response
import shutil
import pytz
from geopy.geocoders import Nominatim
import psutil
import threading
from feedgen.feed import FeedGenerator

app = Flask(__name__)

# Define the path to the file containing channel IDs
CHANNEL_IDS_FILE = "channel_ids.txt"
RSS_FEEDS_FILE = "rss_feeds.txt"

# Define the download directory
DOWNLOAD_DIR = "youtube_videos"

# Global list to store video information
video_list = []

def sanitize_filename(filename):
    """Sanitize the filename to avoid any illegal characters"""
    return "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_')).rstrip()

def download_videos_for_channel(channel_id):
    rss_feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    # Parse the RSS feed
    feed = feedparser.parse(rss_feed_url)

    for entry in feed.entries:
        video_url = entry.link
        video_title = sanitize_filename(entry.title)
        video_description = entry.get('summary', 'No description available')
        channel_name = sanitize_filename(entry.author)
        channel_id = entry.yt_channelid
        published_date = datetime.strptime(entry.published, '%Y-%m-%dT%H:%M:%S%z')

        # Create the directory structure: [channel name + channel id]/year
        channel_dir = os.path.join(DOWNLOAD_DIR, f"{channel_name}_{channel_id}", str(published_date.year))
        os.makedirs(channel_dir, exist_ok=True)

        # Format the file name
        file_name = f"{published_date.strftime('%Y-%m-%d')}_{video_title}.mp4"
        file_path = os.path.join(channel_dir, file_name).replace("\\", "/")

        video_info = {
            'file_path': file_path,
            'title': video_title,
            'description': video_description[:1300],
            'published_on': published_date.isoformat(),
            'original_link': video_url,
            'channel_name': channel_name
        }

        # Check if the video file already exists
        if not os.path.exists(file_path):
            try:
                yt = YouTube(video_url)
                stream = yt.streams.filter(file_extension='mp4', progressive=True).get_highest_resolution()
                if stream:
                    stream.download(output_path=channel_dir, filename=file_name)
                else:
                    print(f"No suitable stream found for {video_title}")
            except Exception as e:
                print(f"Error downloading video: {e}")

        video_list.append(video_info)

def load_channel_ids():
    with open(CHANNEL_IDS_FILE, 'r') as file:
        return [line.strip() for line in file.readlines()]

def load_rss_feeds():
    with open(RSS_FEEDS_FILE, 'r') as file:
        return [line.strip() for line in file.readlines()]

def download_videos():
    global video_list
    channel_ids = load_channel_ids()
    for channel_id in channel_ids:
        download_videos_for_channel(channel_id)

# Schedule the script to run every hour
schedule.every().hour.do(download_videos)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

threading.Thread(target=run_scheduler).start()

def get_time_and_location_info():
    geolocator = Nominatim(user_agent="timezone-app")
    
    locations = {
        'Europe/Amsterdam': {'currency': 'Euro', 'symbol': '€'},
        'Europe/London': {'currency': 'Pound Sterling', 'symbol': '£'},
        'America/New_York': {'currency': 'US Dollar', 'symbol': '$'}
    }

    info = {}

    for tz_name, details in locations.items():
        tz = pytz.timezone(tz_name)
        current_time = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
        location = geolocator.geocode(tz_name.split('/')[1])
        info[tz_name] = {
            'current_time': current_time,
            'latitude': location.latitude,
            'longitude': location.longitude,
            'currency': details['currency'],
            'symbol': details['symbol']
        }

    return info

def clean_old_videos():
    global video_list
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
    new_video_list = []
    for video in video_list:
        try:
            file_date = datetime.fromisoformat(video['published_on'])
            if file_date >= cutoff_date:
                new_video_list.append(video)
            else:
                if os.path.exists(video['file_path']):
                    os.remove(video['file_path'])
                    info_file_path = video['file_path'].replace('.mp4', '.txt')
                    if os.path.exists(info_file_path):
                        os.remove(info_file_path)
        except ValueError:
            continue
    video_list = new_video_list

schedule.every().day.at("00:00").do(clean_old_videos)

# Variables to store network statistics
network_stats = {
    'total_data': 0,
    'past_usage': [],
    'current_data': 0
}

def update_network_stats():
    while True:
        io_counters = psutil.net_io_counters()
        bytes_sent = io_counters.bytes_sent
        bytes_recv = io_counters.bytes_recv
        total_bytes = bytes_sent + bytes_recv

        network_stats['current_data'] = total_bytes / (1024**2)  # Convert to MB

        if datetime.now().hour == 0 and datetime.now().minute == 0:  # Reset statistics at midnight
            network_stats['past_usage'].append(total_bytes / (1024**3))  # Convert to GB
            if len(network_stats['past_usage']) > 1:
                network_stats['total_data'] = sum(network_stats['past_usage'])
            network_stats['current_data'] = 0

        time.sleep(60)  # Update every minute

threading.Thread(target=update_network_stats).start()

@app.route('/')
def index():
    global video_list

    # Sort the video list by publishing date in descending order
    sorted_videos = sorted(video_list, key=lambda x: datetime.fromisoformat(x['published_on']), reverse=True)

    # Get disk usage statistics
    total, used, free = shutil.disk_usage(DOWNLOAD_DIR)
    disk_usage = {
        'total': total // (2**30),  # Convert bytes to GB
        'used': used // (2**30),
        'free': free // (2**30)
    }

    # Get time and location info
    time_location_info = get_time_and_location_info()

    # Calculate average usage over the last 24 hours
    average_usage = (network_stats['total_data'] / len(network_stats['past_usage'])) if network_stats['past_usage'] else 0

    return render_template('index.html', videos=sorted_videos, disk_usage=disk_usage, time_location_info=time_location_info, network_stats=network_stats, average_usage=average_usage)

@app.route('/videos/<path:filename>')
def serve_video(filename):
    return send_from_directory(DOWNLOAD_DIR, filename)

@app.route('/rss')
def rss_feed():
    global video_list
    fg = FeedGenerator()
    fg.title('YouTube Video Downloader RSS Feed')
    fg.link(href=url_for('rss_feed', _external=True), rel='self')
    fg.description('RSS feed for downloaded YouTube videos.')

    # Combine and sort all entries based on published date in ascending order
    combined_entries = sorted(video_list, key=lambda x: datetime.fromisoformat(x['published_on']))

    for video in combined_entries:
        fe = fg.add_entry()
        fe.title(video['title'])
        fe.link(href=video['original_link'], rel='alternate')
        fe.description(video['description'])
        fe.pubDate(datetime.fromisoformat(video['published_on']).replace(tzinfo=timezone.utc))
        fe.enclosure(url_for('serve_video', filename=video['file_path'], _external=True), 0, 'video/mp4')

    rss_feed_data = fg.rss_str(pretty=True)
    return Response(rss_feed_data, mimetype='application/rss+xml')

@app.route('/mixed-rss')
def mixed_rss_feed():
    feeds = load_rss_feeds()
    combined_entries = []

    for feed_url in feeds:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            published_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            combined_entries.append({
                'title': entry.title,
                'link': entry.link,
                'description': entry.get('summary', 'No description available')[:1300],  # First 1300 characters of the description
                'published_date': published_date
            })

    combined_entries.sort(key=lambda x: x['published_date'])

    fg = FeedGenerator()
    fg.title('Combined RSS Feed')
    fg.link(href=url_for('mixed_rss_feed', _external=True), rel='self')
    fg.description('A combined RSS feed of multiple sources.')

    for entry in combined_entries:
        fe = fg.add_entry()
        fe.title(entry['title'])
        fe.link(href=entry['link'], rel='alternate')
        fe.description(entry['description'])
        fe.pubDate(entry['published_date'])

    mixed_rss_feed_data = fg.rss_str(pretty=True)
    return Response(mixed_rss_feed_data, mimetype='application/rss+xml')

if __name__ == "__main__":
    # Run the download_videos function once at the start
    threading.Thread(target=download_videos).start()
    app.run(debug=True, port=8000)
