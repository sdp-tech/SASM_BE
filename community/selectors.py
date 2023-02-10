from datetime import datetime
from dataclasses import dataclass
from collections import Counter

from django.conf import settings
from django.db import transaction
from django.http import Http404
from django.db.models import Q, F, Value, CharField, Func, Aggregate, Count, BooleanField, Field, Prefetch
from django.db.models.functions import Concat, Substr
from django.db.models import Case, When
from django.db.models import OuterRef, Subquery


from users.models import User
from community.models import Board, Post, PostHashtag, PostPhoto, PostComment, PostCommentPhoto


class BoardSelector:
    def __init__(self):
        pass

    @staticmethod
    def get_from_id(id: str) -> Board:
        # TODO (Refactor): 반복 사용되는 쿼리문 Manager, QuerySet으로 이후에 정리
        # TODO: 중복된 이름을 가지는 게시판이 존재해서는 안됨. 게시판 생성 시 게시판 이름 중복 확인 필요
        try:
            # If no record exists that meets the given criteria, it raises a DoesNotExist exception.
            # If more than one record with the given criteria exists, it raises a MultipleObjectsReturned exception.
            # ref. https://www.helmut.dev/understanding-the-difference-between-get-and-first-in-django.html
            return Board.objects.get(id__exact=id)
        except Board.DoesNotExist:
            raise Http404
        except Board.MultipleObjectsReturned:
            raise Http404

    @staticmethod
    def properties(board_id: int) -> Board:
        return Board.objects.annotate(
            supportsHashtags=F('supports_hashtags'),
            supportsPostPhotos=F('supports_post_photos'),
            supportsPostComments=F('supports_post_comments'),
            supportsPostCommentPhotos=F('supports_post_comment_photos'),
            postContentStyle=F('post_content_style__styled_content'),
        ).get(id=board_id)


class GroupConcat(Aggregate):
    # Postgres ArrayAgg similar(not exactly equivalent) for sqlite & mysql
    # https://stackoverflow.com/questions/10340684/group-concat-equivalent-in-django
    function = 'GROUP_CONCAT'
    separator = ','

    def __init__(self, expression, distinct=False, ordering=None, **extra):
        super(GroupConcat, self).__init__(expression,
                                          distinct='DISTINCT ' if distinct else '',
                                          ordering=' ORDER BY %s' % ordering if ordering is not None else '',
                                          output_field=CharField(),
                                          **extra)

    def as_mysql(self, compiler, connection, separator=separator):
        return super().as_sql(compiler,
                              connection,
                              template='%(function)s(%(distinct)s%(expressions)s%(ordering)s%(separator)s)',
                              separator=' SEPARATOR \'%s\'' % separator)

    def as_sql(self, compiler, connection, **extra):
        return super().as_sql(compiler,
                              connection,
                              template='%(function)s(%(distinct)s%(expressions)s%(ordering)s)',
                              **extra)


@dataclass
class PostDto:
    board: int
    title: str
    content: str
    nickname: str
    email: str
    created: datetime
    updated: datetime

    likeCount: int
    viewCount: int
    likes: bool

    hashtagList: list[str] = None  # optional
    photoList: list[str] = None  # optional


class PostCoordinatorSelector:
    def __init__(self, user: User):
        self.user = user

    def list(self, board_id: int, query: str, query_type: str, latest: bool):
        board = BoardSelector.get_from_id(id=board_id)

        extra_fields = {}

        if board.supports_post_comments:
            extra_fields['commentCount'] = Count('comments')

        return PostSelector.list(
            board=board,
            query=query,
            query_type=query_type,
            latest=latest,
            extra_fields=extra_fields
        )

    def detail(self, post_id: int):
        def set_prefetches():
            if board.supports_hashtags:
                prefetches.append(Prefetch('hashtags', to_attr='hashtagList'))

            if board.supports_post_photos:
                prefetches.append(Prefetch('photos',
                                           queryset=PostPhoto.objects.all().annotate(
                                               imageUrl=Concat(Value(settings.MEDIA_URL),
                                                               F('image'),
                                                               output_field=CharField()
                                                               )
                                           ), to_attr='photoList'))

        def post_process_prefetches():
            if board.supports_hashtags:
                dto.hashtagList = [
                    hashtag.name for hashtag in post.hashtagList]

            if board.supports_post_photos:
                dto.photoList = [photo.imageUrl for photo in post.photoList]

        board = Post.objects.get(id=post_id).board
        prefetches = []

        set_prefetches()

        post = PostSelector.detail(
            post_id=post_id,
            user=self.user,
            prefetches=prefetches
        )

        dto = PostDto(
            board=post.board.id,
            title=post.title,
            content=post.content,
            nickname=post.nickname,
            email=post.email,
            created=post.created,
            updated=post.updated,
            likeCount=post.likeCount,
            viewCount=post.viewCount,
            likes=post.likes,
        )

        post_process_prefetches()

        return dto


