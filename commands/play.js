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
        this.musicQueue = [];
        this.isPlaying = false;
        this.messages = {};
    }

    async execute(message, args) {
        logger.info('Comando "play" foi acionado.');
        const query = args.join(' ');
        if (!query) {
            message.channel.send('Please provide a search query.');
            return;
        }

        if (!message.member.voice.channelId) {
            message.channel.send('You must be in a voice channel to use this command.');
            return;
        }

        logger.info('Usuário está em um canal de voz.');

        const video = await this.youtubeAPI.searchVideo(query);
        if (!video) {
            message.channel.send('Could not find the requested video on YouTube.');
            return;
        }

        logger.info('Vídeo encontrado:', video);

        const guildId = message.guildId;
        const voiceChannelId = message.member.voice.channelId;

        let audioPlayer = this.bot.audioPlayers.get(guildId);

        try {
            const argsForPlaydl = message.content.split('play')[1];
            const videoInfo = await playdl.search(argsForPlaydl, {
                limit: 1
            });
            const stream = await playdl.stream(videoInfo[0].url);
            const resource = createAudioResource(stream.stream, {
                inputType: stream.type
            });

            // Verifique se já existe uma instância de MessagesUtils para este servidor
            if (!this.messages[guildId]) {
                this.messages[guildId] = new MessagesUtils(message.channel);
                console.log('Criei a instância de MessagesUtils.');
            }

            const messages = this.messages[guildId];
            if (!audioPlayer) {
                // Se não houver um audioPlayer para este servidor, crie um novo
                const newAudioPlayer = createAudioPlayer();
                this.bot.audioPlayers.set(guildId, newAudioPlayer);
                audioPlayer = newAudioPlayer;

                audioPlayer.queue = [];

                audioPlayer.on(AudioPlayerStatus.Idle, async () => {
                    logger.info('Áudio terminou de tocar.');
                    messages.removeCurrentSongFromQueue();

                    if (audioPlayer.queue.length > 0) {
                        const nextResource = audioPlayer.queue.shift();
                        const nextSongInfo = await messages.getSongInfoForNextSong(); // Use o vídeo atual
                        audioPlayer.play(nextResource);
                        messages.setNowPlayingInfo(nextSongInfo);
                    }
                });

                audioPlayer.on('error', (error) => {
                    logger.error('Erro ao reproduzir a música:', error);
                });

                audioPlayer.play(resource);
                let existingConnection = getVoiceConnection(guildId, voiceChannelId);

                if (existingConnection) {
                    existingConnection.subscribe(audioPlayer);
                } else {
                    existingConnection = new createCustomAdapter(audioPlayer, voiceChannelId, guildId, message);
                    existingConnection.connect();
                }

                await messages.sendInitialMessage(videoInfo[0]);
            } else {
                if (!audioPlayer.queue) {
                    audioPlayer.queue = [];
                }
                audioPlayer.queue.push(resource);
                await messages.updateMessage(videoInfo[0]);

                if (audioPlayer.state.status === AudioPlayerStatus.Idle) {
                    audioPlayer.play(resource);
                }
            }

            logger.info(`Bot conectado ao canal de voz: ${message.member.voice.channel.name}`);
            logger.info('Comando "play" concluído.');
        } catch (error) {
            logger.error('Erro ao buscar e reproduzir o áudio:', error);
            message.channel.send('An error occurred while fetching and playing the audio.');
        }
    }

}

module.exports = PlayCommand;
