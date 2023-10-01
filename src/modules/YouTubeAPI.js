const playdl = require('play-dl');

class YouTubeAPI {
    constructor() {}

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
}

module.exports = YouTubeAPI;
