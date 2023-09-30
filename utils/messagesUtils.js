class MessagesUtils {
    constructor(textChannel) {
        this.textChannel = textChannel;
    }

    async sendMessage(message) {
        return this.textChannel.send(message);
    }

    async sendNowPlaying(songInfo) {
        const embed = {
            color: 0x0099ff,
            title: 'Now Playing',
            author: {
                name: songInfo[0].title,
                icon_url: songInfo[0].thumbnails[0].url // URL da thumbnail
            },
            description: `By ${songInfo[0].channel.name}`,
            fields: [
                {
                    name: 'Duration',
                    value: songInfo[0].durationRaw
                }
            ],
            footer: {
                text: 'Your Bot Name',
                icon_url: null // URL do ícone do seu bot
            }
        };

        const reactions = ['⏮️', '⏸️', '⏭️', '🔊', '🔉', '⏹️']; // Adicione as reações desejadas aqui

        const message = await this.sendEmbedWithReactions(embed, reactions);
        this.setupReactionListener(message, reactions);
    }

    sendSkipMessage() {
        this.sendMessage('Música Skipada.');
    }

    sendStopMessage() {
        this.sendMessage('Parei de Tocar.');
    }

    async sendQueueMessage(songInfo) {
        const embed = {
            color: 0x0099ff,
            title: 'Added to Queue',
            author: {
                name: songInfo[0].title,
                icon_url: songInfo[0].thumbnails[0].url // URL da thumbnail
            },
            description: `By ${songInfo[0].channel.name}`,
            fields: [
                {
                    name: 'Duration',
                    value: songInfo[0].durationRaw
                }
            ],
            footer: {
                text: 'Your Bot Name',
                icon_url: null // URL do ícone do seu bot
            }
        };

        const reactions = ['⏮️', '⏸️', '⏭️', '🔊', '🔉', '⏹️']; // Adicione as reações desejadas aqui

        const message = await this.sendEmbedWithReactions(embed, reactions);
        this.setupReactionListener(message, reactions);
    }

    async sendEmbedWithReactions(embed, reactions) {
        const message = await this.sendMessage({ embeds: [embed] });

        for (const reaction of reactions) {
            await message.react(reaction);
        }

        return message;
    }

    setupReactionListener(message, reactions) {
        const reactionFilter = (reaction, user) => reactions.includes(reaction.emoji.name);
        const collector = message.createReactionCollector({ filter: reactionFilter, time: 60000 });

        collector.on('collect', (reaction, user) => {
            const action = reaction.emoji.name;

            if (action) {
                this.executeAction(action);
            }
        });

        collector.on('end', (collected, reason) => {
            // Lida com o fim do coletor de reações, se necessário
        });
    }

    executeAction(action) {
        switch (action) {
            case '⏮️':
                this.backAction();
                break;
            case '⏸️':
                this.pauseAction();
                break;
            case '⏭️':
                this.skipAction();
                break;
            case '🔊':
                this.volumeUpAction();
                break;
            case '🔉':
                this.volumeDownAction();
                break;
            case '⏹️':
                this.stopAction();
                break;
            default:
                break;
        }
    }

    backAction() {
        // Implemente a lógica para voltar a música
    }

    pauseAction() {
        // Implemente a lógica para pausar a música
    }

    skipAction() {
        // Implemente a lógica para skipar a música
    }

    volumeUpAction() {
        // Implemente a lógica para aumentar o volume
    }

    volumeDownAction() {
        // Implemente a lógica para diminuir o volume
    }

    stopAction() {
        // Implemente a lógica para parar de tocar e sair do canal de voz
    }
}

module.exports = MessagesUtils;
