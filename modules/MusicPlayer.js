const { Player } = require('discord-player');

class MusicPlayer {
  constructor(bot) {
    this.bot = bot;
    this.player = new Player(bot);
    this.player.on('trackStart', (queue, track) => {
      queue.metadata.message.channel.send(`Now playing: ${track.title}`);
    });
  }

  async play(message, query) {
    const guildId = message.guild.id;

    try {
      const queue = this.player.getQueue(message);
      const voiceChannel = message.member.voice.channel;

      if (!voiceChannel) {
        message.channel.send('Você precisa estar em um canal de voz para usar este comando.');
        return;
      }

      if (!queue) {
        await this.player.play(message, query);
        message.channel.send(`Now playing: ${this.player.nowPlaying(message).title}`);
      } else {
        // O bot já está tocando na mesma fila, então apenas adicione a música à fila
        const trackInfo = await this.getTrackInfo(query); // Implemente esta função
        if (!trackInfo) {
          message.channel.send('Could not find the requested track.');
          return;
        }

        const trackStreamURL = await this.getTrackStreamURL(trackInfo.id); // Implemente esta função
        await queue.addTrack(trackStreamURL, { title: trackInfo.title });
        message.channel.send(`Added to queue: ${trackInfo.title}`);
      }
      
    } catch (error) {
      console.error('Error while trying to play music:', error);
      message.channel.send('An error occurred while trying to play music.');
    }
  }

  // Restante do código...

  skip(message) {
    const guildId = message.guild.id;

    try {
      this.player.skip(message);
      message.channel.send('Skipped to the next track.');
    } catch (error) {
      console.error('Error while trying to skip:', error);
      message.channel.send('An error occurred while trying to skip.');
    }
  }

  stop(message) {
    const guildId = message.guild.id;

    try {
      this.player.stop(message);
      message.channel.send('Music stopped and queue cleared.');
    } catch (error) {
      console.error('Error while trying to stop music:', error);
      message.channel.send('An error occurred while trying to stop music.');
    }
  }

  setVolume(message, percent) {
    const guildId = message.guild.id;

    try {
      this.player.setVolume(message, percent);
      message.channel.send(`Volume set to ${percent}%`);
    } catch (error) {
      console.error('Error while trying to set volume:', error);
      message.channel.send('An error occurred while trying to set volume.');
    }
  }
}

module.exports = MusicPlayer;
