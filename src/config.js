const dotenv = require('dotenv');
dotenv.config();

const { TOKEN_DISCORD, CLIENT_ID, GUILD_ID, YOUTUBE_API_KEY, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, PREFIX } = process.env;

module.exports = {
    token: TOKEN_DISCORD,
    prefix: PREFIX, 
    youtubeAPIKey: YOUTUBE_API_KEY
  
  };
  