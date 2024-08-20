from django.db.models import PositiveIntegerField
from django.core.exceptions import ObjectDoesNotExist


class OrderField(PositiveIntegerField):
    """
    Поле для автоматического определения порядка, отсчёт с 1. Порядок
    определяется относительно других полей модели.
    """
    def __init__(self, fields=None, *args, **kwargs):
        self.fields = fields # поля, относительно которых формируется порядок
        super().__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        if getattr(model_instance, self.attname) is None:
            # Если не поле не передано, автоматически назначаем порядок
            try:
                queryset = self.model.objects.all()
                if self.fields:
                    condition = {field: getattr(model_instance, field) \
                                 for field in self.fields}
                    queryset = queryset.filter(**condition)
                last_object = queryset.latest(self.attname)
                value = getattr(last_object, self.attname) + 1
            except ObjectDoesNotExist:
                value = 1
            setattr(model_instance, self.attname, value)
            return value
        else:
            return super().pre_save(model_instance, add)