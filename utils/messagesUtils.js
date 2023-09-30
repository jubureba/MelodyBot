class MessagesUtils {
    constructor(textChannel) {
      this.textChannel = textChannel;
    }
  
    sendMessage(message) {
      this.textChannel.send(message);
    }
  
    sendNowPlaying(songTitle) {
      this.sendMessage(`Now playing: ${songTitle}`);
    }
  
    sendSkipMessage() {
      this.sendMessage('Song skipped.');
    }
  
    sendStopMessage() {
      this.sendMessage('Playback stopped.');
    }
  }
  
  module.exports = MessagesUtils;
  