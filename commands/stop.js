class StopCommand {
    constructor(bot) {
      this.bot = bot;
      this.name = 'stop';
      this.description = 'Stop the music and clear the queue.';
    }
  
    async execute(message, args) {
      const { musicPlayer } = this.bot;
      const queue = musicPlayer.player.getQueue(message.guild);
  
      if (queue) {
        queue.destroy();
        message.channel.send('Music stopped and queue cleared.');
      } else {
        message.channel.send('There is no music playing to stop.');
      }
    }
  }
  
  module.exports = StopCommand;
  