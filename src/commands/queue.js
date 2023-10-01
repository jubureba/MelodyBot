const { AudioPlayerStatus } = require('@discordjs/voice');
const logger = require('../utils/loggerUtils');

class QueueCommand {
    constructor(bot) {
        this.bot = bot;
        this.name = 'queue';
        this.description = 'Display the current queue of songs.';
    }

    async execute(message) {
        logger.info('Comando "queue" foi acionado.');

        const guildId = message.guildId;
        const audioPlayer = this.bot.audioPlayers.get(guildId);

        if (audioPlayer && audioPlayer.queue.length > 0) {
            const queue = audioPlayer.queue
                .filter((resource) => resource.metadata && resource.metadata.title) // Filtra recursos sem título definido
                .map((resource, index) => `${index + 1}. ${resource.metadata.title}`)
                .join('\n');
            message.channel.send(`Current queue:\n${queue}`);
        } else {
            message.channel.send('The queue is empty.');
        }

        logger.info('Comando "queue" concluído.');
    }
}

module.exports = QueueCommand;
