class SkipCommand {
    constructor(bot) {
      this.bot = bot;
      this.name = 'skip';
      this.description = 'Skip the current song.';
    }
  
    async execute(message, args) {
      const { musicPlayer } = this.bot;
      const queue = musicPlayer.player.getQueue(message.guild);
  
      if (queue && queue.playing) {
        queue.skip();
        message.channel.send('Skipped to the next track.');
      } else {
        message.channel.send('There are no tracks to skip.');
      }
    }
  }
  
  module.exports = SkipCommand;
  