import subprocess
import sys
import os
import ctypes

try:
    # Informa ao Windows que este é um programa único
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("meu_projeto.theautobot.v7")
except:
    pass

# CONFIGURAÇÃO
arquivo_script = "automacao.py" 
nome_do_programa = "TheAutobot"
arquivo_icone = "icone.ico"  # <--- Nome atualizado aqui
pacotes_necessarios = ["pyautogui", "PyPDF2", "pywin32"]

def verificar_e_instalar():
    print("--- INICIANDO DIAGNÓSTICO DE AMBIENTE ---")
    
    # 1. Verifica se o script principal existe
    if not os.path.exists(arquivo_script):
        print(f"❌ ERRO: O arquivo '{arquivo_script}' não foi encontrado!")
        return False

    # 2. Verifica se o ícone existe (Evita o erro de 'Unable to find')
    if not os.path.exists(arquivo_icone):
        print(f"❌ ERRO: O ícone '{arquivo_icone}' não foi encontrado na pasta!")
        print("👉 Verifique se o nome do arquivo é exatamente icone.ico")
        return False

    # 3. Testa a importação de cada pacote
    for pacote in pacotes_necessarios:
        try:
            nome_import = "win32gui" if pacote == "pywin32" else pacote
            __import__(nome_import)
            print(f"✅ {pacote}: OK")
        except ImportError:
            print(f"⚠️ {pacote} não encontrado. Instalando...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pacote])
                print(f"✅ {pacote} instalado com sucesso!")
            except Exception as e:
                print(f"❌ Falha ao instalar {pacote}: {e}")
                return False
    
    # 4. Verifica o PyInstaller
    try:
        import PyInstaller
        print("✅ PyInstaller: OK")
    except ImportError:
        print("⚠️ PyInstaller não encontrado. Instalando...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    return True

def empacotar():
    if not verificar_e_instalar():
        print("\nO Diagnóstico falhou. Corrija os erros acima.")
        input("\nPressione Enter para sair...")
        return

    print(f"\n--- INICIANDO EMPACOTAMENTO DE {nome_do_programa} ---")
    
    # COMANDO ATUALIZADO
    comando = [
        sys.executable, "-m", "PyInstaller",
        '--onefile',
        '--noconsole',
        '--clean',
        f'--icon={arquivo_icone}',           # Define o ícone do arquivo .exe
        f'--add-data={arquivo_icone};.',     # Embuti o ícone dentro do programa
        f'--name={nome_do_programa}',
        arquivo_script
    ]

    try:
        subprocess.check_call(comando)
        print("\n" + "="*40)
        print(f"✨ SUCESSO TOTAL! ✨")
        print(f"O executável está na pasta 'dist'.")
        print("="*40)
    except Exception as e:
        print(f"\n❌ Erro durante o PyInstaller: {e}")
    
    input("\nProcesso finalizado. Pressione Enter para fechar...")

if __name__ == "__main__":
    empacotar()