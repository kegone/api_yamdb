from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import NotFound

from reviews.models import Category, Comment, Genre, Review, Title
from users.models import User


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователей."""
    class Meta:
        model = User
        fields = (
            'username',
            'email',
            'first_name',
            'last_name',
            'bio',
            'role'
        )


class UserMeSerializer(UserSerializer):
    """Сериализатор для текущего пользователя."""
    role = serializers.CharField(read_only=True)


class SignUpSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации."""
    def validate_username(self, value):
        if value == 'me':
            raise serializers.ValidationError(
                'Использовать имя _me_ в качестве username запрещено.'
            )

    class Meta:
        model = User
        fields = ('email', 'username')


class TokenSerializer(serializers.Serializer):
    """Сериализатор для получения токена."""
    username = serializers.CharField()
    confirmation_code = serializers.CharField()

    def validate(self, data):
        try:
            user = User.objects.get(username=data.get('username'))
        except User.DoesNotExist:
            raise NotFound({'username': 'Несуществующий username.'})
        confirmation_code = data.get('confirmation_code')
        if default_token_generator.check_token(user, confirmation_code):
            return data
        raise serializers.ValidationError(
            {'confirmation_code': 'Неверный проверочный код.'}
        )


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для категорий."""
    class Meta:
        model = Category
        fields = ('name', 'slug')


class GenreSerializer(serializers.ModelSerializer):
    """Сериализатор для жанров."""
    class Meta:
        model = Genre
        fields = ('name', 'slug')


class TitleRetrieveSerializer(serializers.ModelSerializer):
    """Сериализатор для GET-запросов произведений."""
    category = CategorySerializer(read_only=True)
    genre = GenreSerializer(read_only=True, many=True)
    rating = serializers.FloatField(read_only=True)

    class Meta:
        model = Title
        fields = (
            'id',
            'name',
            'year',
            'rating',
            'description',
            'genre',
            'category'
        )


class TitleSerializer(serializers.ModelSerializer):
    """Сериализатор для произведений."""
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Category.objects.all()
    )
    genre = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Genre.objects.all(),
        many=True
    )
    rating = serializers.FloatField(read_only=True)

    class Meta:
        model = Title
        fields = (
            'id',
            'name',
            'year',
            'rating',
            'description',
            'genre',
            'category'
        )

    def validate_year(self, value):
        if value < 0 or value > timezone.now().year:
            raise serializers.ValidationError(
                'Год не может быть в будущем или отрицательным.'
            )
        return value

    def validate_genre(self, value):
        if value == []:
            raise serializers.ValidationError(
                'Список не может быть пустым.'
            )
        return value


class ReviewSerializer(serializers.ModelSerializer):
    """Сериализатор для отзывов."""
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True,
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Review
        fields = ('id', 'text', 'score', 'author', 'pub_date')


class CommentSerializer(serializers.ModelSerializer):
    """Сериализатор для комментариев."""
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True,
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Comment
        fields = ('id', 'text', 'author', 'pub_date')
        read_only_fields = ('title', 'review')
