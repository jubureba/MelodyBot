const { createAudioPlayer, createAudioResource, getVoiceConnection, AudioPlayerStatus } = require('@discordjs/voice');
const createCustomAdapter = require('./createCustomAdapter');
const MessagesUtils = require('../utils/messagesUtils');
const QueueManager = require('../modules/QueueManager');
const YouTubeAPI = require('../modules/YouTubeAPI');
const { logger, handleException } = require('../utils/loggerUtils');

class PlayCommand {
  constructor(bot) {
    this.bot = bot;
    this.name = 'play';
    this.aliases = ['p'];
    this.description = 'Play a song from YouTube';
    this.youtubeAPI = new YouTubeAPI();
    this.queueManager = new QueueManager();
    this.messages = new Map();
  }

  async execute(message, args) {
    try {
      let query = args.join(' ');

      if (message.author.bot) {
        return;
      }

      if (!query) {
        message.channel.send('Please provide a search query.');
        return;
      }

      if (!message.member.voice.channelId) {
        message.channel.send('Voce precisa conectar em um canal de voz antes.');
        return;
      }

      const guildId = message.guildId;
      const voiceChannelId = message.member.voice.channelId;

      if (query.includes('&list')) {
        const url = query;
        query = url.split('&')[0];
      }

      const videoInfo = await this.youtubeAPI.search(query, { limit: 1 });

      if (!videoInfo || !videoInfo.url) {
        message.channel.send('Não encontrei nada.');
        handleException(videoInfo);
        return;
      }

      const streamInfo = await this.youtubeAPI.stream(videoInfo.url);
      const resource = createAudioResource(streamInfo.stream, { inputType: streamInfo.type });

      const messages = this.getOrCreateMessagesInstance(guildId, message);

      let audioPlayer = this.bot.audioPlayers.get(guildId);
      if (!audioPlayer) {
        audioPlayer = this.createAudioPlayerAndConnect(guildId, resource, voiceChannelId, message);
        await messages.sendInitialMessage(videoInfo, resource);
      } else {
        audioPlayer.queue.push(resource);
        await messages.updateMessage(videoInfo, resource);
      }

      if (!this.queueManager.getIsPlaying(guildId)) {
        audioPlayer.play(resource);
        this.queueManager.setIsPlaying(guildId, true);
      }
    } catch (error) {
      handleException(error);
      message.channel.send('Um erro aconteceu.');
    }
  }

  getOrCreateMessagesInstance(guildId, message) {
    if (!this.messages.has(guildId)) {
      if (!message) {
        console.error('Text channel is undefined.');
        return null;
      }
      this.messages.set(guildId, new MessagesUtils(message, this.queueManager));
      console.log('Created MessagesUtils instance.');
    }
    return this.messages.get(guildId);
  }

  createAudioPlayerAndConnect(guildId, resource, voiceChannelId, message) {
    const newAudioPlayer = createAudioPlayer();
    this.bot.audioPlayers.set(guildId, newAudioPlayer);

    const existingConnection = getVoiceConnection(guildId, voiceChannelId);
    if (existingConnection) {
      existingConnection.subscribe(newAudioPlayer);
    } else {
      const adapter = new createCustomAdapter(newAudioPlayer, voiceChannelId, guildId, message);
      adapter.connect();
    }

    newAudioPlayer.queue = [];
    newAudioPlayer.on(AudioPlayerStatus.Idle, async () => {
      this.handleIdleState(guildId, newAudioPlayer, resource);
    });
    newAudioPlayer.on('error', (error) => {
      handleException(error);
    });

    return newAudioPlayer;
  }

  handleIdleState(guildId, audioPlayer, resource) {
    const messages = this.messages.get(guildId);
    const guildQueue = this.queueManager.getQueue(guildId);

    const firstKey = guildQueue.keys().next().value;
    //guildQueue.delete(firstKey);
    this.queueManager.removeFromQueue(guildId, firstKey);

    //this.queueManager.removeFromQueue(guildId, guildQueue.values().first().value)
    if (guildQueue && guildQueue.length > 0) {
      const nextSongInfo = guildQueue.values().next().value;

      if (nextSongInfo) {
        const nextResource = audioPlayer.queue.shift();
        audioPlayer.play(nextResource);
        this.queueManager.setNowPlaying(guildId, nextSongInfo.videoInfo);
        messages.updateMessage(nextSongInfo.videoInfo, resource);
      }
    } else {
      audioPlayer.stop();
      this.queueManager.setIsPlaying(guildId, false);
      this.queueManager.clearQueue(guildId);
    }
  }
}

module.exports = PlayCommand;
