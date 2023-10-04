const { Client, GatewayIntentBits } = require('discord.js');
const config = require('../config');
const CommandManager = require('../commands/CommandManager');
const PlayCommand = require('../commands/play');
const SkipCommand = require('../commands/skip');
const StopCommand = require('../commands/stop');
const QueueCommand = require('../commands/queue');

const logger = require('../utils/loggerUtils');
const ExceptionHandling = require('../utils/exceptionHandlingUtils');

const intents = [
  GatewayIntentBits.Guilds,
  GatewayIntentBits.GuildMessages,
  GatewayIntentBits.MessageContent,
  GatewayIntentBits.GuildVoiceStates,
  GatewayIntentBits.GuildMessageReactions,
];

class DiscordBot extends Client {
  constructor() {
    super({
      intents: intents,
    });
    this.commandManager = new CommandManager();
    this.token = config.token;
    this.commandPrefix = config.prefix;
    this.audioPlayers = new Map(); // Inicialize a mapa de audioPlayers

    const playCommand = new PlayCommand(this);
    const skipCommand = new SkipCommand(this);
    const stopCommand = new StopCommand(this);
    const queueCommand = new QueueCommand(this);
    this.commandManager.registerCommand(playCommand);
    this.commandManager.registerCommand(skipCommand);
    this.commandManager.registerCommand(stopCommand);
    this.commandManager.registerCommand(queueCommand);
  }

  async start() {
    await this.login(this.token);
    this.setupEventListeners();
    this.setupUnhandledExceptionHandling(); // Adicione esta linha para configurar o tratamento de exceções não tratadas
  }

  setupEventListeners() {
    this.on('ready', () => {
      logger.info(`Logado no Servidor ${this.user.tag}`);
    });

    this.on('messageCreate', async (message) => {
      if (message.author.bot || !message.content.startsWith(this.commandPrefix)) {
        return;
      }

      const args = message.content.slice(this.commandPrefix.length).trim().split(/ +/);
      const commandName = args.shift().toLowerCase();

      if (commandName === 'help') {
        const commandNames = this.commandManager.getCommandNames().join(', ');
        message.channel.send(`Comandos disponíveis: ${commandNames}`);
      } else {
        const command = this.commandManager.getCommand(commandName);
        if (command) {
          try {
            await command.execute(message, args);
          } catch (error) {
            ExceptionHandling.handleException(error);
          }
        } else {
          message.channel.send('Comando não encontrado.');
        }
      }
    });

    this.on('messageReactionAdd', async (reaction, user) => {
      if (user.bot) return;

      if (reaction.emoji.name === '⏭️') {
        const args = ['skip']; // Argumentos para o comando voltar
        const command = this.commandManager.getCommand('skip'); // Substitua com seu método real para obter o comando
        if (command) {
          try {
            await command.execute(reaction.message, args);
            reaction.users.remove(user);
          } catch (error) {
            ExceptionHandling.handleException(error);
          }
        }
      } else if (reaction.emoji.name === '⏹️') {
        const args = ['stop']; // Argumentos para o comando voltar
        const command = this.commandManager.getCommand('stop'); // Substitua com seu método real para obter o comando
        if (command) {
          try {
            await command.execute(reaction.message, args);
            reaction.users.remove(user);
          } catch (error) {
            ExceptionHandling.handleException(error);
          }
        }
      } else if (reaction.emoji.name === '🔉') {
        const command = this.commandManager.getCommand('volume'); // Substitua com seu método real para obter o comando
        if (command) {
          try {
            await command.decreaseVolume(reaction.message);
            reaction.users.remove(user);
          } catch (error) {
            ExceptionHandling.handleException(error);
          }
        }
      } else if (reaction.emoji.name === '🔊') {
        const command = this.commandManager.getCommand('volume'); // Substitua com seu método real para obter o comando
        if (command) {
          try {
            await command.increaseVolume(reaction.message);
            reaction.users.remove(user);
          } catch (error) {
            ExceptionHandling.handleException(error);
          }
        }
      }
    });

  }

  setupUnhandledExceptionHandling() {
    process.on('uncaughtException', (error) => {
      ExceptionHandling.handleException(error);
      //process.exit(1);
    });
  }
}

module.exports = DiscordBot;
