const { AudioPlayerStatus } = require('@discordjs/voice');

class SkipCommand {
    constructor(bot) {
        this.bot = bot;
        this.name = 'skip';
        this.aliases = ['s']; // Adiciona um alias 's' para o comando
        this.description = 'Skip the currently playing song.';
    }

    async execute(message) {
        const guildId = message.guildId;
        const audioPlayer = this.bot.audioPlayers.get(guildId);
        if (audioPlayer && audioPlayer.state.status === AudioPlayerStatus.Playing) {
            audioPlayer.stop();
            message.channel.send('Música pulada.');
        } else {
            message.channel.send('Não há música na fila.');
        }
    }
}

module.exports = SkipCommand;
