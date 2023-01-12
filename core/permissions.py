from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsSdpStaff(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            if request.user.is_sdp:
                return True
        else:
            return False


class CommentWriterOrReadOnly(BasePermission):
    # 작성자만 접근, 작성자가 아니면 Create/Read만 가능
    def has_object_permission(self, request, view, obj):
        if request.user.is_authenticated:
            if request.user.is_sdp:
                return True
            # Create/SAFE_METHODS(GET, HEAD, OPTIONS)는 모든 유저에게 허용
            elif request.method in ['POST'].extend(SAFE_METHODS):
                return True
            # comment(obj)의 작성자가 요청자와 동일하다면 Update, Delete 가능
            elif hasattr(obj, 'writer'):
                return obj.writer.id == request.user.id
            return False
        else:
            return False
