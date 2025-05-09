"""
apps/guidelines/views.py

ViewSet and router for Guideline endpoints.
Delegates all ORM operations to services for testability.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Guideline
from .serializers import GuidelineSerializer, GuidelineMinimalSerializer
from .services import GuidelineService

class GuidelineViewSet(viewsets.ModelViewSet):
    """CRUD endpoints for guidelines."""
    serializer_class = GuidelineSerializer

    def get_queryset(self):
        return GuidelineService.list_guidelines()

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'minimal']:
            return []  # Allow unauthenticated access for read-only
        return [permissions.IsAuthenticated()]

    def retrieve(self, request, *args, **kwargs):
        guideline = GuidelineService.get_guideline(kwargs['pk'])
        serializer = self.get_serializer(guideline)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='minimal', permission_classes=[])
    def minimal(self, request):
        """
        Returns a minimal list of guidelines using the GuidelineMinimalSerializer.
        """
        print(f"[GUIDELINE_VIEW - MINIMAL] Request headers: {request.headers}")
        print(f"[GUIDELINE_VIEW - MINIMAL] Request GET params: {request.GET}")
        print(f"[GUIDELINE_VIEW - MINIMAL] Request POST data: {request.POST}")
        queryset = self.get_queryset()
        serializer = GuidelineMinimalSerializer(queryset, many=True)
        return Response(serializer.data)


    def create(self, request, *args, **kwargs):
        self.check_permissions(request)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        guideline = GuidelineService.create_guideline(serializer.validated_data, request.user)
        return Response(self.get_serializer(guideline).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        self.check_permissions(request)
        partial = kwargs.pop('partial', False)
        guideline = GuidelineService.get_guideline(kwargs['pk'])
        serializer = self.get_serializer(guideline, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated = GuidelineService.update_guideline(guideline, serializer.validated_data)
        return Response(self.get_serializer(updated).data)

    def destroy(self, request, *args, **kwargs):
        self.check_permissions(request)
        guideline = GuidelineService.get_guideline(kwargs['pk'])
        GuidelineService.delete_guideline(guideline)
        return Response(status=status.HTTP_204_NO_CONTENT)