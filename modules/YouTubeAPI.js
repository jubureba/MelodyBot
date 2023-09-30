const axios = require('axios');
const config = require('../config');
const play = require('play-dl'); // Importe play-dl

class YouTubeAPI {
  async searchVideo(query) {
    try {
      const videoData = await play.search(query, { limit: 1 });
      if (videoData[0]) {
        const video = videoData[0];
        return {
          id: video.id,
          title: video.title,
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
    try {
      return `https://www.youtube.com/watch?v=${videoId}`;
    } catch (error) {
      console.error('Error getting YouTube video stream URL:', error);
    }
  }
  
}

module.exports = YouTubeAPI;
