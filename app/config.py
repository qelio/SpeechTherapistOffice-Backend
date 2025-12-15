class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://gen_user:FRV%^PQOzvD6lm@192.168.0.4/speechtherapistsoffice'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False