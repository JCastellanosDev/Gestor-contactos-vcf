import re
from datetime import datetime


def procesar_vcf(archivo_entrada, archivo_salida=None):
    """
    Procesa un archivo VCF y RENUMERA SOLO los contactos con formato 'Cliente X'
    """

    if archivo_salida is None:
        # Crear nombre automático con fecha
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archivo_salida = f'contactos_reordenados_{timestamp}.vcf'

    # Leer el archivo VCF
    print(f"\n Leyendo archivo: {archivo_entrada}")
    try:
        with open(archivo_entrada, 'r', encoding='utf-8') as f:
            contenido = f.read()
    except UnicodeDecodeError:
        with open(archivo_entrada, 'r', encoding='latin-1') as f:
            contenido = f.read()

    # Dividir en contactos individuales
    contactos = contenido.split('BEGIN:VCARD')
    contactos = [c for c in contactos if c.strip()]

    print(f" Total de contactos encontrados: {len(contactos)}")

    # Primer paso: identificar contactos con formato "Cliente X"
    contactos_cliente = []
    contactos_otros = []

    for contacto in contactos:
        # Buscar el nombre actual
        match_nombre = re.search(r'FN:(.+)', contacto)

        if match_nombre:
            nombre = match_nombre.group(1).strip()

            # Verificar si tiene el formato "Cliente X"
            match_cliente = re.match(r'Cliente\s+(\d+)$', nombre, re.IGNORECASE)

            if match_cliente:
                numero_original = int(match_cliente.group(1))
                match_telefono = re.search(r'TEL[^:]*:(.+)', contacto)
                telefono = match_telefono.group(1).strip() if match_telefono else "Sin teléfono"

                # Buscar fecha de revisión (última modificación)
                match_rev = re.search(r'REV:(.+)', contacto)
                fecha_rev = match_rev.group(1).strip() if match_rev else None

                contactos_cliente.append({
                    'contacto': contacto,
                    'numero_original': numero_original,
                    'telefono': telefono,
                    'fecha_rev': fecha_rev
                })
            else:
                contactos_otros.append(contacto)
        else:
            contactos_otros.append(contacto)

    print(f"\n ANÁLISIS:")
    print(f"    Contactos con formato 'Cliente X': {len(contactos_cliente)}")
    print(f"    Otros contactos: {len(contactos_otros)}")

    if len(contactos_cliente) == 0:
        print("\n⚠️  No se encontraron contactos con formato 'Cliente (número)'.")
        return

    # Identificar el último cliente agregado (número más alto)
    cliente_con_numero_mas_alto = max(contactos_cliente, key=lambda x: x['numero_original'])

    print(f"\n ÚLTIMO CLIENTE AGREGADO:")
    print(f"   {'─' * 66}")
    print(f"    Cliente {cliente_con_numero_mas_alto['numero_original']}")
    print(f"    Teléfono: {cliente_con_numero_mas_alto['telefono']}")
    if cliente_con_numero_mas_alto['fecha_rev']:
        try:
            # Intentar formatear la fecha si está en formato ISO
            fecha_str = cliente_con_numero_mas_alto['fecha_rev']
            if 'T' in fecha_str:
                fecha_formateada = fecha_str.split('T')[0]
                print(f"    Última modificación: {fecha_formateada}")
        except:
            pass
    print(f"   {'─' * 66}")

    # Mostrar rango de números actuales
    numero_minimo = min(contactos_cliente, key=lambda x: x['numero_original'])['numero_original']
    numero_maximo = cliente_con_numero_mas_alto['numero_original']
    print(f"\n Rango actual: Cliente {numero_minimo} a Cliente {numero_maximo}")
    print(f" Después de renumerar: Cliente 1 a Cliente {len(contactos_cliente)}")

    # Ordenar por número original (para mantener cierto orden)
    contactos_cliente.sort(key=lambda x: x['numero_original'])

    # Segundo paso: renumerar secuencialmente
    print(f"\n  Renumerando contactos del 1 al {len(contactos_cliente)}...")

    nuevos_contactos = []
    renumerados = []

    # Agregar primero los contactos que NO son "Cliente X"
    for contacto in contactos_otros:
        nuevos_contactos.append('BEGIN:VCARD' + contacto)

    # Renumerar los contactos "Cliente X"
    for i, datos in enumerate(contactos_cliente, start=1):
        contacto = datos['contacto']
        numero_original = datos['numero_original']
        telefono = datos['telefono']

        nuevo_nombre = f'Cliente {i}'

        # Reemplazar el nombre en FN y N
        contacto_modificado = re.sub(
            r'FN:Cliente\s+\d+',
            f'FN:{nuevo_nombre}',
            contacto,
            flags=re.IGNORECASE
        )
        contacto_modificado = re.sub(
            r'N:Cliente\s+\d+',
            f'N:{nuevo_nombre}',
            contacto_modificado,
            flags=re.IGNORECASE
        )

        nuevos_contactos.append('BEGIN:VCARD' + contacto_modificado)

        renumerados.append({
            'numero_anterior': numero_original,
            'numero_nuevo': i,
            'telefono': telefono,
            'era_el_ultimo': numero_original == numero_maximo
        })

    # Guardar el archivo procesado
    with open(archivo_salida, 'w', encoding='utf-8') as f:
        f.write(''.join(nuevos_contactos))

    # Mostrar resumen
    print(f"\n PROCESO COMPLETADO")
    print(f"=" * 70)
    print(f" Contactos renumerados: {len(renumerados)}")
    print(f" Archivo guardado: {archivo_salida}")

    if renumerados and len(renumerados) <= 50:  # Mostrar lista si no son muchos
        print(f"\n📋 LISTA DE CAMBIOS:")
        print(f"-" * 70)
        for r in renumerados:
            marcador = " ⭐ (ÚLTIMO AGREGADO)" if r['era_el_ultimo'] else ""
            print(f"   Cliente {r['numero_anterior']:>3} → Cliente {r['numero_nuevo']:>3} ({r['telefono']}){marcador}")
    elif len(renumerados) > 50:
        print(f"\n📋 PRIMEROS 20 CAMBIOS:")
        print(f"-" * 70)
        for r in renumerados[:20]:
            marcador = " ⭐ (ÚLTIMO AGREGADO)" if r['era_el_ultimo'] else ""
            print(f"   Cliente {r['numero_anterior']:>3} → Cliente {r['numero_nuevo']:>3} ({r['telefono']}){marcador}")
        print(f"   ... y {len(renumerados) - 20} más")

        # Buscar el último agregado en el resto
        ultimo_en_lista = next((r for r in renumerados if r['era_el_ultimo']), None)
        if ultimo_en_lista and ultimo_en_lista not in renumerados[:20]:
            print(
                f"\n   Cliente {ultimo_en_lista['numero_anterior']:>3} → Cliente {ultimo_en_lista['numero_nuevo']:>3} ({ultimo_en_lista['telefono']}) ⭐ (ÚLTIMO AGREGADO)")

    print(f"\n💡 RESULTADO:")
    print(f"   • {len(contactos_otros)} contactos sin cambios")
    print(f"   • {len(renumerados)} contactos renumerados del 1 al {len(renumerados)}")
    print(f"   • El que era 'Cliente {numero_maximo}' ahora es 'Cliente {len(renumerados)}'")
    print(f"   • Siguiente cliente nuevo será: Cliente {len(renumerados) + 1}")


