def period_choices(request):
    return {
        'period_choices': [
            ('day', 'Hoy'),
            ('week', 'Esta semana'),
            ('month', 'Este mes'),
        ]
    }
