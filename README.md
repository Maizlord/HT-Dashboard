
# HappyThings Dashboard (Streamlit)

Tablero interactivo conectado a tu Excel **HappyThings (2).xlsx**.

## ✅ Qué muestra
- Ventas totales, órdenes, AOV, COGS aproximado y margen bruto.
- Ventas por **canal** (Web, MercadoLibre, WhatsApp, Instagram, etc.).
- Ventas por **forma de pago** (MercadoPago, transferencia, etc.).
- Serie de **ventas mensuales** y **top 5 meses**.
- **Top 10 productos** por ingreso.
- **Inventario**: stock total, valor a costo y a PVP + tabla completa.
- **Gastos**: sumas por moneda y por "Pago por".
- Filtros por **rango de fechas**, **canal** y **forma de pago**.

## 🔐 Acceso
- Usuario: `admin`
- Contraseña: `admin`
> *Autenticación simple para demo. No usar en producción.*

## 🚀 Cómo ejecutar
1. Tener **Python 3.10+** instalado.
2. Abrir una terminal en esta carpeta.
3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Dejar el archivo **HappyThings (2).xlsx** en la misma carpeta (o usa la opción de *Subir archivo*).
5. Ejecutar:
   ```bash
   streamlit run app.py
   ```

## 🔄 ¿Cómo se actualiza?
El tablero **lee el Excel cada vez que lo cargas** (por ruta o subiéndolo). Si actualizas el Excel, vuelve a cargarlo y el tablero se refresca.

## 🧩 Columnas esperadas
- **Ventas**: `Fecha`, `Item`, `Cantidad`, `Monto Neto`, `Envío (UYU)`, `Canal de venta`, `Forma de pago`, `Ventas totales`.
- **Inventario**: `Item`, `Stock real`, `Precio Venta Publico`, `Precio Venta Mayorista`, `Costo`.
- **Gastos**: `Detalle`, `Monto.1` (numérico), `Moneda` / o moneda en `Monto`, `Fecha`, `Pago por`.
- **Retiro** (opcional).

## 🛡️ Notas
- El cálculo de **COGS** y **margen** es aproximado: usa `Costo` de **Inventario** por `Item` × `Cantidad` vendida.
- Si cambian nombres de columnas, ajusta el código en `app.py` (sección *clean_*).
