class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:slava2012@localhost:3306/speechtherapistsoffice'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False