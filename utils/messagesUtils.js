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
        this.queue.push(songInfo);
        this.playCount = this.queue.length;
        console.log(this.playCount);
        this.nowPlayingInfo = songInfo;
        const embed = this.createEmbed();
        this.message = await this.textChannel.send({ embeds: [embed] });
        await this.addReactions();
    }

    async updateQueue(newSongInfo) {
        if (!newSongInfo) {
            console.error('Tentativa de atualizar a fila com informações de música nulas.');
            return;
        }
    
        const isNewSong = this.queue.length === 0 || !this.queue.some(info => info.title === newSongInfo.title);
    
        if (isNewSong) {
            // Se a fila estiver vazia ou a nova música não estiver na fila, adicione uma nova linha
            this.queue.push(newSongInfo);
        }
    
        const embed = this.createEmbed();
        try {
            await this.message.edit({ embeds: [embed] });
        } catch (error) {
            console.error('Erro ao editar a mensagem:', error);
        }
    }
    

    async updateMessage(newSongInfo) {
        this.queue.push(newSongInfo);
        this.updateQueue(newSongInfo);
    }

    resetQueue() {
        this.queue = this.queue.slice(1); // Remove a música que está tocando atualmente
        this.updateQueue();
    }

    async removeSongFromQueue() {
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
                ? `Tocando agora: ☝️ (Fila: ${this.queue.length})`
                : 'Aguardando início...',
            author: this.nowPlayingInfo
                ? {
                    name: this.nowPlayingInfo.title || 'Título Desconhecido',
                    icon_url: this.nowPlayingInfo.thumbnails && this.nowPlayingInfo.thumbnails.length > 0
                        ? this.nowPlayingInfo.thumbnails[0].url
                        : 'https://i.ibb.co/Hg7tpbS/logo.png', 
                }
                : {},
            description: this.nowPlayingInfo
                ? `Autor ${this.nowPlayingInfo.channel ? this.nowPlayingInfo.channel.name || 'Desconhecido' : 'Desconhecido'}`
                : '',
            fields: [
                {
                    name: 'Duração',
                    value: this.nowPlayingInfo ? this.nowPlayingInfo.durationRaw || 'Desconhecida' : 'Desconhecida',
                },
                {
                    name: 'Fila',
                    value: this.queue.length > 0
                        ? this.queue.map(info => info.title).join('\n')
                        : 'Fila vazia',
                },
            ],
            footer: {
                text: 'MelodyBot by Anderson.Lima',
                icon_url: 'https://i.ibb.co/Hg7tpbS/logo.png',
            },
        };
    
        return embed;
    }
    
    async removeSongFromQueue() {
        if (this.queue.length > 0) {
            this.queue.shift(); // Remove a música que está tocando atualmente
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
