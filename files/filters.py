import django_filters
from django.db.models import Q
from files.models import Registro

class RegistroFilter(django_filters.FilterSet):
    fecha_inicio = django_filters.DateFilter(field_name='fecha', lookup_expr='gte', label='Fecha desde')
    fecha_fin = django_filters.DateFilter(field_name='fecha', lookup_expr='lte', label='Fecha hasta')
    usuario = django_filters.CharFilter(field_name='usuario__username', method='buscar_usuario', label='Usuario')
    accion = django_filters.ChoiceFilter(field_name='accion', choices=[('C', 'Creación'), ('M', 'Modificación'), ('E', 'Eliminación')], label='Acción')

    def buscar_usuario(self, queryset, name, value):
        if not value:
            return queryset

        # 1. Split the value into tokens (e.g., "John Doe" -> ["John", "Doe"])
        # shlex.split handles quoted phrases like '"New York" City' as single tokens
        tokens = value.split() 

        for token in tokens:
            # 2. For each token, we want to match username OR first_name OR last_name
            queryset = queryset.filter(
                Q(usuario__username__icontains=token) |
                Q(usuario__first_name__icontains=token) |
                Q(usuario__last_name__icontains=token)
        )
    
        # 3. Use distinct() because filtering across joins can return duplicates
        return queryset.distinct()
    
    class Meta:
        model = Registro
        fields = ['fecha_inicio', 'fecha_fin', 'usuario', 'accion']