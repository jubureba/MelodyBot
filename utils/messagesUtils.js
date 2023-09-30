class MessagesUtils {
  constructor(textChannel) {
      this.textChannel = textChannel;
  }

  sendMessage(message) {
      this.textChannel.send(message);
  }

  sendNowPlaying(songTitle) {
      const nowPlayingMessage = {
          embeds: [{
              title: 'Now Playing',
              description: `Tocando agora: **${songTitle}**`,
              color: 0x00FF00, // Cor verde (você pode ajustar a cor conforme desejar)
          }],
      };
      this.sendMessage(nowPlayingMessage);
  }

  sendSkipMessage() {
      const skipMessage = {
          embeds: [{
              title: 'Skip',
              description: 'Música Skipada.',
              color: 0xFF0000, // Cor vermelha (você pode ajustar a cor conforme desejar)
          }],
      };
      this.sendMessage(skipMessage);
  }

  sendStopMessage() {
      const stopMessage = {
          embeds: [{
              title: 'Stop',
              description: 'Parei de Tocar.',
              color: 0xFF0000, // Cor vermelha (você pode ajustar a cor conforme desejar)
          }],
      };
      this.sendMessage(stopMessage);
  }

  sendQueueMessage(songTitle) {
      const queueMessage = {
          embeds: [{
              title: 'Queue',
              description: `Música **${songTitle}** adicionada na fila.`,
              color: 0x3498db, // Cor azul (você pode ajustar a cor conforme desejar)
          }],
      };
      this.sendMessage(queueMessage);
  }
}

module.exports = MessagesUtils;
