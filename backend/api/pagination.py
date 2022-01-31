from rest_framework.pagination import PageNumberPagination, _positive_int


class FoodgramPagination(PageNumberPagination):
    page_size_query_param = 'limit'


class SubscriptionPagination(FoodgramPagination):
    recipes_limit = 'recipes_limit'

    def get_paginated_response(self, data):
        recipes_limit = _positive_int(
            self.request.query_params.get(self.recipes_limit, 1)
        )
        for i in range(len(data)):
            length = len(data[i]['recipes'])
            new_length = recipes_limit if length > recipes_limit else length
            data[i]['recipes'] = data[i]['recipes'][:new_length]

        return super().get_paginated_response(data)
