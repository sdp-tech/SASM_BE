import re, bcrypt

def check_password(val1, val2):
    return bcrypt.checkpw(val1.encode('utf-8'), val2.encode('utf-8'))

def hash_password(value):
    return bcrypt.hashpw(value.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def email_isvalid(value):
    try:
        validation = re.compile(r'^[a-zA-Z0-9+-_.]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
        if not re.match(validation, value):
            raise Exception('올바른 메일 형식이 아닙니다.')
        return value
    except Exception as e:
        print('예외가 발생했습니다.', e)

def password_isvalid(value):
    try:
        if value:
            if len(value) >= 8:
                return value
        raise Exception()
    except Exception as e:
        print('예외가 발생했습니다.')

def username_isvalid(value):
    try:
        if len(value) > 1:
            return value
        raise Exception('닉네임은 2 자리 이상이어야 합니다.')
    except Exception as e:
        print('예외가 발생했습니다.', e)