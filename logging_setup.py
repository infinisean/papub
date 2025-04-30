import logging

def setup_xml_logging():
    xml_logger = logging.getLogger('xml_logger')
    xml_logger.setLevel(logging.DEBUG)
    if not xml_logger.handlers:
        handler = logging.FileHandler('/tmp/xml_processing.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        xml_logger.addHandler(handler)
    return xml_logger

def setup_main_logging(debug_mode):
    main_logger = logging.getLogger('main_logger')
    main_logger.setLevel(logging.DEBUG)
    if not main_logger.handlers:
        handler = logging.FileHandler('/tmp/newstream.log')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'))
        main_logger.addHandler(handler)
        if debug_mode:
            console = logging.StreamHandler()
            console.setLevel(logging.DEBUG)
            console.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'))
            main_logger.addHandler(console)
    return main_logger

# Initialize both loggers
xml_logger = setup_xml_logging()
main_logger = setup_main_logging(debug_mode=True)  # Set debug_mode as needed