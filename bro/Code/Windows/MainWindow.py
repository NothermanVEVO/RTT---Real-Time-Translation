import tkinter as tk
from tkinter import ttk
from tkinter import Tk, Menu, END
from PIL import ImageTk
import Code.WindowScreenshot as WindowScreenshot
# import RTT
import RTTQT
import Code.Languages as Languages

class ComboSuggestions(tk.Frame):
    def __init__(self, master, opcoes, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.opcoes = opcoes
        self.lista_visivel = False
        self.clicando_na_lista = False

        # Campo de texto
        self.entry = tk.Entry(self, font=("Segoe UI", 15))
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=2, padx=(0, 2))
        self.entry.bind("<KeyRelease>", self.atualizar_sugestoes)
        self.entry.bind("<FocusOut>", self.ocultar_sugestoes_apos_foco)

        # Botão com a seta ▼
        self.botao = ttk.Button(self, text="▼", width=2, command=self.toggle_lista)
        self.botao.pack(side=tk.LEFT)

        # Frame flutuante para Listbox + Scroll (usando root como pai)
        self.popup_frame = tk.Frame(self.winfo_toplevel(), bd=1, relief=tk.SOLID, bg="white")

        # Scrollbar
        self.scrollbar = tk.Scrollbar(self.popup_frame, orient=tk.VERTICAL)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Listbox
        self.listbox = tk.Listbox(
            self.popup_frame,
            height=6,
            yscrollcommand=self.scrollbar.set,
            activestyle="none",
            font=("Segoe UI", 15),
            highlightthickness=0,
            relief=tk.FLAT,
            selectbackground="#0078D7",
            selectforeground="white"
        )
        self.scrollbar.config(command=self.listbox.yview)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.listbox.configure(takefocus=0)
        self.listbox.bind("<<ListboxSelect>>", self.selecionar_sugestao)
        self.listbox.bind("<FocusOut>", lambda e: self.popup_frame.place_forget())
        self.listbox.bind("<FocusIn>", lambda e: self.entry.focus_set())
        self.listbox.bind("<Motion>", self.highlight_hover)

    def toggle_lista(self):
        if self.lista_visivel:
            self.popup_frame.place_forget()
            self.lista_visivel = False
        else:
            self.mostrar_todos()
            self.lista_visivel = True
            self.entry.focus_set()

    def atualizar_sugestoes(self, event=None):
        texto = self.entry.get().lower()
        if texto == "":
            self.popup_frame.place_forget()
            self.lista_visivel = False
            return

        sugeridas = [item for item in self.opcoes if texto in item.lower()]
        self._mostrar_lista(sugeridas)

    def mostrar_todos(self):
        self._mostrar_lista(self.opcoes)

    def _mostrar_lista(self, lista):
        if not lista:
            self.popup_frame.place_forget()
            self.lista_visivel = False
            return

        self.listbox.delete(0, tk.END)
        for item in lista:
            self.listbox.insert(tk.END, item)

        # Corrige a posição: calcula posição relativa ao toplevel (root)
        x = self.entry.winfo_rootx() - self.winfo_toplevel().winfo_rootx()
        y = self.entry.winfo_rooty() - self.winfo_toplevel().winfo_rooty() + self.entry.winfo_height()
        largura = self.entry.winfo_width() + self.botao.winfo_width()

        self.popup_frame.place(x=x, y=y, width=largura)

        self.popup_frame.lift()
        self.lista_visivel = True

    def selecionar_sugestao(self, event):
        if self.listbox.curselection():
            valor = self.listbox.get(self.listbox.curselection()[0])
            self.entry.delete(0, tk.END)
            self.entry.insert(0, valor)
            self.listbox.place_forget()
            self.lista_visivel = False
            self.entry.focus_set()

    def ocultar_sugestoes_apos_foco(self, event=None):
        self.after(200, self._checar_foco_com_delay)

    def _checar_foco_com_delay(self):
        foco = self.focus_get()
        if not self.clicando_na_lista and foco not in [self.entry, self.botao]:
            self.popup_frame.place_forget()
            self.lista_visivel = False

    def _checar_foco(self):
        foco = self.focus_get()
        if foco not in [self.listbox, self.entry]:
            self.popup_frame.place_forget()
            self.lista_visivel = False

    def highlight_hover(self, event):
        widget = event.widget
        index = widget.nearest(event.y)
        widget.selection_clear(0, tk.END)
        widget.selection_set(index)

