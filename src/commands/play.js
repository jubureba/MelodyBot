const { createAudioPlayer, createAudioResource, getVoiceConnection, AudioPlayerStatus } = require('@discordjs/voice');
const createCustomAdapter = require('./createCustomAdapter');
const MessagesUtils = require('../utils/messagesUtils');
const QueueManager = require('../modules/QueueManager');
const YouTubeAPI = require('../modules/YouTubeAPI');
const logger = require('../utils/loggerUtils');
const ExceptionHandling = require('../utils/exceptionHandlingUtils');
const { setTimeout } = require('timers');
const inactiveTimeouts = new Map();

class PlayCommand {
  constructor(bot) {
    this.bot = bot;
    this.name = 'play';
    this.aliases = ['p'];
    this.description = 'Reproduzir uma música do YouTube';
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
        message.channel.send('Por favor, forneça uma consulta de pesquisa.');
        return;
      }

      if (!message.member.voice.channelId) {
        message.channel.send('Você precisa estar conectado a um canal de voz antes.');
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
        message.channel.send('Desculpe, não consegui encontrar o que você estava procurando.');
        return;
      }

      if (inactiveTimeouts.has(guildId)) {
        clearTimeout(inactiveTimeouts.get(guildId));
        inactiveTimeouts.delete(guildId);
      }
      

      const streamInfo = await this.youtubeAPI.stream(videoInfo.url);
      const resource = createAudioResource(streamInfo.stream, { inputType: streamInfo.type });

      const messages = this.getOrCreateMessagesInstance(guildId, message);

      let audioPlayer = this.bot.audioPlayers.get(guildId);
      let isNewConnection = false;

      if (!audioPlayer) {
        audioPlayer = this.createAudioPlayerAndConnect(guildId, resource, voiceChannelId, message);
        isNewConnection = true;
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
      ExceptionHandling.handleException(error);
    }
  }

  getOrCreateMessagesInstance(guildId, message) {
    if (!this.messages.has(guildId)) {
      if (!message) {
        logger.error('O canal de texto não está definido.');
        return null;
      }
      this.messages.set(guildId, new MessagesUtils(message, this.queueManager));
      logger.info('Instância MessagesUtils criada.');
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
      ExceptionHandling.handleException(error);
    });

    return newAudioPlayer;
  }

  handleIdleState(guildId, audioPlayer, resource) {
    const messages = this.messages.get(guildId);
    const guildQueue = this.queueManager.getQueue(guildId);

    if (!guildQueue || guildQueue.length === 0 || audioPlayer.queue.length === 0) {
      // Lidar com o caso em que a fila está vazia ou indefinida
      audioPlayer.stop();
      this.queueManager.setIsPlaying(guildId, false);
      this.queueManager.clearQueue(guildId);

      // Adicione ou reinicie o temporizador de inatividade apenas se não houver música tocando
      if (!this.queueManager.getIsPlaying(guildId) && !inactiveTimeouts.has(guildId)) {
        const timeout = setTimeout(() => {
          const connection = getVoiceConnection(guildId);
          if (connection) {
            connection.destroy();
            inactiveTimeouts.delete(guildId);
            this.bot.audioPlayers = new Map();
            logger.info('Bot saiu do canal')
          }
        }, 120000); // Tempo em milissegundos (2 minutos)
        inactiveTimeouts.set(guildId, timeout);
      }

      messages.idleMessage();
      return;
    }

    const firstKey = guildQueue.keys().next().value;
    this.queueManager.removeFromQueue(guildId, firstKey);

    try {
      const nextSongInfo = guildQueue.values().next().value;
      const nextResource = audioPlayer.queue.shift();

      // Verifique se há um temporizador de inatividade e limpe-o
      if (inactiveTimeouts.has(guildId)) {
        clearTimeout(inactiveTimeouts.get(guildId));
        inactiveTimeouts.delete(guildId);
      }
      audioPlayer.play(nextResource);
      this.queueManager.setNowPlaying(guildId, nextSongInfo.videoInfo);
      messages.updateMessage(nextSongInfo.videoInfo, resource);
    } catch (error) {
      logger.error('Erro ao reproduzir áudio:', error);
    }
  }
}


module.exports = PlayCommand;
