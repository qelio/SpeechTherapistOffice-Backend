class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://cabinet:}IhoLy<4!<dL23@192.168.0.4:33060/speechtherapistsoffice'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False