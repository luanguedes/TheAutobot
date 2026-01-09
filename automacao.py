import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
import pyautogui
import json
import time
import threading
import os
import PyPDF2
import re
import ctypes

# Faz o ícone aparecer corretamente na barra de tarefas do Windows
try:
    myappid = 'meuprojeto.theautobot.v7'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except:
    pass

class AppAutomacaoMestre:
    def __init__(self, root):
        self.root = root
        self.root.title("TheAutobot - Automações V7.1")
        self.root.geometry("750x900")
        
        # Variáveis de Controle
        self.arquivo_dados = tk.StringVar()
        self.passos = [] 
        self.pausar_solicitado = False
        self.logica_selecionada = tk.StringVar(value="Relatório de Faturamento (CÓDIGO-NOME PRESTADOR)")
        self.status_texto = tk.StringVar(value="Pronto")

        # --- 1. CONFIGURAÇÃO DE DADOS ---
        frame_dados = tk.LabelFrame(root, text="1. Lógica de Automação", padx=10, pady=5)
        frame_dados.pack(fill="x", padx=10, pady=5)
        
        self.combo_logica = ttk.Combobox(frame_dados, textvariable=self.logica_selecionada, state="readonly",
                                         values=["Relatório de Faturamento (CÓDIGO-NOME PRESTADOR)", "Simples (Apenas código)"])
        self.combo_logica.pack(fill="x", pady=5)
        
        btn_arq = tk.Button(frame_dados, text="📂 Selecionar PDF ou TXT", command=self.selecionar_arquivo)
        btn_arq.pack(side="left", pady=5)
        tk.Label(frame_dados, textvariable=self.arquivo_dados, fg="blue", wraplength=450).pack(side="left", padx=10)

        frame_ignore = tk.LabelFrame(root, text="Ignorar Códigos (Ex: 1-10, 15, 20-25)", padx=10, pady=5)
        frame_ignore.pack(fill="x", padx=10, pady=5)
        self.txt_ignorar = tk.Entry(frame_ignore)
        self.txt_ignorar.pack(fill="x")

        # --- 2. LISTA DE AÇÕES ---
        frame_lista = tk.LabelFrame(root, text="2. Sequência de Ações", padx=10, pady=5)
        frame_lista.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.listbox = tk.Listbox(frame_lista, font=("Courier", 10))
        self.listbox.pack(side="left", fill="both", expand=True)
        
        frame_ordem = tk.Frame(frame_lista)
        frame_ordem.pack(side="right", fill="y", padx=5)
        tk.Button(frame_ordem, text="▲", command=self.mover_cima, width=3).pack(pady=2)
        tk.Button(frame_ordem, text="▼", command=self.mover_baixo, width=3).pack(pady=2)
        tk.Button(frame_ordem, text="DEL", command=self.remover_passo, bg="#ffcdd2", width=3).pack(side="bottom")

        # --- 3. BOTÕES DE COMANDO ---
        frame_cmds = tk.LabelFrame(root, text="3. Adicionar Comandos", padx=5, pady=5)
        frame_cmds.pack(fill="x", padx=10, pady=5)
        
        tk.Button(frame_cmds, text="+ Clique Esq.", bg="#ffcccb", width=15, command=lambda: self.mapear_clique("left")).grid(row=0, column=0, padx=2, pady=2)
        tk.Button(frame_cmds, text="+ Duplo Clique", bg="#ff9999", width=15, command=lambda: self.mapear_clique("double")).grid(row=0, column=1, padx=2, pady=2)
        tk.Button(frame_cmds, text="+ Clique Dir.", bg="#ff6666", width=15, command=lambda: self.mapear_clique("right")).grid(row=0, column=2, padx=2, pady=2)
        
        tk.Button(frame_cmds, text="+ Tecla Única", bg="#add8e6", width=15, command=self.add_tecla).grid(row=1, column=0, padx=2, pady=2)
        tk.Button(frame_cmds, text="+ Atalho (Ctrl+C)", bg="#87cefa", width=15, command=self.add_atalho_janela).grid(row=1, column=1, padx=2, pady=2)
        tk.Button(frame_cmds, text="+ Espera (s)", bg="#ffe4b5", width=15, command=self.add_espera).grid(row=1, column=2, padx=2, pady=2)

        tk.Button(frame_cmds, text="🔢 [1] Colar SÓ Código", bg="#b2dfdb", width=24, font=("Arial", 8, "bold"), command=lambda: self.add_passo_dado("so_codigo")).grid(row=2, column=0, columnspan=1, padx=2, pady=5)
        tk.Button(frame_cmds, text="📄 [2] Colar Completo", bg="#90ee90", width=24, font=("Arial", 8, "bold"), command=lambda: self.add_passo_dado("completo")).grid(row=2, column=1, columnspan=2, sticky="ew", padx=2, pady=5)

        # --- 4. EXECUÇÃO ---
        self.btn_iniciar = tk.Button(root, text="INICIAR PROCESSO", bg="#2e7d32", fg="white", font=("Arial", 14, "bold"), command=self.iniciar_thread)
        self.btn_iniciar.pack(fill="x", padx=10, pady=5)
        
        self.btn_parar = tk.Button(root, text="PARAR", bg="orange", fg="white", font=("Arial", 10, "bold"), command=self.solicitar_parada, state="disabled")
        self.btn_parar.pack(fill="x", padx=10, pady=5)
        
        frame_foot = tk.Frame(root)
        frame_foot.pack(fill="x", padx=10)
        tk.Button(frame_foot, text="💾 Salvar Receita", command=self.salvar_receita).pack(side="left")
        tk.Button(frame_foot, text="📂 Abrir Receita", command=self.carregar_receita).pack(side="left", padx=5)
        
        tk.Label(root, textvariable=self.status_texto, bd=1, relief=tk.SUNKEN, anchor="w").pack(side="bottom", fill="x")

    def obter_lista_exclusao(self):
        entrada = self.txt_ignorar.get().strip()
        if not entrada: return set()
        ignorar = set()
        partes = [p.strip() for p in entrada.split(",")]
        for p in partes:
            if "-" in p:
                try:
                    inicio, fim = p.split("-")
                    for n in range(int(inicio), int(fim) + 1): ignorar.add(str(n))
                except: continue
            else: ignorar.add(p)
        return ignorar

    def extrair_dados(self):
        caminho = self.arquivo_dados.get()
        logica = self.logica_selecionada.get()
        ignorar = self.obter_lista_exclusao()
        dados_finais = []
        if not caminho: return []
        try:
            texto = ""
            if caminho.lower().endswith(".pdf"):
                with open(caminho, 'rb') as f:
                    pdf = PyPDF2.PdfReader(f)
                    texto = "".join([p.extract_text() or "" for p in pdf.pages])
            else:
                with open(caminho, 'r', encoding='utf-8') as f: texto = f.read()
            
            for linha in texto.split('\n'):
                limpa = linha.strip()
                if not limpa: continue
                
                if "Relatório de Faturamento" in logica:
                    match = re.search(r'^(\d+)\s*-', limpa)
                    if match:
                        codigo = match.group(1)
                        if len(codigo) <= 4 and codigo not in ignorar: 
                            dados_finais.append(limpa)
                else:
                    palavras = limpa.split()
                    for p in palavras:
                        cod_limpo = "".join(filter(str.isdigit, p))
                        if cod_limpo and cod_limpo not in ignorar:
                            dados_finais.append(cod_limpo)
                            
        except Exception as e: 
            messagebox.showerror("Erro Extração", str(e))
        return dados_finais

    def rodar_automacao(self):
        pyautogui.FAILSAFE = True
        self.pausar_solicitado = False
        
        try:
            dados = self.extrair_dados()
            if not dados: return

            for i, info in enumerate(dados):
                if self.pausar_solicitado: break
                self.status_texto.set(f"Item {i+1}/{len(dados)}: {info}")
                
                match_codigo = re.search(r'^(\d+)', info)
                so_codigo = match_codigo.group(1) if match_codigo else info
                
                for p in self.passos:
                    if self.pausar_solicitado: break
                    tipo = p.get('tipo')
                    
                    if tipo == 'clique':
                        sub = p.get('subtipo', 'left').lower()
                        if 'double' in sub: pyautogui.doubleClick(p['x'], p['y'])
                        elif 'right' in sub: pyautogui.rightClick(p['x'], p['y'])
                        else: pyautogui.click(p['x'], p['y'], button='left')
                    
                    elif tipo == 'dado':
                        time.sleep(0.2)
                        pyautogui.hotkey('ctrl', 'a')
                        time.sleep(0.1)
                        pyautogui.press('backspace')
                        time.sleep(0.2)
                        texto = so_codigo if p.get('modo') == 'so_codigo' else info
                        pyautogui.write(str(texto), interval=0.05)
                        time.sleep(0.5)
                    
                    elif tipo == 'tecla':
                        pyautogui.press(p.get('valor', 'enter'))
                    
                    elif tipo == 'atalho':
                        pyautogui.hotkey(*p.get('combo', ['ctrl', 'c']))
                    
                    elif tipo == 'espera':
                        time.sleep(float(p.get('valor', 0.5)))
                    
                    time.sleep(0.6)

            if not self.pausar_solicitado:
                messagebox.showinfo("Fim", "Automação concluída!")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha: {str(e)}")
        finally:
            self.btn_iniciar.config(state="normal")
            self.btn_parar.config(state="disabled")
            self.status_texto.set("Pronto")
            self.root.deiconify()

    def solicitar_parada(self): self.pausar_solicitado = True
    def selecionar_arquivo(self): self.arquivo_dados.set(filedialog.askopenfilename())
    def iniciar_thread(self):
        if not self.arquivo_dados.get() or not self.passos: return
        self.btn_iniciar.config(state="disabled")
        self.btn_parar.config(state="normal")
        self.root.iconify()
        threading.Thread(target=self.rodar_automacao, daemon=True).start()
    
    def mapear_clique(self, subtipo):
        self.root.iconify(); time.sleep(4)
        x, y = pyautogui.position()
        self.passos.append({"tipo": "clique", "subtipo": subtipo, "x": x, "y": y, "desc": f"CLIQUE ({subtipo.upper()}) em ({x}, {y})"})
        self.atualizar_lista(); self.root.deiconify()
        
    def add_passo_dado(self, modo):
        desc = "🔢 COLAR SÓ CÓDIGO" if modo == "so_codigo" else "📄 COLAR COMPLETO"
        self.passos.append({"tipo": "dado", "modo": modo, "desc": desc})
        self.atualizar_lista()
        
    def add_atalho_janela(self):
        win = tk.Toplevel(self.root)
        win.title("Atalho")
        v_ctrl, v_alt, v_shift = tk.BooleanVar(), tk.BooleanVar(), tk.BooleanVar()
        tk.Checkbutton(win, text="CTRL", variable=v_ctrl).pack()
        tk.Checkbutton(win, text="ALT", variable=v_alt).pack()
        tk.Checkbutton(win, text="SHIFT", variable=v_shift).pack()
        ent = tk.Entry(win); ent.pack()
        def conf():
            c = []
            if v_ctrl.get(): c.append('ctrl')
            if v_alt.get(): c.append('alt')
            if v_shift.get(): c.append('shift')
            c.append(ent.get().lower())
            self.passos.append({"tipo": "atalho", "combo": c, "desc": f"ATALHO [{' + '.join(c).upper()}]"})
            self.atualizar_lista(); win.destroy()
        tk.Button(win, text="OK", command=conf).pack()

    def add_tecla(self):
        t = simpledialog.askstring("Tecla", "Ex: enter, tab, f5:")
        if t: self.passos.append({"tipo": "tecla", "valor": t.lower(), "desc": f"TECLA [{t.upper()}]"}); self.atualizar_lista()
        
    def add_espera(self):
        s = simpledialog.askfloat("Espera", "Segundos:")
        if s: self.passos.append({"tipo": "espera", "valor": s, "desc": f"ESPERAR {s}s"}); self.atualizar_lista()

    def atualizar_lista(self):
        self.listbox.delete(0, tk.END)
        for i, p in enumerate(self.passos): self.listbox.insert(tk.END, f"{i+1}. {p.get('desc', 'Ação')}")

    def remover_passo(self):
        idx = self.listbox.curselection()
        if idx: del self.passos[idx[0]]; self.atualizar_lista()

    def mover_cima(self):
        idx = self.listbox.curselection()
        if idx and idx[0] > 0:
            i = idx[0]; self.passos[i], self.passos[i-1] = self.passos[i-1], self.passos[i]
            self.atualizar_lista(); self.listbox.selection_set(i-1)

    def mover_baixo(self):
        idx = self.listbox.curselection()
        if idx and idx[0] < len(self.passos) - 1:
            i = idx[0]; self.passos[i], self.passos[i+1] = self.passos[i+1], self.passos[i]
            self.atualizar_lista(); self.listbox.selection_set(i+1)

    def salvar_receita(self):
        f = filedialog.asksaveasfilename(defaultextension=".json")
        if f: 
            with open(f, 'w') as arq: json.dump(self.passos, arq)

    def carregar_receita(self):
        f = filedialog.askopenfilename(filetypes=[("Arquivos JSON", "*.json")])
        if f: 
            with open(f, 'r') as arq: self.passos = json.load(arq)
            self.atualizar_lista()

if __name__ == "__main__":
    root = tk.Tk()
    
    # Carrega o ícone se ele existir na pasta
    if os.path.exists("robot.ico"):
        root.iconbitmap("robot.ico")
        
    AppAutomacaoMestre(root)
    root.mainloop()