from sqlalchemy import text  
from models import Usuario
from sqlalchemy.exc import SQLAlchemyError

class ModelUser():
    @classmethod
    def login(cls, db, username):
        try:
            query = text("SELECT id, username, password, fullname FROM usuario WHERE username = :username")
            result = db.session.execute(query, {"username": username})
            row = result.fetchone()
            
            if row is not None:
                user = Usuario(row[1], row[2], row[3])  
                user.id = row[0]  
                return user
            return None
        except SQLAlchemyError as ex:
            print("Error en la base de datos:", ex)
            return None
        

    @classmethod
    def get_by_id(self, db, id):
        try:
            query = text("SELECT id, username,password, fullname FROM usuario WHERE id = :id")
            result = db.session.execute(query, {"id": id})
            row = result.fetchone()
            
            if row is not None:
                user = Usuario(row[1], row[2], row[3])  
                user.id = row[0]  
                return user
            return None
        except SQLAlchemyError as ex:
            print("Error en la base de datos:", ex)
            return None


