from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import Producto, Proveedor, Tienda
from .serializers import ProductoSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from rest_framework.decorators import action
from rest_framework.response import Response
import pandas as pd
import openpyxl
from django.db import transaction

@extend_schema(tags=["Productos"])
class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['codigo', 'marca', 'modelo', 'color', 'proveedor', 'tienda', 'temporada', 'oferta']

    @swagger_auto_schema(
        operation_description="Importar catálogo de productos desde un archivo Excel.",
        request_body=OpenApiTypes.BINARY,
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT}
    )
    @action(detail=False, methods=['post'])
    def import_catalogo(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No se proporcionó ningún archivo."}, status=status.HTTP_400_BAD_REQUEST)

        if not file.name.endswith(('.xls', '.xlsx')):
            return Response({"error": "El archivo debe ser un archivo Excel (.xls o .xlsx)."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            df = pd.read_excel(file)
        except Exception as e:
            return Response({"error": f"Error al leer el archivo Excel: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        # Define the expected columns (adjust as per your Excel structure)
        expected_columns = ['codigo', 'marca', 'modelo', 'color', 'propiedad', 'costo', 'precio', 'numero_pagina', 'temporada', 'oferta', 'admite_devolucion', 'proveedor', 'tienda']
        if not all(col in df.columns for col in expected_columns):
            missing_cols = [col for col in expected_columns if col not in df.columns]
            return Response({"error": f"Faltan columnas en el archivo Excel: {missing_cols}"}, status=status.HTTP_400_BAD_REQUEST)

        imported_count = 0
        errors = {}

        with transaction.atomic():
            for index, row in df.iterrows():
                codigo = row['codigo']
                try:
                    # Get or create related objects (Proveedor and Tienda)
                    proveedor_nombre = row['proveedor']
                    tienda_nombre = row['tienda']
                    
                    try:
                        proveedor = Proveedor.objects.get(nombre=proveedor_nombre)
                    except Proveedor.DoesNotExist:
                        errors[codigo] = f"Proveedor '{proveedor_nombre}' no encontrado."
                        continue # Skip this row if provider not found
                        
                    try:
                        tienda = Tienda.objects.get(nombre=tienda_nombre)
                    except Tienda.DoesNotExist:
                        errors[codigo] = f"Tienda '{tienda_nombre}' no encontrada."
                        continue # Skip this row if store not found

                    # Create or update the product
                    producto, created = Producto.objects.update_or_create(
                        codigo=codigo,
                        defaults={
                            'marca': row['marca'],
                            'modelo': row['modelo'],
                            'color': row['color'],
                            'propiedad': row['propiedad'],
                            'costo': row['costo'],
                            'precio': row['precio'],
                            'numero_pagina': row['numero_pagina'],
                            'temporada': row['temporada'],
                            'oferta': row['oferta'],
                            'admite_devolucion': row['admite_devolucion'],
                            'proveedor': proveedor,
                            'tienda': tienda,
                        }
                    )
                    imported_count += 1
                except Exception as e:
                    errors[codigo] = f"Error al procesar producto {codigo}: {e}"
                    # continue # You might want to continue processing other rows even if one fails
                    # Or raise the exception to stop the transaction
                    raise e # Raising the exception to rollback the transaction

        if errors:
            return Response({"message": f"Se importaron {imported_count} productos con errores.", "errors": errors}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": f"Catálogo importado exitosamente. {imported_count} productos procesados."}, status=status.HTTP_200_OK)

# Create your views here.
