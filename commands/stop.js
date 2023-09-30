const { AudioPlayerStatus } = require('@discordjs/voice');
const logger = require('../utils/loggerUtils');

class StopCommand {
    constructor(bot) {
        this.bot = bot;
        this.name = 'stop';
        this.description = 'Stop the currently playing song and clear the queue.';
    }

    async execute(message) {
        logger.info('Comando "stop" foi acionado.');

        const guildId = message.guildId;
        const audioPlayer = this.bot.audioPlayers.get(guildId);

        if (audioPlayer && audioPlayer.state.status !== AudioPlayerStatus.Idle) {
            audioPlayer.queue = [];
            audioPlayer.stop();
            message.channel.send('Stopped the playback and cleared the queue.');
        } else {
            message.channel.send('There is nothing to stop.');
        }

        logger.info('Comando "stop" concluído.');
    }
}

module.exports = StopCommand;
