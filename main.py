"""Interface gráfica (Tkinter) do problema do entregador."""

import tkinter as tk
from tkinter import messagebox

from delivery_problem import generate_world, solve

CANVAS_SIZE = 520
COLORS = {
    "normal": "white",
    "obstacle": "black",
    "toll": "gray",
    "agent": "#1e88e5",
    "package": "#fdd835",
    "destination": "#e53935",
    "path": "#43a047",
}


class App:
    def __init__(self, root):
        self.root = root
        self.world = None
        root.title("APS - Entregador em GridWorld")

        controls = tk.Frame(root)
        controls.pack(pady=8)
        tk.Label(controls, text="Dimensão N:").pack(side=tk.LEFT)
        self.size_entry = tk.Entry(controls, width=5)
        self.size_entry.insert(0, "6")
        self.size_entry.pack(side=tk.LEFT, padx=4)
        tk.Button(controls, text="Gerar mundo", command=self.on_generate).pack(side=tk.LEFT, padx=4)
        tk.Button(controls, text="Resolver", command=self.on_solve).pack(side=tk.LEFT, padx=4)

        body = tk.Frame(root)
        body.pack(padx=10, pady=4)
        self.canvas = tk.Canvas(body, width=CANVAS_SIZE, height=CANVAS_SIZE, bg="white")
        self.canvas.pack(side=tk.LEFT, anchor="n")

        side = tk.Frame(body)
        side.pack(side=tk.LEFT, fill=tk.Y, padx=10)
        self.draw_legend(side)
        self.result_text = tk.Text(side, width=36, height=22, wrap="word")
        self.result_text.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.on_generate()

    def draw_legend(self, parent):
        tk.Label(parent, text="Legenda", font=("Arial", 10, "bold")).pack(anchor="w")
        items = [
            ("normal", "Célula normal (custo 1)"),
            ("obstacle", "Obstáculo"),
            ("toll", "Pedágio (custo 1 + 2 = 3)"),
            ("agent", "A - Agente"),
            ("package", "P - Pacote"),
            ("destination", "X - Destino"),
            ("path", "Caminho encontrado"),
        ]
        for color_key, text in items:
            row = tk.Frame(parent)
            row.pack(anchor="w")
            tk.Label(row, width=2, bg=COLORS[color_key], relief="solid", borderwidth=1).pack(side=tk.LEFT)
            tk.Label(row, text=" " + text).pack(side=tk.LEFT)

    def on_generate(self):
        try:
            n = int(self.size_entry.get())
            self.world = generate_world(n)
        except ValueError:
            messagebox.showerror("Dimensão inválida", "Informe um número inteiro maior ou igual a 2.")
            return
        self.draw_world()
        self.show_message(
            f"Mundo {n}x{n} gerado.\n"
            f"Obstáculos: {len(self.world['obstacles'])}\n"
            f"Pedágios: {len(self.world['tolls'])}\n\n"
            "Clique em Resolver."
        )

    def on_solve(self):
        result = solve(self.world)
        self.draw_world()
        if result is None:
            self.show_message("Não existe solução para este mundo.")
            return

        self.draw_path(result["cells"])
        lines = ["Solução encontrada", "", f"Custo total: {result['cost']}", "", "Plano:"]
        for i, (action, cost) in enumerate(zip(result["actions"], result["step_costs"]), start=1):
            lines.append(f"{i}. {action}  (custo {cost})")
        self.show_message("\n".join(lines))

    def show_message(self, text):
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, text)

    def cell_size(self):
        return CANVAS_SIZE / self.world["n"]

    def draw_world(self):
        self.canvas.delete("all")
        size = self.cell_size()
        n = self.world["n"]
        for row in range(n):
            for col in range(n):
                color = COLORS["normal"]
                if (row, col) in self.world["obstacles"]:
                    color = COLORS["obstacle"]
                elif (row, col) in self.world["tolls"]:
                    color = COLORS["toll"]
                x, y = col * size, row * size
                self.canvas.create_rectangle(x, y, x + size, y + size, fill=color, outline="#bbbbbb")
        self.draw_marks()

    def draw_marks(self):
        self.draw_mark(self.world["package"], "P", "package", "rectangle")
        self.draw_mark(self.world["destination"], "X", "destination", None)
        self.draw_mark(self.world["agent"], "A", "agent", "oval")

    def draw_mark(self, cell, letter, color_key, shape):
        size = self.cell_size()
        row, col = cell
        pad = size * 0.15
        x1, y1 = col * size + pad, row * size + pad
        x2, y2 = (col + 1) * size - pad, (row + 1) * size - pad
        if shape == "rectangle":
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=COLORS[color_key])
        elif shape == "oval":
            self.canvas.create_oval(x1, y1, x2, y2, fill=COLORS[color_key])
        text_color = COLORS["destination"] if shape is None else "black"
        font_size = max(6, int(size * (0.5 if shape is None else 0.35)))
        self.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=letter,
                                fill=text_color, font=("Arial", font_size, "bold"))

    def draw_path(self, cells):
        size = self.cell_size()
        points = []
        for row, col in cells:
            points += [col * size + size / 2, row * size + size / 2]
        if len(points) >= 4:
            self.canvas.create_line(*points, fill=COLORS["path"], width=max(2, size / 8))
        self.draw_marks()  # mantém A, P e X visíveis por cima da linha


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
