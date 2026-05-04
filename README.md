# Gestor de Contactos VCF

Conjunto de herramientas en Python para gestionar contactos de clientes
y automatizar campañas de difusión por WhatsApp.

Desarrollado para uso real en negocio de restaurante.

Herramientas incluidas

### 1. `lada_contactos.py`
Lee un historial de llamadas en Excel y extrae números sin nombre guardado,
con opción de filtrar por código de área (ej: 614 para Chihuahua).

### 2. `historial_contactos.py`
Procesa el historial completo de llamadas y genera un archivo VCF
con los contactos nuevos detectados.

### 3. `renombrar_contactos.py`
Renumera secuencialmente los contactos con formato "Cliente X",
detecta el último cliente agregado y mantiene el orden limpio.

##  App requerida para el historial
Necesitas descargar la app  en tu celular
para exportar el historial de llamadas en formato Excel (.xlsx),
que es el archivo que usan estos scripts.

# Cómo usarlo

Instala las dependencias:

```bash
pip install pandas openpyxl
```

Ejecuta el script que necesites:

```bash
python lada_contactos.py
python historial_contactos.py
python renombrar_contactos.py
```

##  Requisitos
- Python 3.8+
- pandas
- openpyxl

##  Caso de uso real
Sistema de gestión de clientes para restaurante:
captura números de clientes que llaman, los organiza como contactos
y permite enviar publicidad masiva por estados de WhatsApp.

##  Privacidad
Los archivos .vcf y .xlsx con datos reales están excluidos
del repositorio por protección de datos.

## 👤 Autor
Jesús Castellanos - [@JCastellanosDev](https://github.com/JCastellanosDev)

## 📄 Licencia
MIT
