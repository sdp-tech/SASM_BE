from django.db import models
from core.models import TimeStampedModel


class Report(TimeStampedModel):
    '''
    신고 사유로 아래와 같은 선택 기본 제시
    - "지나친 광고성 컨텐츠입니다.(상업적 홍보)"
    - "욕설이 포함된 컨텐츠입니다."
    - "성희롱이 포함된 컨텐츠입니다."
    - "기타"
    '''
    target = models.CharField(
        max_length=100, blank=False)  # 대상 인스턴스 (형식: <서비스명>:<하위 서비스명>:<하위 서비스명>:...:<대상 ID> => 예: story:comment:10)
    reason = models.CharField(max_length=100, blank=False)  # 신고 사유
    reporter = models.ForeignKey(
        'users.User', related_name='reports', on_delete=models.SET_NULL, null=True, blank=False)
