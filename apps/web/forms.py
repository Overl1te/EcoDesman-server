import os
import uuid

from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.files.storage import default_storage

from apps.posts.models import Post
from apps.users.models import User
from apps.users.services import (
    create_user_account,
    normalize_email,
    normalize_phone,
    normalize_username,
)


def save_uploaded_image(upload, request, *, folder: str = "uploads") -> str:
    extension = os.path.splitext(upload.name)[1].lower() or ".jpg"
    if extension not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise forms.ValidationError("Поддерживаются только JPG, PNG и WEBP")

    relative_path = default_storage.save(
        os.path.join(folder, f"{uuid.uuid4().hex}{extension}"),
        upload,
    )
    public_url = default_storage.url(relative_path).replace("\\", "/")
    if not public_url.startswith(("http://", "https://")):
        public_url = request.build_absolute_uri(public_url)
    return public_url


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        single_clean = super().clean
        if not data:
            return []
        if isinstance(data, (list, tuple)):
            return [single_clean(item, initial) for item in data]
        return [single_clean(data, initial)]


class SignInForm(forms.Form):
    identifier = forms.CharField(label="Почта, телефон или логин")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)


class RegisterForm(forms.Form):
    display_name = forms.CharField(label="Имя", max_length=120, required=False)
    username = forms.CharField(label="Логин", min_length=3, max_length=150)
    email = forms.EmailField(label="Email")
    phone = forms.CharField(label="Телефон", max_length=32, required=False)
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput, min_length=8)
    password_confirmation = forms.CharField(
        label="Повтор пароля",
        widget=forms.PasswordInput,
        min_length=8,
    )

    def clean_username(self):
        username = normalize_username(self.cleaned_data["username"])
        if not username:
            raise forms.ValidationError("Введите логин")
        User.username_validator(username)
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Этот логин уже занят")
        return username

    def clean_email(self):
        email = normalize_email(self.cleaned_data["email"])
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Аккаунт с таким email уже существует")
        return email

    def clean_phone(self):
        phone = normalize_phone(self.cleaned_data.get("phone"))
        if phone and User.objects.filter(phone__iexact=phone).exists():
            raise forms.ValidationError("Этот номер уже привязан к другому аккаунту")
        return phone

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirmation = cleaned_data.get("password_confirmation")
        if password and password_confirmation and password != password_confirmation:
            self.add_error("password_confirmation", "Пароли не совпадают")

        if password:
            temp_user = User(
                username=cleaned_data.get("username", ""),
                email=cleaned_data.get("email", ""),
                phone=cleaned_data.get("phone"),
                display_name=cleaned_data.get("display_name", "").strip(),
            )
            try:
                validate_password(password, user=temp_user)
            except forms.ValidationError as error:
                self.add_error("password", error)
        return cleaned_data

    def save(self):
        return create_user_account(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password"],
            display_name=self.cleaned_data.get("display_name", ""),
            phone=self.cleaned_data.get("phone"),
        )


class CommentForm(forms.Form):
    body = forms.CharField(
        label="Комментарий",
        widget=forms.Textarea(attrs={"rows": 4}),
        max_length=4000,
    )


class ProfileSettingsForm(forms.ModelForm):
    avatar_file = forms.ImageField(label="Аватар", required=False)

    class Meta:
        model = User
        fields = (
            "display_name",
            "username",
            "email",
            "phone",
            "status_text",
            "bio",
            "city",
            "website_url",
            "telegram_url",
            "vk_url",
            "instagram_url",
        )
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 5}),
        }

    def clean_username(self):
        username = normalize_username(self.cleaned_data["username"])
        if not username:
            raise forms.ValidationError("Введите логин")
        User.username_validator(username)
        queryset = User.objects.exclude(pk=self.instance.pk).filter(username__iexact=username)
        if queryset.exists():
            raise forms.ValidationError("Этот логин уже занят")
        return username

    def clean_email(self):
        email = normalize_email(self.cleaned_data["email"])
        queryset = User.objects.exclude(pk=self.instance.pk).filter(email__iexact=email)
        if queryset.exists():
            raise forms.ValidationError("Аккаунт с таким email уже существует")
        return email

    def clean_phone(self):
        phone = normalize_phone(self.cleaned_data.get("phone"))
        if phone is None:
            return None
        queryset = User.objects.exclude(pk=self.instance.pk).filter(phone__iexact=phone)
        if queryset.exists():
            raise forms.ValidationError("Этот номер уже привязан к другому аккаунту")
        return phone


class PostEditorForm(forms.Form):
    title = forms.CharField(label="Заголовок", max_length=160, required=False)
    body = forms.CharField(
        label="Текст",
        widget=forms.Textarea(attrs={"rows": 8}),
        max_length=10000,
    )
    kind = forms.ChoiceField(label="Тип", choices=Post.Kind.choices)
    is_published = forms.BooleanField(label="Опубликовать сразу", required=False, initial=True)
    event_starts_at = forms.DateTimeField(
        label="Начало события",
        required=False,
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )
    event_ends_at = forms.DateTimeField(
        label="Окончание события",
        required=False,
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )
    event_location = forms.CharField(label="Место события", max_length=200, required=False)
    image_files = MultipleFileField(label="Фотографии", required=False)
    clear_images = forms.BooleanField(label="Удалить текущие фотографии", required=False)

    def clean(self):
        cleaned_data = super().clean()
        kind = cleaned_data.get("kind")
        starts_at = cleaned_data.get("event_starts_at")
        ends_at = cleaned_data.get("event_ends_at")

        if kind == Post.Kind.EVENT and not starts_at:
            self.add_error("event_starts_at", "Укажите дату и время события")

        if starts_at and ends_at and ends_at < starts_at:
            self.add_error("event_ends_at", "Окончание не может быть раньше начала")
        return cleaned_data
