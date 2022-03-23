import os, jwt, datetime, time

def generate_jwt_token(payload, type):
    SECONDS = 1
    MINUTE = SECONDS * 60
    HOUR = MINUTE * 60
    DAY = HOUR * 24
    MONTH = DAY * 30
    YEAR = DAY * 365

    if type == "access":
        #exp = datetime.datetime.now() + datetime.timedelta(seconds=3)
        # 만료 토큰 생명 주기 한 달
        exp = int(time.time()) + (MONTH)

    elif type == "refresh":
        # 갱신 토큰 생명 주기 한 달 + 1주
        exp = int(time.time()) + (MONTH + (DAY * 7))

    else:
        raise Exception("토큰 타입을 정확하게 명시해 주세요.")

    payload["exp"] = exp
    payload["iat"] = datetime.datetime.now()
    jwt_encoded = jwt.encode(payload, os.environ.get("DJANGO_SECRET_KEY"), algorithm=os.environ.get("JWT_ALGORITHM"))

    return jwt_encoded