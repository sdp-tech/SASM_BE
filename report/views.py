from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers, status
from rest_framework.response import Response

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from report.models import Report


class ReportCreateApi(APIView):
    permission_classes = (IsAuthenticated, )

    class ReportCreateInputSerializer(serializers.Serializer):
        target = serializers.CharField()
        reason = serializers.CharField()

        class Meta:
            examples = {
                'target': 'story:post:1',
                'reason': '지나친 광고성 컨텐츠입니다.(상업적 홍보)',
            }

    @swagger_auto_schema(
        request_body=ReportCreateInputSerializer,
        operation_id='신고 리포트 생성',
        operation_description='''
            * target 형식:
            ** <서비스명>:<하위 서비스명>:<하위 서비스명>:...:<대상 ID>
            * target 예시:
            ** 스토리 글 - "story:post:1"
            ** 스토리 댓글 - "story:comment:1"
            * reason 예시:
            ** "지나친 광고성 컨텐츠입니다.(상업적 홍보)"
            ** "욕설이 포함된 컨텐츠입니다."
            ** "성희롱이 포함된 컨텐츠입니다."
            ** "기타" => 사용자가 직접 작성
            ''',
        responses={
            "200": openapi.Response(
                description="OK",
                examples={
                    "application/json": {
                        "status": "success",
                        "data": {"id": 1}
                    }
                }
            ),
            "400": openapi.Response(
                description="Bad Request",
            ),
        },
    )
    def post(self, request):
        serializer = self.ReportCreateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        report = Report(
            target=data.get('target'),
            reason=data.get('reason'),
            reporter=request.user
        )

        report.full_clean()
        report.save()

        return Response({
            'status': 'success',
            'data': {'id': report.id},
        }, status=status.HTTP_201_CREATED)
