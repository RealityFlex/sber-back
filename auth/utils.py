from passlib.context import CryptContext
import os
from datetime import datetime, timedelta
from typing import Union, Any
from jose import jwt
from jwcrypto import jwk
import json

ACCESS_TOKEN_EXPIRE_MINUTES = 300  # 30 minutes
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 days
# JWT_SECRET_KEY = "qweqweqwe" #os.environ['JWT_SECRET_KEY']     # should be kept secret
# JWT_REFRESH_SECRET_KEY = "qwe" #os.environ['JWT_REFRESH_SECRET_KEY']      # should be kept secret

key = jwk.JWK.generate(kty='RSA', size=2048)
# PUBLIC_KEY = key.export_public()
# JWT_SECRET_KEY = json.loads(key.export_private())
# JWT_REFRESH_SECRET_KEY = json.loads(key.export_private())
ALGORITHM = "RS256"

PUBLIC_KEY = json.dumps({"e":"AQAB","kty":"RSA","n":"3umIRQ-1weEms044tv5Fzb076bG4wyXx8eTMZJeNzlForlo9WVIO5GYuHpCD8v6viYUwrJGl77eMtBEw3hjRi0T6jCdlJlS-MGk99L2BIAAvXf9AhSHXuiY0clenwhgQHiBBnPrGLcSfNaRtVw1O2Vcvt6c1t7c8jfO7akLj1-zpeavIu4M8YbhF-fAip6DkX09b1npTtTXidYMu739G7Jf4jy0o9Obt13YUC-f7ivPOHK7nYLN50h7k2w0qj-DY_QKdLo8xk9edZzrc7uW6viGJWkMAOx60lrNyhnne_D_6atpN6rqvOYnC4V1Zt4P4mF7ofczGni8o3ckPW32OCQ"})
JWT_SECRET_KEY = {"d":"JzZMft2PGw5ouOT7LBGZpOHzbp4RQt7jaypU3CMe0lrWv8jm_tXlAb-JwF2qoG214kqYL9slJgCTUz-s6XzTK50UN-BcNjx1Al4ZBHrrgn4V1wKmTmUQJlI_KpgJziZee3YwJJWmk_mBCjYk98nDA4-HONbEp88na08jOkOPAfX6YqQKbElCfQY2j56IKLYEUYumQPSgPu24vw3gNsMiusTG07Y-k_9ZHxRN0qVwXpLhdMGyeWyb6xLDnjm-0Nzxep4QVz9THY7e0uBA2YjfMAmL-4VCs-ZVTeobSHVSeF3CMRnA14GvQvfPc6JSzrc9Ams2caavGgGoxuTQOBgpKw","dp":"ZAiFTy6fXSAoapZ7edPHL0zaldA6CPie_S148OdOQ-sAHlJqcYHluLrPb5weDMItBZO7HATRmFCnOMpMaU-KkZuwaGIZ7m-uAEXaDlkK1Gl4ynlp2Gdt9IDAmJ3TKfiRYqQWknu-QRghamUITqvRCtLrSeXu829_YcblxT99IN8","dq":"s3sAfGCu_d5eV8N840FkiHMA8lg16cwAKRvAmwuGCJqMnbvmL1GCEQT-Gz_U2cKx1AnAni2xGRPRDVknE29hPdpDCJn2CAhMGpE6sljEg3IAAM-B2F4XGo2nzCryWAlKzkttyYGQsuGXOqNOQ8zEowo6LcT--Ea19PWTU3L8REM","e":"AQAB","kty":"RSA","n":"3umIRQ-1weEms044tv5Fzb076bG4wyXx8eTMZJeNzlForlo9WVIO5GYuHpCD8v6viYUwrJGl77eMtBEw3hjRi0T6jCdlJlS-MGk99L2BIAAvXf9AhSHXuiY0clenwhgQHiBBnPrGLcSfNaRtVw1O2Vcvt6c1t7c8jfO7akLj1-zpeavIu4M8YbhF-fAip6DkX09b1npTtTXidYMu739G7Jf4jy0o9Obt13YUC-f7ivPOHK7nYLN50h7k2w0qj-DY_QKdLo8xk9edZzrc7uW6viGJWkMAOx60lrNyhnne_D_6atpN6rqvOYnC4V1Zt4P4mF7ofczGni8o3ckPW32OCQ","p":"85hoGRLFyvmOUW6xevTLeYlwkDsMxGTKSHfCRRRWqsr4X9SOTP6TSrQuLQaz67jnfCGG-_nGgBybq5W0L0F9aMwwBJb15MqmjpXgU5WDbIba_N9ZD3NH66t3dPSmYl811zT8DtKppbbp46h53dpFrEYbANH1uIyT-5upZybq7x8","q":"6kN-WkJjpci-Y2YxNuBc4iVhBqOXXnLwpNgAPRSbxQDY88A_heuaWV8ja5-jn6LmSsWxJYA9DZzN9t1TzoltkU8zA8XZk-nvOF7b0FtmWmiwgOMe1HQZmQEZFBtsGRUrCMFa94H6CXwSemMByPZHh9-4_QDDcQwMhSuG95q45dc","qi":"5qGq28Pfm_6RAtfqtKkwqSXyUt4yKKQ1IsAb_BEdWQ6Ynt7HklKp98U0dtE31ZYsU3T4G-fUkrNvCEBKMyjiOnDmQhrmW76qX_termjDgYPvk_r-ta7tfpPUWTRaGhBPj5-MDxOcvkyDatPL5OvVosWFo8WYxn_p5kWtrXyPxpM"}
JWT_REFRESH_SECRET_KEY = {"d":"JzZMft2PGw5ouOT7LBGZpOHzbp4RQt7jaypU3CMe0lrWv8jm_tXlAb-JwF2qoG214kqYL9slJgCTUz-s6XzTK50UN-BcNjx1Al4ZBHrrgn4V1wKmTmUQJlI_KpgJziZee3YwJJWmk_mBCjYk98nDA4-HONbEp88na08jOkOPAfX6YqQKbElCfQY2j56IKLYEUYumQPSgPu24vw3gNsMiusTG07Y-k_9ZHxRN0qVwXpLhdMGyeWyb6xLDnjm-0Nzxep4QVz9THY7e0uBA2YjfMAmL-4VCs-ZVTeobSHVSeF3CMRnA14GvQvfPc6JSzrc9Ams2caavGgGoxuTQOBgpKw","dp":"ZAiFTy6fXSAoapZ7edPHL0zaldA6CPie_S148OdOQ-sAHlJqcYHluLrPb5weDMItBZO7HATRmFCnOMpMaU-KkZuwaGIZ7m-uAEXaDlkK1Gl4ynlp2Gdt9IDAmJ3TKfiRYqQWknu-QRghamUITqvRCtLrSeXu829_YcblxT99IN8","dq":"s3sAfGCu_d5eV8N840FkiHMA8lg16cwAKRvAmwuGCJqMnbvmL1GCEQT-Gz_U2cKx1AnAni2xGRPRDVknE29hPdpDCJn2CAhMGpE6sljEg3IAAM-B2F4XGo2nzCryWAlKzkttyYGQsuGXOqNOQ8zEowo6LcT--Ea19PWTU3L8REM","e":"AQAB","kty":"RSA","n":"3umIRQ-1weEms044tv5Fzb076bG4wyXx8eTMZJeNzlForlo9WVIO5GYuHpCD8v6viYUwrJGl77eMtBEw3hjRi0T6jCdlJlS-MGk99L2BIAAvXf9AhSHXuiY0clenwhgQHiBBnPrGLcSfNaRtVw1O2Vcvt6c1t7c8jfO7akLj1-zpeavIu4M8YbhF-fAip6DkX09b1npTtTXidYMu739G7Jf4jy0o9Obt13YUC-f7ivPOHK7nYLN50h7k2w0qj-DY_QKdLo8xk9edZzrc7uW6viGJWkMAOx60lrNyhnne_D_6atpN6rqvOYnC4V1Zt4P4mF7ofczGni8o3ckPW32OCQ","p":"85hoGRLFyvmOUW6xevTLeYlwkDsMxGTKSHfCRRRWqsr4X9SOTP6TSrQuLQaz67jnfCGG-_nGgBybq5W0L0F9aMwwBJb15MqmjpXgU5WDbIba_N9ZD3NH66t3dPSmYl811zT8DtKppbbp46h53dpFrEYbANH1uIyT-5upZybq7x8","q":"6kN-WkJjpci-Y2YxNuBc4iVhBqOXXnLwpNgAPRSbxQDY88A_heuaWV8ja5-jn6LmSsWxJYA9DZzN9t1TzoltkU8zA8XZk-nvOF7b0FtmWmiwgOMe1HQZmQEZFBtsGRUrCMFa94H6CXwSemMByPZHh9-4_QDDcQwMhSuG95q45dc","qi":"5qGq28Pfm_6RAtfqtKkwqSXyUt4yKKQ1IsAb_BEdWQ6Ynt7HklKp98U0dtE31ZYsU3T4G-fUkrNvCEBKMyjiOnDmQhrmW76qX_termjDgYPvk_r-ta7tfpPUWTRaGhBPj5-MDxOcvkyDatPL5OvVosWFo8WYxn_p5kWtrXyPxpM"}


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_hashed_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, hashed_pass: str) -> bool:
    return password_context.verify(password, hashed_pass)

def create_access_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: Union[str, Any], expires_delta: int = None) -> str:
    if expires_delta is not None:
        expires_delta = datetime.utcnow() + expires_delta
    else:
        expires_delta = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, JWT_REFRESH_SECRET_KEY, ALGORITHM)
    return encoded_jwt