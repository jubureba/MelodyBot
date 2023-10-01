const QueueManager = require('../modules/QueueManager');
const { Embed } = require('discord.js');
const ytdl = require('ytdl-core');

class MessagesUtils {
    constructor(textChannel, queueManager) {
        this.textChannel = textChannel;
        this.message = null;
        this.queueManager = queueManager;
        this.nowPlayingInfo = null;
    }

    async sendInitialMessage(songInfo, resource) {
        this.queueManager.addToQueue(this.textChannel.guildId, songInfo, resource);
        this.nowPlayingInfo = songInfo;
        const embed = this.createEmbed();
        this.message = await this.textChannel.send({ embeds: [embed] });
        await this.addReactions();
    }

    async updateMessage(newSongInfo, resource) {
        this.queueManager.addToQueue(this.textChannel.guildId, newSongInfo, resource);
        const embed = this.createEmbed();
        
        try {
            await this.message.edit({ embeds: [embed] });
        } catch (error) {
            console.error('Erro ao editar a mensagem:', error);
        }
        this.nowPlayingInfo = newSongInfo;
    }

    async removeSongFromQueue() {
        this.queueManager.removeFromQueue(this.textChannel.guildId, 0);
    }

    async addReactions() {
        if (this.message) {
            await this.message.react('⏮️');
            await this.message.react('⏸️');
            await this.message.react('⏭️');
            await this.message.react('🔊');
            await this.message.react('🔉');
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
      console.log(this.queueManager.getQueue(this.textChannel.guildId));
        const embed = {
            color: 0xFF0000,
            title: this.nowPlayingInfo
                ? `**Tocando Agora**`
                : 'Aguardando Início...',
            author: {
                name: this.nowPlayingInfo
                    ? this.nowPlayingInfo.title || 'Título Desconhecido'
                    : 'MelodyBot',
                icon_url: this.nowPlayingInfo && this.nowPlayingInfo.thumbnails && this.nowPlayingInfo.thumbnails.length > 0
                    ? this.nowPlayingInfo.thumbnails[0].url
                    : 'https://i.ibb.co/Hg7tpbS/logo.png',
            },
            description: this.nowPlayingInfo
                ? `**Autor:** ${this.nowPlayingInfo.channel ? this.nowPlayingInfo.channel.name || 'Desconhecido' : 'Desconhecido'}`
                : '',
            fields: [
                {
                    name: 'Duração',
                    value: this.nowPlayingInfo
                        ? this.formatDuration(this.nowPlayingInfo.durationRaw) || 'Desconhecida'
                        : 'Desconhecida',
                },
                {
                  name: 'Fila',
                  value: this.queueManager.getQueue(this.textChannel.guildId).length > 0
                      ? this.queueManager.getQueue(this.textChannel.guildId).map((info, index) => {
                          if (info.resource) {
                              return `**${index + 1}.** ${info.videoInfo.title}`;
                          } else {
                              return `**${index + 1}.** Música sem recurso disponível`;
                          }
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
