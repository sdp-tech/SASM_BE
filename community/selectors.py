from datetime import datetime
from dataclasses import dataclass
from collections import Counter

from django.conf import settings
from django.db import transaction
from django.http import Http404
from django.db.models import Q, F, Value, CharField, Func, Aggregate, Count
from django.db.models.functions import Concat, Substr
from django.db.models import Case, When


from users.models import User
from community.models import Board, Post, PostHashtag, PostLike, PostPhoto, PostComment, PostCommentPhoto

# class PostSelector:
#     def __init__(self):
#         pass


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
        board = Post.objects.get(id=post_id).board

        # extra_fields = {}

        # if board.supports_hashtags:
        #     extra_fields['hashtags__name'] = GroupConcat(
        #         'hashtags__name')
        #     extra_fields['hashtagList'] = F('hashtags__name')

        # if board.supports_post_photos:
        #     extra_fields['photos__image'] = GroupConcat(
        #         'photos__image')
        #     extra_fields['photoList'] = F('photos__image')

        post = PostSelector.detail(post_id=post_id)

        likes = PostLikeSelector.likes(
            post_id=post.id,
            user=self.user
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
            likes=likes,
        )

        if board.supports_hashtags:
            dto.hashtagList = PostHashtagSelector.hashtags_of_post(post=post)

        if board.supports_post_photos:
            dto.photoList = PostPhotoSelector.photos_of_post(post=post)

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
    def detail(post_id: int, extra_fields: dict = {}):
        return Post.objects.annotate(
            nickname=F('writer__nickname'),
            email=F('writer__email'),
            likeCount=F('like_cnt'),
            viewCount=F('view_cnt'),
            **extra_fields
        ).get(id=post_id)


@dataclass
class PostHashtagDto:
    name: str
    postCount: int


class PostHashtagSelector:
    def __init__(self):
        pass

    @staticmethod
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

    @staticmethod
    def hashtags_of_post(post: Post):
        return PostHashtag.objects.filter(post=post).values_list('name', flat=True)

    def exists(self, post: Post, name: str):
        return post.hashtags.filter(name__exact=name).exists()


class PostLikeSelector:
    def __init__(self):
        pass

    @staticmethod
    def likes(post_id: int, user: User):
        return PostLike.objects.filter(
            post__id=post_id,
            user=user
        ).exists()


class PostPhotoSelector:
    def __init__(self):
        pass

    @staticmethod
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

        return PostCommentSelector.list(
            post=post
        )


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
        #댓글이면 id값을, 대댓글이면 parent id값을 대표값(group)으로 설정
        #group 내에서는 id값 기준으로 정렬
        #photoList=list(PostCommentPhotoSelector.photos_of_post_comment(post_comment="id")
            group=Case(
                    When( 
                        isParent=False,
                        then= 'parent_id'
                    ),
                    default='id'
            ),
            nickname=F('writer__nickname'),
            email=F('writer__email'),
            mentionEmail=F('mention__email'),
            mentionNickname=F('mention__nickname')
        ).order_by("group", "id")

        return post_comments


class PostCommentPhotoSelector:
    def __init__(self):
        pass

    def isPostCommentPhotoAvailable(self, post_id: int):
        post = Post.objects.get(id=post_id)
        board_id = post.board_id

        return Board.objects.get(id=board_id).supports_post_comment_photos

    @staticmethod
    def photos_of_post_comment(post_comment: PostComment):
        return PostCommentPhoto.objects.filter(post_comment=post_comment) \
            .annotate(
            imageUrls=Concat(Value(settings.MEDIA_URL),
                              F('image'),
                              output_field=CharField())
        ).values_list('imageUrls', flat=True)