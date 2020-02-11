import logging

TRACE = 3


def configure_logging(configfile):
    logging.fileConfig(configfile)
    logging.addLevelName(TRACE, "TRACE")


def add_trace_logging(log):
    log.addLevelName(TRACE, "TRACE")
