const { createAudioPlayer, createAudioResource, getVoiceConnection, AudioPlayerStatus } = require('@discordjs/voice');
const YouTubeAPI = require('../modules/YouTubeAPI');
const createCustomAdapter = require('./createCustomAdapter');
const playdl = require('play-dl');
const logger = require('../utils/loggerUtils');
const MessagesUtils = require('../utils/messagesUtils');

class PlayCommand {
    constructor(bot) {
        this.bot = bot;
        this.name = 'play';
        this.description = 'Play a song from YouTube or Spotify.';
        this.youtubeAPI = new YouTubeAPI();
        this.musicQueue = new Map(); // Use um mapa para armazenar a fila de reprodução por guildId
        this.isPlaying = new Map(); // Use um mapa para rastrear o estado de reprodução por guildId
        this.messages = {};
    }

    async execute(message, args) {
        const query = args.join(' ');
        if (!query) {
            message.channel.send('Please provide a search query.');
            return;
        }

        if (!message.member.voice.channelId) {
            message.channel.send('You must be in a voice channel to use this command.');
            return;
        }

        const guildId = message.guildId;
        const voiceChannelId = message.member.voice.channelId;

        let audioPlayer = this.bot.audioPlayers.get(guildId);

        try {
            let args = message.content.split('play')[1];
            let videoInfo = await playdl.search(args, {
                limit: 1
            });
            let stream = await playdl.stream(videoInfo[0].url)
            let resource = createAudioResource(stream.stream, {
                inputType: stream.type
            });

            // Verifique se já existe uma instância de MessagesUtils para este servidor
            if (!this.messages[guildId]) {
                this.messages[guildId] = new MessagesUtils(message.channel);
                console.log('criei a instância.')
            }

            const messages = this.messages[guildId];

            if (!audioPlayer) {
                // Se não houver um audioPlayer para este servidor, crie um novo
                const newAudioPlayer = createAudioPlayer();
                this.bot.audioPlayers.set(guildId, newAudioPlayer);
                audioPlayer = newAudioPlayer;

                audioPlayer.queue = [];

                // Salve as informações da música na fila de reprodução
                this.musicQueue.set(guildId, [videoInfo[0]]); // Use um array para guardar as informações

                audioPlayer.play(resource);
                let existingConnection = getVoiceConnection(guildId, voiceChannelId);

                if (existingConnection) {
                    existingConnection.subscribe(audioPlayer);
                } else {
                    existingConnection = new createCustomAdapter(audioPlayer, voiceChannelId, guildId, message);
                    existingConnection.connect();
                }

                // Inicie a fila de reprodução para o servidor atual
                this.musicQueue.set(guildId, [resource]);
                this.isPlaying.set(guildId, true);

                audioPlayer.on(AudioPlayerStatus.Idle, async () => {
                    logger.info('Áudio terminou de tocar.');
                    messages.removeCurrentSongFromQueue();

                    if (audioPlayer.queue.length > 0) {
                        const nextResource = audioPlayer.queue.shift();
                        const nextSongInfo = messages.queue[0];
                        if (nextSongInfo) {
                            audioPlayer.play(nextResource);
                            messages.setNowPlayingInfo(nextSongInfo);
                            await messages.updateMessage(nextSongInfo);
                        } else {
                            // Não há informações da próxima música, você pode lidar com isso aqui
                        }
                    } else {
                        // A fila de reprodução está vazia, você pode lidar com isso aqui
                    }

                });

                audioPlayer.on('error', (error) => {
                    logger.error('Erro ao reproduzir a música:', error);
                });

                await messages.sendInitialMessage(videoInfo[0]);
            } else {
                if (!audioPlayer.queue) {
                    audioPlayer.queue = [];
                }
                audioPlayer.queue.push(resource);

                // Adicione a música à fila de reprodução
                //const queue = this.musicQueue.get(guildId);
                /////queue.push(videoInfo[0]);
                //queue.push(resource);

                await messages.updateMessage(videoInfo[0]);

                if (audioPlayer.state.status === AudioPlayerStatus.Idle) {
                    audioPlayer.play(resource);
                }
            }
        } catch (error) {
            logger.error('Erro ao buscar e reproduzir o áudio:', error);
            message.channel.send('An error occurred while fetching and playing the audio.');
        }
    }

    getNextSongInfo(guildId, messages) {
        const nextSongInfo = messages.queue[0]; 
        return nextSongInfo;
    }
}

module.exports = PlayCommand;
