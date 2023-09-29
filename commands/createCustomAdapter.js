const { joinVoiceChannel, VoiceConnectionStatus, AudioPlayerStatus } = require('@discordjs/voice');

class CustomAdapter {
  constructor(player, channelId, guildId, message) {
    this.player = player;
    this.channelId = channelId;
    this.guildId = guildId;
    this.connection = null;
    this.message = message;
  }

  connect() {
    this.connection = joinVoiceChannel({
      channelId: this.channelId,
      guildId: this.guildId,
      adapterCreator: this.message.channel.guild.voiceAdapterCreator,
    });
    this.connection.subscribe(this.player);
  }

  sendPayload(payload) {
    if (this.connection) {
      this.connection.networking.sendData(payload);
    }
  }

  destroy() {
    if (this.connection) {
      this.connection.destroy();
    }
  }

}

module.exports = CustomAdapter;
