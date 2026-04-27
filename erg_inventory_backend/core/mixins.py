class CreatedByMixin:
    """Guarda automáticamente quién creó el registro."""
    def perform_create(self, serializer):
        serializer.save(creado_por=self.request.user)
