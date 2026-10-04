from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Q, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.views.generic.detail import BaseDetailView
from django.views.generic.list import BaseListView
from movies.models import FilmWork, Roles


class MoviesApiMixin:
    model = FilmWork
    http_method_names = ['get']

    @staticmethod
    def annotate_filmwork(queryset):
        empty_list = Value([])

        return queryset.annotate(
            genres_list=Coalesce(
                ArrayAgg(
                    'genres__name',
                    distinct=True,
                    ordering='genres__name',
                ),
                empty_list,
            ),
            actors=Coalesce(
                ArrayAgg(
                    'personfilmwork__person__full_name',
                    filter=Q(personfilmwork__role=Roles.ACTOR),
                    distinct=True,
                    ordering='personfilmwork__person__full_name',
                ),
                empty_list,
            ),
            directors=Coalesce(
                ArrayAgg(
                    'personfilmwork__person__full_name',
                    filter=Q(personfilmwork__role=Roles.DIRECTOR),
                    distinct=True,
                    ordering='personfilmwork__person__full_name',
                ),
                empty_list,
            ),
            writers=Coalesce(
                ArrayAgg(
                    'personfilmwork__person__full_name',
                    filter=Q(personfilmwork__role=Roles.WRITER),
                    distinct=True,
                    ordering='personfilmwork__person__full_name',
                ),
                empty_list,
            ),
        )

    @staticmethod
    def serialize_filmwork(film):
        return {
            'id': film.id,
            'title': film.title,
            'description': film.description,
            'creation_date': film.creation_date,
            'rating': film.rating,
            'type': film.type,
            'genres': film.genres_list,
            'actors': film.actors,
            'directors': film.directors,
            'writers': film.writers,
        }

    def render_to_response(self, context, **response_kwargs):
        return JsonResponse(context)

    def get_queryset(self):
        queryset = super().get_queryset().only(
                'id',
                'title',
                'description',
                'creation_date',
                'rating',
                'type',
            )
        return self.annotate_filmwork(queryset)


class MoviesListApi(MoviesApiMixin, BaseListView):
    paginate_by = 50

    def get_context_data(self, *, object_list=None, **kwargs):
        queryset = object_list if object_list is not None else self.object_list
        paginator, page, films, _ = self.paginate_queryset(
            queryset, self.paginate_by,
            )

        return {
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'prev':
                page.previous_page_number() if page.has_previous() else None,
            'next': page.next_page_number() if page.has_next() else None,
            'results': [self.serialize_filmwork(film) for film in films],
        }


class MoviesDetailApi(MoviesApiMixin, BaseDetailView):

    def get_context_data(self, **kwargs):
        return self.serialize_filmwork(self.object)
