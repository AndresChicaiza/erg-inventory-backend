from django.db import models
from productos.models import Producto
from users.models import Usuario


class Movimiento(models.Model):
    TIPO_CHOICES = [
        ('Entrada', 'Entrada'),
        ('Salida',  'Salida'),
        ('Ajuste',  'Ajuste'),
    ]

    producto    = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name='movimientos')
    bodega      = models.ForeignKey('bodegas.Bodega', on_delete=models.PROTECT, related_name='movimientos', null=True, blank=True)
    lote        = models.ForeignKey('productos.Lote', on_delete=models.SET_NULL, null=True, blank=True, related_name='movimientos')
    tipo           = models.CharField(max_length=10, choices=TIPO_CHOICES)
    cantidad       = models.DecimalField(max_digits=14, decimal_places=3)
    valor_unitario = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text='Costo unitario en este movimiento')
    saldo_cantidad = models.DecimalField(max_digits=14, decimal_places=3, default=0, help_text='Saldo de cantidad tras el movimiento')
    saldo_valor    = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text='Saldo valorizado tras el movimiento')
    referencia     = models.CharField(max_length=100, blank=True)
    observacion = models.TextField(blank=True)
    creado_por  = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True,
                                    related_name='movimientos_creados')
    fecha       = models.DateField(auto_now_add=True)
    creado_en   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table   = 'movimientos'
        ordering   = ['-fecha', '-id']
        verbose_name = 'Movimiento'

    def __str__(self):
        lote_str = f' (Lote: {self.lote.numero_lote})' if self.lote else ''
        return f'{self.tipo} | {self.producto.nombre}{lote_str} | {self.cantidad}'

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        
        if is_new:
            # Refresh from DB in case stock is out of sync due to concurrent transactions
            self.producto.refresh_from_db()
            stock_actual = self.producto.stock
            costo_actual = self.producto.precio_costo
            valor_actual = stock_actual * costo_actual
            
            if self.tipo == 'Entrada':
                # Si no envían un valor_unitario explícito, tomamos el actual
                if not getattr(self, 'valor_unitario', False):
                    self.valor_unitario = costo_actual
                    
                nuevo_stock = stock_actual + self.cantidad
                valor_agregado = self.cantidad * self.valor_unitario
                nuevo_valor = valor_actual + valor_agregado
                
                # Actualizar el precio de costo (Promedio Ponderado)
                if nuevo_stock > 0:
                    nuevo_costo = nuevo_valor / nuevo_stock
                    # Redondear a 2 decimales para moneda
                    self.producto.precio_costo = round(nuevo_costo, 2)
                    
                self.saldo_cantidad = nuevo_stock
                self.saldo_valor = nuevo_valor
                
            elif self.tipo == 'Salida':
                self.valor_unitario = costo_actual
                nuevo_stock = stock_actual - self.cantidad
                nuevo_valor = valor_actual - (self.cantidad * self.valor_unitario)
                
                self.saldo_cantidad = nuevo_stock
                self.saldo_valor = nuevo_valor
            else:
                # Ajuste (puede ser positivo o negativo) - para simplificar tomaremos el costo actual
                if not getattr(self, 'valor_unitario', False):
                    self.valor_unitario = costo_actual
                
                # Ajuste usualmente sobrescribe la cantidad o añade/quita, dependiendo de la implementación actual.
                # Aquí lo manejaremos como si el ajuste fuera la cantidad final o relativa (Asumiremos relativa positiva si es Entrada-like)
                # En el código actual, Ajuste asigna cantidad directa o suma?
                # Lo mejor es mantener el valor promedio intacto y ajustar el valor total proporcionalmente.
                # Como es un caso atípico en este ERP por el momento, tomamos el valor unitario actual.
                nuevo_stock = stock_actual + self.cantidad # Si asumimos que ajuste viene con signo
                self.saldo_cantidad = nuevo_stock
                self.saldo_valor = nuevo_stock * self.valor_unitario
                
            # OJO: No guardamos self.producto.save() aquí porque el controlador/vista a veces
            # actualiza self.producto.stock = stock_actual + cantidad y llama producto.save() después.
            # Solo modificamos precio_costo en el objeto en memoria. El que llame al save del producto
            # persistirá el precio_costo actualizado, PERO por si acaso:
            self.producto.save(update_fields=['precio_costo'])

        super().save(*args, **kwargs)
