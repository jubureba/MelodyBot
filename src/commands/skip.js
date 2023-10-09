const { AudioPlayerStatus } = require('@discordjs/voice');

class SkipCommand {
  constructor(bot) {
    this.bot = bot;
    this.name = 'skip';
    this.aliases = ['s'];
    this.description = 'Pular a música que está tocando no momento.';
  }

  async execute(message) {
    const guildId = message.guildId;
    const audioPlayer = this.bot.audioPlayers.get(guildId);
    if (audioPlayer && audioPlayer.state.status === AudioPlayerStatus.Playing) {
      audioPlayer.stop();
      message.channel.send('Música pulada com sucesso. 🎵');
    } else {
      message.channel.send('Desculpe, não há música na fila no momento.');
    }
  }
}

module.exports = SkipCommand;
