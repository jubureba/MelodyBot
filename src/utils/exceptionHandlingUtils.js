const { logger } = require('../utils/loggerUtils');

class ExceptionHandling {
  static handleException(error) {
    if (error instanceof Error) {
      logger.error(`Unhandled Exception: ${error.message}`);
    } else {
      logger.error(`Unhandled Exception: ${error}`);
    }
  }
}

module.exports = ExceptionHandling;
