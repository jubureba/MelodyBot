const { createAudioPlayer, createAudioResource, getVoiceConnection, AudioPlayerStatus } = require('@discordjs/voice');
const YouTubeAPI = require('../modules/YouTubeAPI');
const createCustomAdapter = require('./createCustomAdapter');
const ytdl = require('ytdl-core-discord');
const logger = require('../utils/loggerUtils');
const play = require('play-dl'); // Everything


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
    
        const audioPlayer = createAudioPlayer();
        const url = `https://www.youtube.com/watch?v=${video.id}`;
        const audioStream = await ytdl(url, { filter: 'audioonly' });

        let resource;

        resource = createAudioResource(audioStream, {
	        inlineVolume: true,
        });
        resource.volume.setVolume(0.5)
    
        audioPlayer.play(resource);

        let existingConnection = getVoiceConnection(guildId, voiceChannelId);
        
        if (existingConnection) {
            existingConnection.subscribe(audioPlayer);
        } else {
            existingConnection = new createCustomAdapter(audioPlayer, voiceChannelId, guildId, message);
            existingConnection.connect();
        }
        
        logger.info(`Bot conectado ao canal de voz: ${message.member.voice.channel.name}`);
        
        audioPlayer.on(AudioPlayerStatus.Idle, () => {
            logger.info('Áudio terminou de tocar.');
        });

        audioPlayer.on('error', async (error) => {
            logger.error('Erro ao reproduzir a música:', error);
        
            if (error.message === 'aborted') {
                // Tente reconectar e retomar a reprodução
                const guildId = message.guildId;
                const voiceChannelId = message.member.voice.channelId;
        
                try {
                    const existingConnection = getVoiceConnection(guildId, voiceChannelId);
                    if (existingConnection) {
                        existingConnection.subscribe(audioPlayer);
                    } else {
                        const newConnection = new createCustomAdapter(audioPlayer, voiceChannelId, guildId, message);
                        newConnection.connect();
                    }
        
                    logger.info('Reconexão bem-sucedida.');
                } catch (reconnectError) {
                    logger.error('Erro ao tentar reconectar:', reconnectError);
                }
            }
        });
        

        logger.info('Comando "play" concluído.');
    }
}

module.exports = PlayCommand;
