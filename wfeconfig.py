import config


class WFEConfig(config.Config):

    class general(config.Section):

        db_file = config.STR()

    class load_db(config.Section):

        useragent = config.STR()
        tmp_dir = config.STR()

    class server(config.Section):

        port = config.INT()
