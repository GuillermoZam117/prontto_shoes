from django import forms
from .models import Producto, Catalogo
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'codigo', 'marca', 'modelo', 'color', 'propiedad', 
            'costo', 'precio', 'numero_pagina', 'temporada', 
            'oferta', 'admite_devolucion', 'stock_minimo', 
            'proveedor', 'tienda', 'catalogo'
        ]
        widgets = {
            'oferta': forms.CheckboxInput(),
            'admite_devolucion': forms.CheckboxInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('codigo', css_class='form-group col-md-6 mb-0'),
                Column('marca', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('modelo', css_class='form-group col-md-6 mb-0'),
                Column('color', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('propiedad', css_class='form-group col-md-6 mb-0'),
                Column('numero_pagina', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('costo', css_class='form-group col-md-4 mb-0'),
                Column('precio', css_class='form-group col-md-4 mb-0'),
                Column('stock_minimo', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('temporada', css_class='form-group col-md-4 mb-0'),
                Column('catalogo', css_class='form-group col-md-4 mb-0'),
                Column('proveedor', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('tienda', css_class='form-group col-md-4 mb-0'),
                Column('oferta', css_class='form-group col-md-4 mb-0 align-self-center'),
                Column('admite_devolucion', css_class='form-group col-md-4 mb-0 align-self-center'),
                css_class='form-row mt-3'
            ),
            Submit('submit', 'Guardar Producto')
        )

class ProductoImportForm(forms.Form):
    excel_file = forms.FileField(label="Archivo Excel de Productos")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'excel_file',
            Submit('submit', 'Importar Productos', css_class='btn-success')
        )