class PostSelector:
    def __init__(self):
        pass

    def isWriter(self, post_id: int, user: User):
        return Post.objects.get(id=post_id).writer == user

    @ staticmethod
    def list(board: Board, query: str = '', query_type: str = 'default', latest: bool = True, extra_fields: dict = {}):

        q = Q()
        q.add(Q(board=board), q.AND)

        if query_type == 'hashtag':  # 해시태그 검색
            q.add(Q(hashtags__name__exact=query), q.AND)
        else:  # 게시글 제목 또는 내용 검색 - 기본값
            q.add(Q(title__icontains=query) | Q(
                content__icontains=query), q.AND)

        # 최신순 정렬
        if latest:
            order = '-created'
        else:
            order = 'created'

        posts = Post.objects.filter(q).annotate(
            preview=Substr('content', 1, 50),
            nickname=F('writer__nickname'),
            email=F('writer__email'),
            likeCount=F('like_cnt'),
            **extra_fields
        ).order_by(order)  # .distinct

        return posts

    @ staticmethod
    def detail(post_id: int, user: User, prefetches: list = []):
        post = Post.objects.annotate(
            nickname=F('writer__nickname'),
            email=F('writer__email'),
            likeCount=F('like_cnt'),
            viewCount=F('view_cnt'),
            # post.likers에 유저가 포함되어 있는 경우, 좋아요 상태를 True로 반환, 아니라면 False로 반환
            # 다른 구현 대안으로, Exists 함수와 함께 sub query를 쓸 수도 있을 것으로 보임
            # ref. https://stackoverflow.com/questions/40599681/annotate-queryset-with-whether-matching-related-object-exists
            likes=Case(
                When(
                    likers=user,
                    then=1
                ),
                default=0,
                output_field=BooleanField(),
            ),
        ).prefetch_related(*prefetches).get(id=post_id)

        return post

    @ staticmethod
    def likes_post(user: User, post: Post):
        return post.likers.filter(email=user.email).exists()

    @ staticmethod
    def has_hashtag(post: Post, name: str):
        return post.hashtags.filter(name__exact=name).exists()


@ dataclass
class PostHashtagDto:
    name: str
    postCount: int


class PostHashtagSelector:
    def __init__(self):
        pass

    @ staticmethod
    def list(board_id: int, query: str):
        dtos = []

        # Counter를 이용해 hashtag 빈도(해당 해시태그를 가지는 게시글 수) 계산
        # query와 정확히 일치하는 순(= startswith이므로 문자열 길이가 가장 짧은 순)으로 해시태그 정렬
        # TODO: 향후 해시태그 수가 많아질 경우 성능 저하 포인트가 될 수 있음
        hashtags = sorted(
            Counter(
                PostHashtag.objects.filter(post__board__id=board_id,
                                           name__startswith=query)
                .values_list('name', flat=True)).items()
        )

        for hashtag in hashtags:
            name = hashtag[0]
            post_cnt = hashtag[1]

            dtos.append(PostHashtagDto(
                name=name,
                postCount=post_cnt
            ))

        return dtos

    @ staticmethod
    def hashtags_of_post(post: Post):
        return PostHashtag.objects.filter(post=post).values_list('name', flat=True)

    @ staticmethod
    def exists(name: str):
        return PostHashtag.objects.filter(name__exact=name).exists()


class PostPhotoSelector:
    def __init__(self):
        pass

    @ staticmethod
    def photos_of_post(post: Post):
        return PostPhoto.objects.filter(post=post) \
            .annotate(
            imageUrls=Concat(Value(settings.MEDIA_URL),
                             F('image'),
                             output_field=CharField())
        ).values_list('imageUrls', flat=True)


'''
@dataclass
class PostCommentDto:
    post: int
    content: str
    isParent: bool
    parent: int
    nickname: str
    email: str
    created: datetime
    updated: datetime
    mentioned_email: str
    mentioned_nickname: str

    photoList: list[str] = None  # optional
'''


class PostCommentCoordinatorSelector:
    def __init__(self, user: User):
        self.user = user

    def list(self, post_id: int):
        post = Post.objects.get(id=post_id)
        post_comment_qs = PostCommentSelector.list(
            post=post
        )

        # concat된 문자열을 리스트로
        for post_comment in post_comment_qs:
            if post_comment['photoList']:
                photo_url = []
                post_comment['photoList'] = post_comment['photoList'].split(",")
                
                # 각각의 photo에 접근하여 url 완성
                for photo in post_comment['photoList']:
                    photo = settings.MEDIA_URL + photo 
                    photo_url.append(photo)

                post_comment['photoList'] = photo_url # photoList에 리스트 저장
        
        return post_comment_qs


class PostCommentSelector:
    def __init__(self):
        pass

    def isWriter(self, post_comment_id: int, user: User):
        return PostComment.objects.get(id=post_comment_id).writer == user

    def isPostCommentAvailable(self, post_id: int):
        post = Post.objects.get(id=post_id)
        board_id = post.board_id

        return Board.objects.get(id=board_id).supports_post_comments

    @ staticmethod
    def list(post: Post):
        q = Q(post=post)

        post_comments = PostComment.objects.filter(q).annotate(
            # 댓글이면 id값을, 대댓글이면 parent id값을 대표값(group)으로 설정
            # group 내에서는 id값 기준으로 정렬
            group=Case(
                When(
                    isParent=False,
                    then='parent_id'
                ),
                default='id'
            ),
            nickname=F('writer__nickname'),
            email=F('writer__email'),
            mentionEmail=F('mention__email'),
            mentionNickname=F('mention__nickname'),
            photoList = GroupConcat("photos__image")
        ).values('id',
                'content',
                'isParent',
                'group',
                'nickname',
                'email',
                'mentionEmail',
                'created',
                'updated',
                'photoList').order_by('group', 'id')

        return post_comments


class PostCommentPhotoSelector:
    def __init__(self):
        pass

    def isPostCommentPhotoAvailable(self, post_id: int):
        post = Post.objects.get(id=post_id)
        board_id = post.board_id

        return Board.objects.get(id=board_id).supports_post_comment_photos

    @ staticmethod
    def photos_of_post_comment(post_comment: PostComment):
        return PostCommentPhoto.objects.filter(post_comment=post_comment) \
            .annotate(
            imageUrls=Concat(Value(settings.MEDIA_URL),
                             F('image'),
                             output_field=CharField())
        ).values_list('imageUrls', flat=True)
