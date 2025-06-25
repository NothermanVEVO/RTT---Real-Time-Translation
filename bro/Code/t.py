import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.title("Exemplo de Abas")
root.geometry("400x300")

# Criar o Notebook (o "JTabbedPane")
notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill='both')

# Criar os frames (conteúdo de cada aba)
aba1 = tk.Frame(notebook, bg='lightblue')
aba2 = tk.Frame(notebook, bg='lightgreen')

# Adicionar as abas ao Notebook
notebook.add(aba1, text='Aba 1')
notebook.add(aba2, text='Aba 2')

# Adicionar widgets dentro das abas
tk.Label(aba1, text="Conteúdo da Aba 1").pack(pady=20)
tk.Label(aba2, text="Conteúdo da Aba 2").pack(pady=20)

root.mainloop()