def mostrar_vista_previa(archivo):
    """Muestra una vista previa antes de procesar"""
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
    except UnicodeDecodeError:
        with open(archivo, 'r', encoding='latin-1') as f:
            contenido = f.read()

    contactos = contenido.split('BEGIN:VCARD')
    contactos = [c for c in contactos if c.strip()]

    # Contar contactos "Cliente X" y encontrar el último
    total_clientes = 0
    ejemplos_clientes = []
    numeros_encontrados = []

    for contacto in contactos:
        nombre_match = re.search(r'FN:(.+)', contacto)
        if nombre_match:
            nombre = nombre_match.group(1).strip()
            match_numero = re.match(r'Cliente\s+(\d+)$', nombre, re.IGNORECASE)
            if match_numero:
                numero = int(match_numero.group(1))
                total_clientes += 1
                numeros_encontrados.append(numero)

                if len(ejemplos_clientes) < 10:
                    tel_match = re.search(r'TEL[^:]*:(.+)', contacto)
                    telefono = tel_match.group(1).strip() if tel_match else "Sin teléfono"
                    ejemplos_clientes.append((nombre, telefono, numero))

    print("\n VISTA PREVIA:")
    print("=" * 70)
    print(f" Total de contactos: {len(contactos)}")
    print(f" Contactos 'Cliente X' encontrados: {total_clientes}")

    if numeros_encontrados:
        numero_max = max(numeros_encontrados)
        numero_min = min(numeros_encontrados)
        print(f" Rango de números: {numero_min} - {numero_max}")
        print(f" Último cliente agregado: Cliente {numero_max}")

    if ejemplos_clientes:
        print(f"\n Ejemplos de contactos que se renumerarán:")
        print("-" * 70)
        # Ordenar ejemplos por número
        ejemplos_clientes.sort(key=lambda x: x[2])
        for nombre, telefono, num in ejemplos_clientes:
            marcador = " ⭐" if num == max(numeros_encontrados) else ""
            print(f"   • {nombre:<20} → {telefono}{marcador}")

        if total_clientes > 10:
            print(f"   ... y {total_clientes - 10} más")
    else:
        print("\n⚠️  No se encontraron contactos con formato 'Cliente X'")

    print("=" * 70)


# ===== PROGRAMA PRINCIPAL =====
if __name__ == "__main__":
    print("=" * 70)
    print(" RENUMERADOR DE CONTACTOS 'CLIENTE X'")
    print("=" * 70)

    # Pedir archivo de entrada
    archivo_entrada = input("\n📁 Nombre del archivo VCF: ").strip()

    if not archivo_entrada.endswith('.vcf'):
        archivo_entrada += '.vcf'

    try:
        # Mostrar vista previa
        mostrar_vista_previa(archivo_entrada)

        # Confirmar
        print("\n Este programa:")
        print("   • Identificará SOLO los contactos con formato 'Cliente X'")
        print("   • Mostrará cuál fue el último cliente agregado (número más alto)")
        print("   • Los renumerará secuencialmente del 1 al N")
        print("   • Mantendrá TODOS los demás contactos sin cambios")

        confirmar = input("\n¿Continuar? (s/n): ").lower()

        if confirmar in ['s', 'si', 'yes', 'y']:
            # Pedir nombre de salida (opcional)
            archivo_salida = input("\n Nombre del archivo de salida (Enter para auto): ").strip()
            if not archivo_salida:
                archivo_salida = None
            elif not archivo_salida.endswith('.vcf'):
                archivo_salida += '.vcf'

            # Procesar
            procesar_vcf(archivo_entrada, archivo_salida)

        else:
            print("\nOperación cancelada")

    except FileNotFoundError:
        print(f"\n ERROR: No se encontró el archivo '{archivo_entrada}'")
        print("   Asegúrate de que el archivo esté en la misma carpeta que este script")
    except Exception as e:
        print(f"\n ERROR: {str(e)}")