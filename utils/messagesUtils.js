const { MessageActionRow, MessageButton, MessageEmbed } = require('discord.js');
const ytdl = require('ytdl-core');

class MessagesUtils {
    constructor(textChannel) {
        this.textChannel = textChannel;
        this.message = null;
        this.playCount = 0;
        this.queue = [];
        this.nowPlayingInfo = null;
    }

    async sendInitialMessage(songInfo) {
        this.playCount = 1;
        this.queue.push(songInfo.title);
        this.nowPlayingInfo = songInfo;
        const embed = this.createEmbed();
        this.message = await this.textChannel.send({ embeds: [embed] });
        await this.addReactions();
    }

    async updateQueue() {
        const embed = this.createEmbed();
        try {
            await this.message.edit({ embeds: [embed] });
        } catch (error) {
            console.error('Erro ao editar a mensagem:', error);
        }
    }

    async updateMessage(newSongInfo) {
        this.playCount++;
        this.queue.push(newSongInfo.title);
        this.updateQueue();
    }

    async removeSongFromQueue(songTitle) {
        if (this.queue.length > 0) {
            this.queue.shift(); // Remove a música que está tocando atualmente
            this.updateQueue();
        }
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
        const embed = {
            color: 0xFF0000,
            title: this.nowPlayingInfo
                ? `Tocando agora: ☝️ (Fila: ${this.playCount})`
                : 'Aguardando início...',
            author: this.nowPlayingInfo
                ? {
                      name: this.nowPlayingInfo.title,
                      icon_url: this.nowPlayingInfo.thumbnails[0].url,
                  }
                : {},
            description: this.nowPlayingInfo
                ? `Autor ${this.nowPlayingInfo.channel.name}`
                : '',
            fields: [
                {
                    name: 'Duração',
                    value: this.nowPlayingInfo ? this.nowPlayingInfo.durationRaw : '',
                },
                {
                    name: 'Fila',
                    value: this.queue.length > 0 ? this.queue.join('\n') : 'Fila vazia',
                },
            ],
            footer: {
                text: 'MelodyBot by Anderson.Lima',
                icon_url: 'https://i.ibb.co/Hg7tpbS/logo.png',
            },
        };

        return embed;
    }

    async removeCurrentSongFromQueue() {
        if (this.queue.length > 0) {
            // Remove a música que acabou de tocar da fila
            this.queue.shift();
    
            // Atualize a mensagem da fila para refletir as mudanças
            await this.updateQueue();
        }
    }

    async getSongInfo(resource) {
        try {
            const stream = await ytdl.getBasicInfo(resource.url);
            
            return {
                title: stream.videoDetails.title,
                channel: {
                    name: stream.videoDetails.author.name,
                },
                durationRaw: stream.videoDetails.lengthSeconds,
                // Adicione outras informações que você deseja extrair
                // da música, como URL da imagem da capa, etc.
            };
        } catch (error) {
            console.error('Erro ao obter informações da música:', error);
            return null;
        }
    }

    async getSongInfoForNextSong() {
        if (!this.nowPlayingInfo) {
            return null; // Retorna null se não houver informações da próxima música
        }
    
        console.log('play info', this.nowPlayingInfo);
        return {
            title: this.nowPlayingInfo.title,
            channel: {
                name: this.nowPlayingInfo.channel.name,
            },
            durationRaw: this.nowPlayingInfo.durationRaw,
            // Adicione outras informações que você deseja extrair
            // da música, como URL da imagem da capa, etc.
        };
    }

    clearMessage() {
        if (this.message) {
            this.message.delete();
            this.message = null;
            this.playCount = 0;
            this.queue = [];
        }
    }
}

module.exports = MessagesUtils;
