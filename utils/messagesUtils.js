const { AudioPlayerStatus } = require('@discordjs/voice');
const { playEmoji, pauseEmoji, skipEmoji, volumeUpEmoji, volumeDownEmoji, stopEmoji } = require('../utils/emojisUtils');
const MusicControl = require('../modules/MusicControl');


class MessagesUtils {
    //construtor somente pra enviar as msg
    constructor(textChannel, options = {}) {
        this.textChannel = textChannel;
        this.audioPlayer = options.audioPlayer || null;
        this.musicQueue = options.musicQueue || [];
        this.currentSongIndex = options.currentSongIndex || 0;
        this.voiceConnection = options.voiceConnection || null;
    }

    async sendMessage(message) {
        return this.textChannel.send(message);
    }

    async sendNowPlaying(songInfo) {
        const embed = {
            color: 0x0099ff,
            title: 'Now Playing',
            author: {
                name: songInfo[0].title,
                icon_url: songInfo[0].thumbnails[0].url // URL da thumbnail
            },
            description: `By ${songInfo[0].channel.name}`,
            fields: [
                {
                    name: 'Duration',
                    value: songInfo[0].durationRaw
                }
            ],
            footer: {
                text: 'Your Bot Name',
                icon_url: null // URL do ícone do seu bot
            }
        };

        const reactions = ['⏮️', '⏸️', '⏭️', '🔊', '🔉', '⏹️']; // Adicione as reações desejadas aqui

        const message = await this.sendEmbedWithReactions(embed, reactions);
        this.setupReactionListener(message, reactions);
    }

    sendSkipMessage() {
        this.sendMessage('Música Skipada.');
    }

    sendStopMessage() {
        this.sendMessage('Parei de Tocar.');
    }

    async sendQueueMessage(songInfo) {
        const embed = {
            color: 0x0099ff,
            title: 'Now Playing',
            author: {
                name: songInfo[0].title,
                icon_url: songInfo[0].thumbnails[0].url // URL da thumbnail
            },
            description: `By ${songInfo[0].channel.name}`,
            fields: [
                {
                    name: 'Duration',
                    value: songInfo[0].durationRaw
                }
            ],
            footer: {
                text: 'Your Bot Name',
                icon_url: null // URL do ícone do seu bot
            }
        };

        const playPauseEmoji = this.musicControl.isPlaying ? pauseEmoji : playEmoji;

        const message = await this.sendEmbedWithReactions(embed, [
            { emoji: '⏮️', action: 'back' },
            { emoji: playPauseEmoji, action: 'playPause' }, // Botão de pausa/reprodução
            { emoji: skipEmoji, action: 'skip' },
            { emoji: volumeUpEmoji, action: 'volumeUp' },
            { emoji: volumeDownEmoji, action: 'volumeDown' },
            { emoji: stopEmoji, action: 'stop' },
        ]);

        this.setupReactionListener(message, reactions);
    }

    async sendEmbedWithReactions(embed, reactions) {
        const message = await this.sendMessage({ embeds: [embed] });

        for (const reaction of reactions) {
            await message.react(reaction);
        }

        return message;
    }

    setupReactionListener(message, reactions) {
        const reactionFilter = (reaction, user) => reactions.includes(reaction.emoji.name);
        const collector = message.createReactionCollector({ filter: reactionFilter, time: 60000 });

        collector.on('collect', (reaction, user) => {
            const action = reaction.emoji.name;

            if (action) {
                this.executeAction(action);
            }
        });

        collector.on('end', (collected, reason) => {
            // Lida com o fim do coletor de reações, se necessário
        });
    }

    executeAction(action) {
        switch (action) {
            case '⏮️':
                this.backAction();
                break;
            case '⏸️':
                this.pauseAction();
                break;
            case '⏭️':
                this.skipAction();
                break;
            case '🔊':
                this.volumeUpAction();
                break;
            case '🔉':
                this.volumeDownAction();
                break;
            case '⏹️':
                this.stopAction();
                break;
            default:
                break;
        }
    }

    backAction() {
        // Lógica para voltar a música
        // Verifique se há uma fila de reprodução e se a música atual não é a primeira da fila
    
        if (this.musicQueue.length > 0 && this.currentSongIndex > 0) {
            // Decrementar o índice da música atual
            this.currentSongIndex--;
    
            // Obter a música anterior da fila
            const previousSong = this.musicQueue[this.currentSongIndex];
    
            // Toque a música anterior
            this.playMusic(previousSong);
        } else {
            // Caso contrário, não há uma música anterior para tocar
            this.sendMessage('Não há uma música anterior na fila.');
        }
    }
    

    pauseAction() {
        // Verifique se o bot está em um canal de voz
        if (!this.voiceConnection) {
            this.sendMessage('Não estou em um canal de voz.');
            return;
        }
    
        // Verifique se já está pausado
        if (this.audioPlayer.state.status === AudioPlayerStatus.Paused) {
            this.sendMessage('A música já está pausada.');
            return;
        }
    
        // Pausar a música
        this.audioPlayer.pause();
        this.sendMessage('Música pausada.');
    }
    

    skipAction() {
        // Implemente a lógica para skipar a música
    }

    volumeUpAction() {
        // Implemente a lógica para aumentar o volume
    }

    volumeDownAction() {
        // Implemente a lógica para diminuir o volume
    }

    stopAction() {
        // Implemente a lógica para parar de tocar e sair do canal de voz
    }
}

module.exports = MessagesUtils;
