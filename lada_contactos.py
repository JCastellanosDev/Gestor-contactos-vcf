
import pandas as pd
from pathlib import Path
import re
import traceback

def buscar_encabezados(ruta_archivo):
    """
    Escanea las primeras filas del archivo para identificar la ubicación
    de las columnas 'name' y 'phone'.
    """
    try:
        # Se cargan solo las primeras 10 filas para optimizar memoria
        df_muestra = pd.read_excel(ruta_archivo, header=None, nrows=10)

        for i, fila in df_muestra.iterrows():
            # Concatenamos los valores de la fila para buscar palabras clave
            contenido = ' '.join(str(v).lower() for v in fila if pd.notna(v))
            if 'name' in contenido and 'phone' in contenido:
                print(f"Estructura detectada en la fila: {i}")
                return i
        return None
    except Exception as e:
        print(f"Error al analizar estructura: {e}")
        return None

def normalizar_cadena_numerica(dato):
    """
    Procesa el dato de entrada para extraer únicamente los dígitos.
    Maneja el error común de Excel que añade '.0' a valores numéricos.
    """
    if pd.isna(dato):
        return ""

    cadena = str(dato).strip()

    if cadena.endswith('.0'):
        cadena = cadena[:-2]

    # Utilizamos expresiones regulares para conservar solo caracteres del 0-9
    return re.sub(r'\D', '', cadena)

def validar_codigo_area(numero, codigo):
    """
    Determina si un número telefónico pertenece a una zona geográfica específica.
    """
    if not codigo:
        return True

    limpio = normalizar_cadena_numerica(numero)
    return codigo in limpio

def procesar_archivo_excel(ruta, filtro_area=None):
    """
    Orquestador de la lectura y filtrado de datos.
    Busca registros donde el nombre coincida con el teléfono o sea nulo.
    """
    try:
        print("Iniciando análisis del archivo...")
        idx_header = buscar_encabezados(ruta)

        if idx_header is None:
            print("Error: No se pudo determinar la fila de encabezados.")
            return []

        df = pd.read_excel(ruta, header=idx_header)

        if 'Name' not in df.columns or 'Phone Number' not in df.columns:
            print("Error: El esquema de columnas es inválido.")
            return []

        # Limpieza inicial de datos vacíos en la columna crítica
        df = df.dropna(subset=['Phone Number'])
        df = df[df['Phone Number'].astype(str).str.strip() != '']

        # Aplicación de filtro por zona si existe
        if filtro_area:
            df = df[df['Phone Number'].apply(lambda x: validar_codigo_area(x, filtro_area))]
            print(f"Registros tras filtrar por área ({filtro_area}): {len(df)}")

        def es_contacto_no_guardado(registro):
            """
            Lógica interna para identificar números que no tienen un nombre real.
            """
            try:
                nombre_raw = str(registro['Name']).strip()

                if pd.isna(registro['Name']) or not nombre_raw or nombre_raw.lower() == 'nan':
                    return True

                n_limpio = normalizar_cadena_numerica(nombre_raw)
                t_limpio = normalizar_cadena_numerica(registro['Phone Number'])

                # Caso 1: El nombre guardado es el mismo número
                if n_limpio == t_limpio:
                    return True

                # Caso 2: Coincidencia parcial en los últimos 10 dígitos
                if len(n_limpio) >= 10 and len(t_limpio) >= 10:
                    if n_limpio[-10:] == t_limpio[-10:] and n_limpio.isdigit():
                        return True

                return False
            except Exception:
                return False

        df_final = df[df.apply(es_contacto_no_guardado, axis=1)].copy()

        print("-" * 40)
        print("RESULTADOS DEL ANÁLISIS")
        print(f"Registros válidos analizados: {len(df)}")
        print(f"Números identificados sin nombre: {len(df_final)}")
        print("-" * 40)

        lista_final = []
        for n in df_final['Phone Number'].unique():
            num = normalizar_cadena_numerica(n)
            if num and len(num) >= 10:
                # Estandarización internacional para México
                if num.startswith('52') and len(num) == 12:
                    num = '+' + num
                lista_final.append(num)

        return sorted(set(lista_final))

    except Exception as e:
        print(f"Error durante el procesamiento: {e}")
        traceback.print_exc()
        return []

def generar_vcf(lista, salida, prefijo, inicio=0):
    """
    Escribe los datos en formato vCard versión 3.0.
    """
    if not lista:
        return

    try:
        with open(salida, 'w', encoding='utf-8') as f:
            for i, num in enumerate(lista):
                contador = inicio + i
                nombre_contacto = f"{prefijo} {contador}"

                f.write("BEGIN:VCARD\n")
                f.write("VERSION:3.0\n")
                f.write(f"FN:{nombre_contacto}\n")
                f.write(f"N:{contador};{prefijo};;;\n")
                f.write(f"TEL;TYPE=CELL:{num}\n")
                f.write("END:VCARD\n")

        print(f"Archivo exportado correctamente: {salida}")
    except Exception as e:
        print(f"Error al escribir archivo VCF: {e}")

def main():
    """
    Punto de entrada de la aplicación.
    """
    print("EXTRACTOR DE CONTACTOS PROFESIONAL")
    print("-" * 40)

    nombre_archivo = input("Ruta del archivo Excel: ").strip()

    if not Path(nombre_archivo).exists():
        print("El archivo especificado no existe.")
        return

    area = input("Código de área para filtrar (ej. 614) [Presiona Enter para omitir]: ").strip()

    numeros_procesados = procesar_archivo_excel(nombre_archivo, area if area else None)

    if not numeros_procesados:
        print("No se encontraron registros para procesar.")
        return

    confirmar = input(f"¿Generar archivo VCF para {len(numeros_procesados)} números? (s/n): ").lower()
    if confirmar != 's':
        return

    nombre_base = input("Prefijo del contacto [cliente]: ").strip() or "cliente"

    try:
        # El número inicial ahora es 0 por defecto si se deja vacío
        entrada_inicio = input("Índice numérico inicial [0]: ").strip()
        num_inicio = int(entrada_inicio) if entrada_inicio else 0
    except ValueError:
        num_inicio = 0

    archivo_vcf = input("Nombre del archivo de salida [contactos_nuevos.vcf]: ").strip() or "contactos_nuevos.vcf"

    generar_vcf(numeros_procesados, archivo_vcf, nombre_base, num_inicio)
    print("Proceso completado exitosamente.")

if __name__ == "__main__":
    main()