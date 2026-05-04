import pandas as pd
from pathlib import Path
import re
import traceback


def buscar_fila_encabezados(ruta_archivo):
    """
    Localiza el índice de la fila que contiene las columnas 'name' y 'phone'.
    Analiza las primeras 10 filas para optimizar la búsqueda.
    """
    try:
        df_muestreo = pd.read_excel(ruta_archivo, header=None, nrows=10)

        for indice, fila in df_muestreo.iterrows():
            contenido_fila = ' '.join(str(valor).lower() for valor in fila if pd.notna(valor))
            if 'name' in contenido_fila and 'phone' in contenido_fila:
                print(f"Encabezados detectados en la fila: {indice}")
                return indice
        return None
    except Exception as error:
        print(f"Error durante el escaneo de encabezados: {error}")
        return None


def normalizar_telefono(dato):
    """
    Limpia y estandariza el formato de los números telefónicos.
    Elimina sufijos decimales de Excel y caracteres no numéricos.
    """
    if pd.isna(dato):
        return ""

    cadena = str(dato).strip()

    # Corrección de formato decimal heredado de Excel
    if cadena.endswith('.0'):
        cadena = cadena[:-2]

    # Extracción de caracteres numéricos mediante expresiones regulares
    solo_digitos = re.sub(r'\D', '', cadena)

    return solo_digitos


def procesar_registros_excel(ruta_archivo):
    """
    Carga el archivo y filtra registros que carecen de un nombre válido.
    Retorna una lista de números únicos normalizados.
    """
    try:
        print("Iniciando análisis de estructura de archivo...")
        indice_cabecera = buscar_fila_encabezados(ruta_archivo)

        if indice_cabecera is None:
            print("No se identificaron las columnas requeridas automáticamente.")
            return []

        df = pd.read_excel(ruta_archivo, header=indice_cabecera)
        print(f"Lectura exitosa: {len(df)} registros cargados.")

        if 'Name' not in df.columns or 'Phone Number' not in df.columns:
            print("Error: El archivo no cumple con el esquema 'Name' y 'Phone Number'.")
            return []

        # Depuración de registros sin número telefónico
        df = df.dropna(subset=['Phone Number'])
        df = df[df['Phone Number'].astype(str).str.strip() != '']

        def validar_ausencia_nombre(registro):
            try:
                nombre_raw = str(registro['Name']).strip()

                if pd.isna(registro['Name']) or not nombre_raw or nombre_raw.lower() == 'nan':
                    return True

                nombre_limpio = normalizar_telefono(nombre_raw)
                tel_limpio = normalizar_telefono(registro['Phone Number'])

                # Si el nombre es idéntico al número, se considera contacto no guardado
                if nombre_limpio == tel_limpio:
                    return True

                # Validación por coincidencia de terminales (últimos 10 dígitos)
                if len(nombre_limpio) >= 10 and len(tel_limpio) >= 10:
                    if nombre_limpio[-10:] == tel_limpio[-10:] and nombre_limpio.isdigit():
                        return True

                return False
            except Exception:
                return False

        df_filtrado = df[df.apply(validar_ausencia_nombre, axis=1)].copy()

        print("-" * 30)
        print("RESUMEN DE PROCESAMIENTO")
        print(f"Total registros: {len(df)}")
        print(f"Contactos identificados: {len(df) - len(df_filtrado)}")
        print(f"Contactos por procesar: {len(df_filtrado)}")
        print("-" * 30)

        lista_numeros = df_filtrado['Phone Number'].dropna().unique()
        resultados = []

        for n in lista_numeros:
            limpio = normalizar_telefono(n)
            if limpio and len(limpio) >= 10:
                # Prefijo internacional para México si cumple longitud
                if limpio.startswith('52') and len(limpio) == 12:
                    limpio = '+' + limpio
                resultados.append(limpio)

        return sorted(set(resultados))

    except FileNotFoundError:
        print(f"Error: El archivo '{ruta_archivo}' no existe en el directorio.")
        return []
    except Exception as error:
        print(f"Fallo en la ejecución del proceso: {error}")
        traceback.print_exc()
        return []


def generar_vcf(lista_contactos, salida='contactos_nuevos.vcf', prefijo='cliente', inicio=0):
    """
    Genera el archivo VCF compatible con dispositivos móviles.
    """
    if not lista_contactos:
        print("Operación abortada: No hay datos para exportar.")
        return

    try:
        with open(salida, 'w', encoding='utf-8') as archivo:
            for i, tel in enumerate(lista_contactos):
                id_contacto = inicio + i
                nombre_vcard = f"{prefijo} {id_contacto}"

                archivo.write("BEGIN:VCARD\n")
                archivo.write("VERSION:3.0\n")
                archivo.write(f"FN:{nombre_vcard}\n")
                archivo.write(f"N:{id_contacto};{prefijo};;;\n")
                archivo.write(f"TEL;TYPE=CELL:{tel}\n")
                archivo.write("END:VCARD\n")

        print(f"Proceso finalizado. Archivo generado: {salida}")
        print(f"Cantidad de contactos: {len(lista_contactos)}")

    except Exception as error:
        print(f"Error en la escritura del archivo VCF: {error}")


def ejecutor_principal():
    """
    Orquestador del flujo de trabajo.
    """
    print("SISTEMA DE GESTIÓN DE CONTACTOS VCF")

    nombre_excel = input("Ingrese el nombre del archivo Excel (con extensión): ").strip()

    if not Path(nombre_excel).exists():
        print("Error de ruta: Archivo no localizado.")
        return

    datos_numeros = procesar_registros_excel(nombre_excel)

    if not datos_numeros:
        print("No se detectaron registros que cumplan los criterios de filtrado.")
        return

    confirmacion = input(f"Se procesarán {len(datos_numeros)} registros. ¿Continuar? (s/n): ").lower()
    if confirmacion != 's':
        print("Ejecución cancelada por el usuario.")
        return

    nombre_base = input("Ingrese prefijo para los nombres [cliente]: ").strip() or "cliente"
    try:
        # Se establece el valor inicial por defecto en 0
        valor_inicial = input("Ingrese el índice inicial [0]: ").strip()
        valor_inicial = int(valor_inicial) if valor_inicial else 0
    except ValueError:
        valor_inicial = 0

    archivo_vcf = input("Nombre del archivo de salida [contactos_nuevos.vcf]: ").strip() or "contactos_nuevos.vcf"

    generar_vcf(datos_numeros, archivo_vcf, nombre_base, valor_inicial)


if __name__ == "__main__":
    ejecutor_principal()