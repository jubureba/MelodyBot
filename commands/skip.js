const { AudioPlayerStatus } = require('@discordjs/voice');
const logger = require('../utils/loggerUtils');

class SkipCommand {
    constructor(bot) {
        this.bot = bot;
        this.name = 'skip';
        this.description = 'Skip the currently playing song.';
    }

    async execute(message) {
        logger.info('Comando "skip" foi acionado.');

        const guildId = message.guildId;
        const audioPlayer = this.bot.audioPlayers.get(guildId);

        if (audioPlayer && audioPlayer.state.status === AudioPlayerStatus.Playing) {
            audioPlayer.stop();
            message.channel.send('Skipped the current song.');
        } else {
            message.channel.send('There is nothing to skip.');
        }

        logger.info('Comando "skip" concluído.');
    }
}

module.exports = SkipCommand;
