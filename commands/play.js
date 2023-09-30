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
            let args = message.content.split('play')[1];
            let videoInfo = await playdl.search(args, {
                limit: 1
            });
            let stream = await playdl.stream(videoInfo[0].url)
            let resource = createAudioResource(stream.stream, {
                inputType: stream.type
            });
            
            const messages = new MessagesUtils(message.channel);
            if (!audioPlayer) {
                // Se não houver um audioPlayer para este servidor, crie um novo
                const newAudioPlayer = createAudioPlayer();
                this.bot.audioPlayers.set(guildId, newAudioPlayer);
                audioPlayer = newAudioPlayer; // Atribua o novo audioPlayer à variável audioPlayer

                // Inicialize a fila para o novo audioPlayer
                audioPlayer.queue = [];

                // Assine os eventos do novo audioPlayer
                audioPlayer.on(AudioPlayerStatus.Idle, () => {
                    logger.info('Áudio terminou de tocar.');

                    // Verifique se há músicas na fila e inicie a próxima, se houver
                    if (audioPlayer.queue.length > 0) {
                        const nextResource = audioPlayer.queue.shift();
                        audioPlayer.play(nextResource);
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
                messages.sendNowPlaying(videoInfo[0].title);
            } else {
                // Se já houver um audioPlayer, adicione a música à fila e inicie a reprodução se o audioPlayer estiver ocioso
                if (!audioPlayer.queue) {
                    audioPlayer.queue = []; // Inicialize a fila se ainda não estiver definida
                }
                audioPlayer.queue.push(resource);
                messages.sendQueueMessage(videoInfo[0].title);

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
