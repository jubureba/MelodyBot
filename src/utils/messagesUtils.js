const { Embed } = require('discord.js');
const ytdl = require('ytdl-core');
const logger = require('../utils/loggerUtils');
const ExceptionHandling = require('../utils/exceptionHandlingUtils');


class MessagesUtils {
  constructor(message, queueManager) {
    this.textChannel = message.channel;
    this.message = message;
    this.queueManager = queueManager;
    this.nowPlayingInfo = null;
    this.author = message.author; // Armazena o autor original da mensagem
  }

  async sendInitialMessage(songInfo, resource) {
    // Exclua mensagens anteriores no canal
    await this.textChannel.bulkDelete(100, true);

    this.queueManager.addToQueue(this.textChannel.guildId, songInfo, resource, this.author);
    this.nowPlayingInfo = songInfo;
    const embed = this.createEmbed();
    this.message = await this.textChannel.send({ embeds: [embed] });
    await this.addReactions();
  }

  async updateMessage(newSongInfo, resource) {
    if (!newSongInfo) {
      console.error('Tentativa de atualizar a fila com informações de música nulas.');
      return;
    }

    const isNewSong = this.queueManager.getQueue(this.textChannel.guildId).size === 0 ||
      ![...this.queueManager.getQueue(this.textChannel.guildId).values()].some((info) => info.videoInfo.title === newSongInfo.title);

    if (isNewSong) {
      this.queueManager.addToQueue(this.textChannel.guildId, newSongInfo, resource, this.author.username);
    }

    const embed = this.createEmbed();

    try {
      await this.message.edit({ embeds: [embed] });
    } catch (error) {
      ExceptionHandling.handleException(error);
    }
    this.nowPlayingInfo = newSongInfo;

    // Apague todas as mensagens subsequentes no canal, exceto as do bot
    const messagesToDelete = await this.textChannel.messages.fetch({ after: this.message.id });
    messagesToDelete.forEach(async (message) => {
      if (message.author.id !== this.textChannel.client.user.id) {
        await message.delete();
      }
    });
  }
  async removeSongFromQueue() {
    await this.queueManager.removeFromQueue(this.textChannel.guildId, 0);
  }

  async addReactions() {
    if (this.message) {
      //await this.message.react('⏮️');
      //await this.message.react('⏸️');
      await this.message.react('⏭️');
      //await this.message.react('🔉');
      //await this.message.react('🔊');
      await this.message.react('⏹️');
    }
  }

  setNowPlayingInfo(songInfo) {
    this.nowPlayingInfo = songInfo;
  }

  clearNowPlayingInfo() {
    this.nowPlayingInfo = null;
  }

  createEmbed() {
    const queueInfo = this.queueManager.getQueue(this.textChannel.guildId);

    const embed = {
      color: 0xFF0000,
      title: queueInfo.length > 0 ? '**Tocando Agora**' : 'Aguardando Início...',
      author: {
        name: queueInfo.length > 0 ? queueInfo.values().next().value.videoInfo.title || 'Título Desconhecido' : 'MelodyBot',
        icon_url: queueInfo.length > 0 && queueInfo.values().next().value.videoInfo.thumbnails && queueInfo.values().next().value.videoInfo.thumbnails.length > 0
          ? queueInfo.values().next().value.videoInfo.thumbnails[0].url
          : 'https://i.ibb.co/Hg7tpbS/logo.png',
      },
      description: queueInfo.length > 0
        ? `**Autor:** ${queueInfo.values().next().value.videoInfo.channel ? queueInfo.values().next().value.videoInfo.channel.name || 'Desconhecido' : 'Desconhecido'}`
        : '',
      fields: [
        {
          name: 'Duração',
          value: queueInfo.length > 0
            ? this.formatDuration(queueInfo.values().next().value.videoInfo.durationRaw) || 'Desconhecida'
            : 'Desconhecida',
        },
        {
          name: 'Fila',
          value: queueInfo.length > 1
            ? [...queueInfo.values()].slice(1).map((info, index) => {
              const title = info.videoInfo ? info.videoInfo.title || 'Título Desconhecido' : 'Título Desconhecido';
              const author = info.videoInfo && info.videoInfo.channel ? info.videoInfo.channel.name || 'Desconhecido' : 'Desconhecido';
              const duration = info.videoInfo ? this.formatDuration(info.videoInfo.durationRaw) || 'Desconhecida' : 'Desconhecida';
              return `**${index + 1}.** [${title}](${info.videoInfo.url}) - **${info.addedBy}**`; //
            }).join('\n')
            : 'Fila Vazia',
        },
      ],
      footer: {
        text: 'MelodyBot by Anderson.Lima',
        icon_url: 'https://i.ibb.co/Hg7tpbS/logo.png',
      },
    };

    return new Embed(embed);
  }

  formatDuration(duration) {
    if (typeof duration !== 'string') {
      return 'Desconhecida';
    }

    const parts = duration.split(':');

    if (parts.length !== 2) {
      return 'Desconhecida';
    }

    const minutes = parseInt(parts[0], 10);
    const seconds = parseInt(parts[1], 10);

    if (isNaN(minutes) || isNaN(seconds) || minutes < 0 || seconds < 0) {
      return 'Desconhecida';
    }

    const totalSeconds = minutes * 60 + seconds;

    const hours = Math.floor(totalSeconds / 3600);
    const remainingMinutes = Math.floor((totalSeconds % 3600) / 60);
    const remainingSeconds = totalSeconds % 60;

    let formattedDuration = '';

    if (hours > 0) {
      formattedDuration += hours + 'h ';
    }

    if (remainingMinutes > 0) {
      formattedDuration += remainingMinutes + 'm ';
    }

    if (remainingSeconds > 0) {
      formattedDuration += remainingSeconds + 's';
    }

    return formattedDuration.trim();
  }

  clearMessage() {
    if (this.message) {
      this.message.delete();
      this.message = null;
    }
  }
}

module.exports = MessagesUtils;
