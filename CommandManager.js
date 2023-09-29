class CommandManager {
    constructor() {
        this.commands = [];
    }

    registerCommand(command) {
        this.commands.push(command);
    }

    getCommand(commandName) {
        return this.commands.find((command) => command.name === commandName);
    }

    getCommandNames() {
        return this.commands.map((command) => command.name);
    }

    executeCommand(message, commandName, args) {
        const command = this.getCommand(commandName);

        if (command) {
            command.execute(message, args);
        }
    }
}

module.exports = CommandManager;
