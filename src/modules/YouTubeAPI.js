const playdl = require('play-dl');

class YouTubeAPI {
  constructor() { }

  async search(query, options) {
    try {
      const videoInfo = await playdl.search(query, options);
      return videoInfo[0];
    } catch (error) {
      throw new Error('Error searching for video: ' + error.message);
    }
  }

  async stream(url) {
    try {
      const streamInfo = await playdl.stream(url);
      return {
        stream: streamInfo.stream,
        type: streamInfo.type
      };
    } catch (error) {
      throw new Error('Error streaming video: ' + error.message);
    }
  }

  async getPlaylistInfo(url) {
    try {
      const playlistInfo = await playdl.playlist_info(url);
      return playlistInfo;
    } catch (error) {
      throw new Error('Error getting playlist information: ' + error.message);
    }
  }

  async getPlaylistItems(url) {
    try {
      const playlistItems = await playdl.playlist(url, { limit: 50 });
      return playlistItems;
    } catch (error) {
      throw new Error('Error getting playlist items: ' + error.message);
    }
  }
}

module.exports = YouTubeAPI;
