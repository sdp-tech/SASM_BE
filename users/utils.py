import re


def email_isvalid(value):
    try:
        validation = re.compile(
            r'^[a-zA-Z0-9+-_.]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
        if not re.match(validation, value):
            raise Exception('올바른 메일 형식이 아닙니다.')
        return value
    except Exception as e:
        print('예외가 발생했습니다.', e)
