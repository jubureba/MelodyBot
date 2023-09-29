const ytdl = require('ytdl-core');
const axios = require('axios');
const config = require('../config');

class YouTubeAPI {
  async searchVideo(query) {
    try {
      const response = await axios.get('https://www.googleapis.com/youtube/v3/search', {
        params: {
          q: query,
          key: config.youtubeAPIKey,
          type: 'video',
          part: 'snippet',
          maxResults: 1,
        },
      });

      const video = response.data.items[0];
      if (video) {
        return {
          id: video.id.videoId,
          title: video.snippet.title,
        };
      }
      
    } catch (error) {
      console.error('Error searching for YouTube video:', error);
    }
  }

  async getTrackInfo(videoId) {
    try {
      const response = await axios.get('https://www.googleapis.com/youtube/v3/videos', {
        params: {
          id: videoId,
          key: config.youtubeAPIKey,
          part: 'snippet',
        },
      });

      const video = response.data.items[0];
      if (video) {
        return {
          id: video.id,
          title: video.snippet.title,
        };
      }
    } catch (error) {
      console.error('Error getting YouTube video info:', error);
    }
  }

  async getTrackStreamURL(videoId) {
    return ytdl(`https://www.youtube.com/watch?v=${videoId}`);
  }
}

module.exports = YouTubeAPI;
