class QueueManager {
  constructor() {
    this.queue = [];
    this.queues = new Map();
    this.nowPlaying = null;
    this.isPlaying = false;
  }

  addToQueue(guildId, videoInfo, resource, addedBy) {
    if (!this.queues.has(guildId)) {
      this.queues.set(guildId, []);
    }
    this.queues.get(guildId).push({ videoInfo, resource, addedBy });
  }

  removeFromQueue(guildId, index) {
    if (this.queues.has(guildId)) {
      const queue = this.queues.get(guildId);
      if (index >= 0 && index < queue.length) {
        queue.splice(index, 1);
      }
    }
  }

  getQueue(guildId) {
    return this.queues.get(guildId) || [];
  }

  clearQueue(guildId) {
    if (this.queues.has(guildId)) {
      this.queues.set(guildId, []);
    }
  }

  getNextSong(guildId) {
    const queue = this.getQueue(guildId);
    return queue.length > 0 ? queue[0] : null;
  }

  setNowPlaying(guildId, videoInfo) {
    this.nowPlaying = { guildId, videoInfo };
  }

  getNowPlaying(guildId) {
    return this.nowPlaying;
  }

  setIsPlaying(guildId, isPlaying) {
    this.isPlaying = isPlaying;
  }

  getIsPlaying(guildId) {
    return this.isPlaying;
  }
}

module.exports = QueueManager;
