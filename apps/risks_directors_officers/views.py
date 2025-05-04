"""
apps/risks_directors_officers/views.py

ViewSet and router for Directors & Officers Risk endpoints.
Delegates all ORM operations to services for testability.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import DirectorsOfficersRisk
from .serializers import DirectorsOfficersRiskSerializer
from .services import DirectorsOfficersRiskService


class DirectorsOfficersRiskViewSet(viewsets.ModelViewSet):
    """CRUD endpoints for Directors & Officers risks."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DirectorsOfficersRiskSerializer

    def get_queryset(self):
        return DirectorsOfficersRiskService.list_risks()

    def retrieve(self, request, *args, **kwargs):
        risk = DirectorsOfficersRiskService.get_risk(kwargs['pk'])
        serializer = self.get_serializer(risk)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        risk = DirectorsOfficersRiskService.create_risk(serializer.validated_data, request.user)
        return Response(self.get_serializer(risk).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        risk = DirectorsOfficersRiskService.get_risk(kwargs['pk'])
        serializer = self.get_serializer(risk, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated = DirectorsOfficersRiskService.update_risk(risk, serializer.validated_data)
        return Response(self.get_serializer(updated).data)

    def destroy(self, request, *args, **kwargs):
        risk = DirectorsOfficersRiskService.get_risk(kwargs['pk'])
        DirectorsOfficersRiskService.delete_risk(risk)
        return Response(status=status.HTTP_204_NO_CONTENT) 