from django import forms
from .models import Cliente, Anticipo, DescuentoCliente, Tienda
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, HTML
from django.utils import timezone

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            'nombre', 'contacto', 'tienda', 'saldo_a_favor', 
            'monto_acumulado', 'puntos_lealtad', 'max_return_days', 'observaciones', 'user'
        ]
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 3}),
            'user': forms.Select(attrs={'class': 'select2'}), # Asumiendo que quieres un select2 para el usuario
        }
        help_texts = {
            'user': 'Usuario del sistema para login de esta distribuidora (opcional).'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('nombre', css_class='form-group col-md-6 mb-0'),
                Column('contacto', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('tienda', css_class='form-group col-md-6 mb-0'),
                Column('user', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('saldo_a_favor', css_class='form-group col-md-4 mb-0'),
                Column('monto_acumulado', css_class='form-group col-md-4 mb-0'),
                Column('puntos_lealtad', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('max_return_days', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'observaciones',
            Submit('submit', 'Guardar Cliente')
        )
        # Populate tienda choices if not already populated by Django's ModelChoiceField
        if 'tienda' in self.fields:
            self.fields['tienda'].queryset = Tienda.objects.all()
        # Consider populating user choices carefully if there are many users

class AnticipoForm(forms.ModelForm):
    fecha = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=timezone.now().date(),
        label="Fecha del Anticipo"
    )
    class Meta:
        model = Anticipo
        fields = ['cliente', 'monto', 'fecha'] # 'observaciones' no existe en el modelo Anticipo

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'cliente',
            'monto',
            'fecha',
            Submit('submit', 'Guardar Anticipo')
        )
        if 'cliente' in self.fields:
            self.fields['cliente'].queryset = Cliente.objects.all()
            self.fields['cliente'].widget.attrs.update({'class': 'select2'})


class DescuentoClienteForm(forms.ModelForm):
    mes_vigente = forms.CharField(
        label="Mes Vigente (YYYY-MM)",
        widget=forms.TextInput(attrs={'type': 'month', 'class': 'form-control'}),
        initial=timezone.now().strftime('%Y-%m')
    )
    class Meta:
        model = DescuentoCliente
        fields = ['cliente', 'mes_vigente', 'porcentaje', 'monto_acumulado_mes_anterior']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'cliente',
            'mes_vigente',
            'porcentaje',
            'monto_acumulado_mes_anterior',
            Submit('submit', 'Guardar Descuento')
        )
        if 'cliente' in self.fields:
            self.fields['cliente'].queryset = Cliente.objects.all()
            self.fields['cliente'].widget.attrs.update({'class': 'select2'})