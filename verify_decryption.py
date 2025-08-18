#!/usr/bin/env python3
import os

def verify_decryption():
    """Verificar si los archivos realmente se descifraron"""
    print("VERIFICANDO DESCIFRADO DRM")
    print("=" * 40)
    
    base_path = "decrypted_content"
    orig_dir = os.path.join(base_path, "original_segments")
    decr_dir = os.path.join(base_path, "decrypted_segments")
    
    total_files = 0
    same_files = 0
    encrypted_originals = 0
    valid_decrypted = 0
    
    # Verificar primeros 50 segmentos
    for i in range(50):
        orig_file = os.path.join(orig_dir, f"original_{i:04d}.ts")
        decr_file = os.path.join(decr_dir, f"decrypted_{i:04d}.ts")
        
        if os.path.exists(orig_file) and os.path.exists(decr_file):
            total_files += 1
            
            # Leer primeros bytes
            with open(orig_file, 'rb') as f:
                orig_data = f.read(16)
            with open(decr_file, 'rb') as f:
                decr_data = f.read(16)
            
            # Verificar si son idénticos
            if orig_data == decr_data:
                same_files += 1
            
            # Verificar encriptación
            if len(orig_data) > 0 and orig_data[0] != 0x47:
                encrypted_originals += 1
            
            if len(decr_data) > 0 and decr_data[0] == 0x47:
                valid_decrypted += 1
            
            # Mostrar algunos ejemplos
            if i < 10:
                orig_hex = orig_data[:4].hex() if len(orig_data) >= 4 else "vacio"
                decr_hex = decr_data[:4].hex() if len(decr_data) >= 4 else "vacio"
                identical = "SI" if orig_data == decr_data else "NO"
                
                print(f"Seg {i:03d}: Orig={orig_hex} Desc={decr_hex} Identicos={identical}")
    
    print("\nRESULTADOS:")
    print(f"Archivos verificados: {total_files}")
    print(f"Archivos idénticos (no descifrados): {same_files}")
    print(f"Originales encriptados: {encrypted_originals}")
    print(f"Descifrados válidos (0x47): {valid_decrypted}")
    
    # Diagnóstico
    print("\nDIAGNOSTICO:")
    if same_files == total_files:
        print("PROBLEMA: Los archivos 'descifrados' son identicos a los originales")
        print("   El proceso de descifrado NO funciono correctamente")
    elif same_files > total_files * 0.8:
        print("PARCIAL: Mayoria de archivos no fueron descifrados")
    else:
        print("CORRECTO: Los archivos fueron modificados (descifrados)")
    
    if encrypted_originals == 0:
        print("EXTRANO: Ningun archivo original parece estar encriptado")
        print("   Puede que el contenido no tuviera DRM real")
    
    return {
        'total': total_files,
        'identical': same_files,
        'encrypted_originals': encrypted_originals,
        'valid_decrypted': valid_decrypted
    }

if __name__ == "__main__":
    verify_decryption()