class ImagesGrid(tk.Frame):
    def __init__(self, master, dados, largura_item=200, altura_item=140, altura_canvas=300, bg="#e4e6ed", *args, **kwargs):
        super().__init__(master, bg=bg, *args, **kwargs)
        self.bg = bg
        self.dados = dados
        self.largura_item = largura_item
        self.altura_item = altura_item
        self.itens = []
        self.selecionado = None
        self.imagens_ref = []  # Referências às imagens
        self.objetos = []  # (imagem, texto)

        # Canvas com rolagem vertical
        self.canvas = tk.Canvas(self, borderwidth=0, height=altura_canvas, bg=bg)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="x", expand=True)

        # Frame interno
        self.frame_interno = tk.Frame(self.canvas, bg=bg)
        self.frame_interno_id = self.canvas.create_window((0, 0), window=self.frame_interno, anchor="nw")

        self.frame_interno.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.adicionar_dados(dados)

    def adicionar_dados(self, novos_dados):
        # Limpa dados anteriores
        for item in self.itens:
            item.destroy()
        self.itens.clear()
        self.objetos.clear()
        self.imagens_ref.clear()
        self.selecionado = None

        self.dados = novos_dados

        for idx, (img_obj, hwnd, texto) in enumerate(novos_dados):
            frame_item = tk.Frame(self.frame_interno, width=self.largura_item, height=self.altura_item, relief="flat", bd=2)
            frame_item.pack_propagate(False)

            imagem_redimensionada = img_obj.resize((192, 108))
            foto = ImageTk.PhotoImage(imagem_redimensionada)
            self.imagens_ref.append(foto)  # Referência

            img_label = tk.Label(frame_item, image=foto)
            img_label.image = foto
            img_label.pack()

            texto_label = tk.Label(frame_item, text=texto, wraplength=self.largura_item - 10, justify="center")
            texto_label.pack()

            frame_item.bind("<Button-1>", lambda e, idx=idx: self.selecionar_item(idx))
            img_label.bind("<Button-1>", lambda e, idx=idx: self.selecionar_item(idx))
            texto_label.bind("<Button-1>", lambda e, idx=idx: self.selecionar_item(idx))

            self.itens.append(frame_item)
            self.objetos.append((img_obj, hwnd, texto))

        self.reorganizar()

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        largura = event.width
        self.canvas.itemconfig(self.frame_interno_id, width=largura)
        self.reorganizar()

    def _on_mousewheel(self, event):
        if event.num == 5 or event.delta == -120:
            self.canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta == 120:
            self.canvas.yview_scroll(-1, "units")

    def reorganizar(self):
        for item in self.itens:
            item.grid_forget()

        largura_total = self.canvas.winfo_width()
        if largura_total <= 1:
            self.after(100, self.reorganizar)
            return

        colunas = max(1, largura_total // self.largura_item)
        for i, item in enumerate(self.itens):
            linha = i // colunas
            coluna = i % colunas
            item.grid(row=linha, column=coluna, padx=5, pady=5, sticky="n")

    def selecionar_item(self, idx):
        if self.selecionado is not None:
            self.itens[self.selecionado].config(relief="flat", bd=2)
        self.selecionado = idx
        self.itens[idx].config(relief="solid", bd=3, highlightbackground="blue", highlightcolor="blue")

    def obter_item_selecionado(self):
        if self.selecionado is not None:
            return self.objetos[self.selecionado]#TODO, self.objetos.index(self.selecionado)
        return None

windows = []

_window_width = 800
_window_height = 600

notebook = None
grade1 = None
grade2 = None
_translate_from : ComboSuggestions
_translate_to : ComboSuggestions

is_on : bool = False
is_paused : bool = False

_options = Languages.get_all_language_names()

is_on_select_tab = True

def create():
    global notebook, grade1, grade2, _translate_from, _translate_to, _options

    root = Tk()
    root.wm_title("RTT - Real Time Translation")
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    pos_x = (screen_width - _window_width) // 2
    pos_y = (screen_height - _window_height) // 2
    root.geometry(f"{_window_width}x{_window_height}+{pos_x}+{pos_y}")

    menu = Menu(root)
    root.config(menu=menu)
    configmenu = Menu(menu)
    menu.add_cascade(label='Configurações', menu=configmenu)
    modesmenu = Menu(menu)
    menu.add_cascade(label='Modos', menu=modesmenu)
    modesmenu.add_command(label="RTT")
    modesmenu.add_command(label="Translation")
    shortcutsmenu = Menu(menu)
    menu.add_cascade(label="Atalhos", menu=shortcutsmenu)
    helpmenu = Menu(menu)
    menu.add_cascade(label='Ajuda', menu=helpmenu)
    helpmenu.add_command(label='Sobre')

    conteiner = tk.Frame(root, height=60)
    conteiner.pack(fill=tk.X, padx=10, pady=10)
    conteiner.pack_propagate(False)

    _translate_from = ComboSuggestions(conteiner, _options)
    _translate_from.grid(row=0, column=0, sticky="ew", padx=(0, 5))

    switch = ttk.Button(conteiner, text="↔", width=5, command=switch_languages)
    switch.grid(row=0, column=1, padx=5)

    _translate_to = ComboSuggestions(conteiner, _options)
    _translate_to.grid(row=0, column=2, sticky="ew", padx=(5, 0))

    conteiner.grid_columnconfigure(0, weight=1)
    conteiner.grid_columnconfigure(1, weight=0)
    conteiner.grid_columnconfigure(2, weight=1)

    # Notebook (abas)
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    notebook.bind("<<NotebookTabChanged>>", on_tab_changed)
    
    # === Aba 1: Selecionar Janela ===
    aba1 = tk.Frame(notebook)
    notebook.add(aba1, text="Selecionar Janela")
    
    # Container para seleção
    select_conteiner = tk.Frame(aba1, height=60)
    select_conteiner.pack(fill=tk.X, padx=10, pady=10)
    
    select_window = tk.Label(select_conteiner, text="Selecionar Janela:", font=("Segoe UI", 25, "bold"))
    select_window.grid(row=0, column=0, sticky="w", padx=(0, 5))
    
    reload = ttk.Button(select_conteiner, text="R", width=10, command=reload_windows)
    reload.grid(row=0, column=1, sticky="e", padx=(5, 0), ipadx=10, ipady=5)
    
    select_conteiner.grid_columnconfigure(0, weight=0)
    select_conteiner.grid_columnconfigure(1, weight=1)
    
    # Grade de imagens na aba 1
    grade1 = ImagesGrid(aba1, [])
    grade1.pack(fill=tk.X, padx=10, pady=10)
    
    # === Aba 2: Tela Cheia ===
    aba2 = tk.Frame(notebook)
    notebook.add(aba2, text="Tela Cheia")

    # Container para seleção
    full_conteiner = tk.Frame(aba2, height=60)
    full_conteiner.pack(fill=tk.X, padx=10, pady=10)
    
    select_window = tk.Label(full_conteiner, text="Tela Cheia:", font=("Segoe UI", 25, "bold"))
    select_window.grid(row=0, column=0, sticky="w", padx=(0, 5))
    
    full_conteiner.grid_columnconfigure(0, weight=0)
    full_conteiner.grid_columnconfigure(1, weight=1)
    
    # Grade de imagens na aba 2
    grade2 = ImagesGrid(aba2, [])
    grade2.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    bottom_conteiner = tk.Frame(root, height=60)
    bottom_conteiner.pack(fill=tk.X, side="bottom", padx=10, pady=10)

    apply = ttk.Button(bottom_conteiner, text="Aplicar", width=10, command=apply_window)
    apply.grid(row=0, column=1, sticky="w", padx=(5, 0), ipadx=10, ipady=5)

    pause = ttk.Button(bottom_conteiner, text="Pausar", width=10, command=pause_app)
    pause.grid(row=0, column=2, sticky="e", padx=(5, 0), ipadx=10, ipady=5)

    onNoff = ttk.Button(bottom_conteiner, text="ON/OFF", width=10, command=turn_on_off)
    onNoff.grid(row=0, column=3, sticky="e", padx=(5, 0), ipadx=10, ipady=5)

    bottom_conteiner.grid_columnconfigure(0, weight=0)
    bottom_conteiner.grid_columnconfigure(1, weight=1)
    bottom_conteiner.grid_columnconfigure(2, weight=1)

    root.mainloop()

def on_tab_changed(event):
    global notebook, grade2, is_on_select_tab
    aba_selecionada = event.widget.select()
    indice = notebook.index(aba_selecionada)
    if indice == 0: # SELECT TAB
        is_on_select_tab = True
        reload_windows()
    elif indice == 1: # FULL SCREEN TAB
        is_on_select_tab = False
        screenshot = WindowScreenshot.getFullScreenshot()
        if screenshot:
            grade2.adicionar_dados([(screenshot, -1, "Tela Cheia")])
        else:
            print("ERRO AO TIRAR SCREENSHOT") #TODO

def switch_languages():
    global _translate_from, _translate_to
    text_from = _translate_from.entry.get()
    text_to = _translate_to.entry.get()

    _translate_from.entry.delete(0, END)
    _translate_from.entry.insert(0, text_to)

    _translate_to.entry.delete(0, END)
    _translate_to.entry.insert(0, text_from)

def reload_windows():
    global windows, grade1
    windows.clear()
    for hwnd, title in WindowScreenshot.getAllVisibleWindows():
        # print("title: ", title, " | hwnd:", hwnd)
        if title == RTTQT.FULLSCREEN:
            continue
        result = WindowScreenshot.getWindowScreenshot(hwnd)
        if result and result[0]:
            windows.append((result[0], hwnd, title))
    grade1.adicionar_dados(windows)

def apply_window():
    if RTTQT.exists():
        if not is_languages_valid():#TODO
            return
        RTTQT.quit()
        if is_on_select_tab:
            hwnd = get_selected_window()
            if not hwnd:
                return
            result = WindowScreenshot.getWindowScreenshot(hwnd)
            RTTQT.create(hwnd, result[1], result[2], result[3], result[4], 1, _translate_from.entry.get(), _translate_to.entry.get(), not is_on_select_tab)
        else:
            image = WindowScreenshot.getFullScreenshot()
            RTTQT.create(-1, 0, 0, image.size[0], image.size[1], 1, _translate_from.entry.get(), _translate_to.entry.get(), not is_on_select_tab)        
    pass

def pause_app():
    pass

def turn_on_off():
    global _translate_from, _translate_to, is_on_select_tab
    if RTTQT.exists():
        RTTQT.quit()
    else:
        if not is_languages_valid():#TODO
            return
        if is_on_select_tab:
            hwnd = get_selected_window()
            if not hwnd:
                return
            result = WindowScreenshot.getWindowScreenshot(hwnd)
            RTTQT.create(hwnd, result[1], result[2], result[3], result[4], 1, _translate_from.entry.get(), _translate_to.entry.get(), not is_on_select_tab)
        else:
            image = WindowScreenshot.getFullScreenshot()
            RTTQT.create(-1, 0, 0, image.size[0], image.size[1], 1, _translate_from.entry.get(), _translate_to.entry.get(), not is_on_select_tab)       

def is_languages_valid() -> bool:
    global _translate_from, _translate_to, _options
    if not _translate_to.entry.get() in _options or not _translate_from.entry.get() in _options:
        return False
    if _translate_to.entry.get() == _translate_from.entry.get():
        return False
    return True

def get_selected_window_name():
    global grade1
    item = grade1.obter_item_selecionado()
    if item:
        return item[2]
    return None

def get_selected_window():
    global grade1
    item = grade1.obter_item_selecionado()
    if item:
        return item[1]
    return None

create()
