"""
apps/risks_credit_political/views.py

ViewSet and router for CreditPoliticalRisk endpoints.
Delegates all ORM operations to services for testability.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import CreditPoliticalRisk
from .serializers import CreditPoliticalRiskSerializer
from .services import CreditPoliticalRiskService


class CreditPoliticalRiskViewSet(viewsets.ModelViewSet):
    """CRUD endpoints for credit & political risks."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CreditPoliticalRiskSerializer

    def get_queryset(self):
        return CreditPoliticalRiskService.list_risks()

    def retrieve(self, request, *args, **kwargs):
        risk = CreditPoliticalRiskService.get_risk(kwargs['pk'])
        serializer = self.get_serializer(risk)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        risk = CreditPoliticalRiskService.create_risk(serializer.validated_data, request.user)
        return Response(self.get_serializer(risk).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        risk = CreditPoliticalRiskService.get_risk(kwargs['pk'])
        serializer = self.get_serializer(risk, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated = CreditPoliticalRiskService.update_risk(risk, serializer.validated_data)
        return Response(self.get_serializer(updated).data)

    def destroy(self, request, *args, **kwargs):
        risk = CreditPoliticalRiskService.get_risk(kwargs['pk'])
        CreditPoliticalRiskService.delete_risk(risk)
        return Response(status=status.HTTP_204_NO_CONTENT) 