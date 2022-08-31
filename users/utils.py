import re

def email_isvalid(value):
    try:
        validation = re.compile(r'^[a-zA-Z0-9+-_.]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
        if not re.match(validation, value):
            raise Exception('올바른 메일 형식이 아닙니다.')
        return value
    except Exception as e:
        print('예외가 발생했습니다.', e)

def username_isvalid(value):
    try:
        if len(value) > 1:
            return value
        raise Exception('닉네임은 2 자리 이상이어야 합니다.')
    except Exception as e:
        print('예외가 발생했습니다.', e)
# def execute(self, sql, params=None):
# 				# 실행되는 모든 sql을 만드는 sql문과 params를 출력
#         print(sql, params)
#         return self._execute_with_wrappers(sql, params, many=False, executor=self._execute)