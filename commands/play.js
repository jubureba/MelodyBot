const { createAudioPlayer, createAudioResource, getVoiceConnection, AudioPlayerStatus } = require('@discordjs/voice');
const logger = require('../utils/loggerUtils');
const createCustomAdapter = require('./createCustomAdapter');
const MessagesUtils = require('../utils/messagesUtils');
const YouTubeAPI = require('../modules/YouTubeAPI');

class PlayCommand {
    constructor(bot) {
        this.bot = bot;
        this.name = 'play';
        this.description = 'Play a song from YouTube';
        this.youtubeAPI = new YouTubeAPI();
        this.musicQueue = new Map();
        this.isPlaying = new Map();
        this.messages = new Map();
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

        try {

            let args = message.content.split('play')[1];
            const videoInfo = await this.youtubeAPI.search(args, { limit: 1 });

            const streamInfo = await this.youtubeAPI.stream(videoInfo.url);
            const resource = createAudioResource(streamInfo.stream, { inputType: streamInfo.type });

            const messages = this.getOrCreateMessagesInstance(guildId, message.channel);

            let audioPlayer = this.bot.audioPlayers.get(guildId);
            if (!audioPlayer) {
                audioPlayer = this.createAudioPlayerAndConnect(guildId, resource, voiceChannelId, message);
                // Envie a mensagem inicial apenas no primeiro uso do comando
                await messages.sendInitialMessage(videoInfo);
            } else {
                audioPlayer.queue.push(resource);
                this.addToQueue(guildId, videoInfo, resource);
                await messages.updateMessage(videoInfo);
            }

            if (audioPlayer.state.status === AudioPlayerStatus.Idle) {
                // Se o audioPlayer estiver ocioso, inicie a reprodução
                audioPlayer.play(resource);
            }
        } catch (error) {
            logger.error('Error:', error);
            message.channel.send('An error occurred while fetching and playing the audio.');
        }
    }

    getOrCreateMessagesInstance(guildId, textChannel) {
        if (!this.messages.has(guildId)) {
            this.messages.set(guildId, new MessagesUtils(textChannel));
            console.log('Created MessagesUtils instance.');
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
            this.handleIdleState(guildId, newAudioPlayer);
        });
        newAudioPlayer.on('error', (error) => {
            logger.error('Error playing the song:', error);
        });

        return newAudioPlayer;
    }

    addToQueue(guildId, videoInfo, resource) {
        if (!this.musicQueue.has(guildId)) {
            this.musicQueue.set(guildId, []);
        }
        this.musicQueue.get(guildId).push({ videoInfo, resource });
    }

    handleIdleState(guildId, audioPlayer) {
        const messages = this.messages.get(guildId);
        messages.removeCurrentSongFromQueue();

        if (audioPlayer.queue.length > 0) {
            const nextResource = audioPlayer.queue.shift();
            const nextSongInfo = this.musicQueue.get(guildId)[0];

            if (nextSongInfo) {
                audioPlayer.play(nextResource);
                messages.setNowPlayingInfo(nextSongInfo.videoInfo);
                messages.updateMessage(nextSongInfo.videoInfo);
            } else {
                // A fila de reprodução está vazia, você pode lidar com isso aqui
            }
        } else {
            // A fila de reprodução está vazia, você pode lidar com isso aqui
        }
    }
}

module.exports = PlayCommand;
