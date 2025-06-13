import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import random
from collections import defaultdict
import copy
import threading
import time
import pandas as pd

TOTAL_CARDS = 108  # Total de cartas en un mazo de UNO

class UNOCard:
    def __init__(self, color, value, card_type):
        self.color = color
        self.value = value
        self.card_type = card_type

    def __repr__(self):
        return f"{self.color}{self.value}" if self.color else str(self.value)

    def to_display_string(self):
        """Convierte carta a string legible"""
        color_names = {'a': 'Azul', 'v': 'Verde', 'r': 'Rojo', 'am': 'Amarillo'}
        special_names = {'r2': 'Roba 2', 'rev': 'Reversa', 's': 'Salta', 'c': 'Comodín', 'r4': 'Roba 4'}
        if self.color:
            if isinstance(self.value, int):
                return f"{color_names[self.color]} {self.value}"
            else:
                return f"{color_names[self.color]} {special_names.get(self.value, self.value)}"
        else:
            return special_names.get(self.value, self.value)

    def get_color_hex(self):
        """Obtiene color hexadecimal para la interfaz"""
        color_map = {
            'a': '#0066CC',  # Azul
            'v': '#00AA00',  # Verde
            'r': '#CC0000',  # Rojo
            'am': '#FFAA00'  # Amarillo
        }
        return color_map.get(self.color, '#333333')


class UNODeck:
    def __init__(self):
        self.cards = []
        self.discarded = []
        self.create_deck()
        self.shuffle()

    def create_deck(self):
        """Crea el mazo completo según especificaciones del PDF"""
        colors = ['a', 'v', 'r', 'am']
        # Cartas numéricas (76 total)
        for color in colors:
            # Un 0 por color
            self.cards.append(UNOCard(color, 0, 'number'))
            # Dos de cada número 1-9 por color
            for num in range(1, 10):
                self.cards.append(UNOCard(color, num, 'number'))
                self.cards.append(UNOCard(color, num, 'number'))
        # Cartas especiales (24 total)
        specials = ['r2', 'rev', 's']
        for color in colors:
            for special in specials:
                self.cards.append(UNOCard(color, special, 'special'))
                self.cards.append(UNOCard(color, special, 'special'))
        # Cartas comodín (8 total)
        wildcards = ['c', 'r4']
        for wildcard in wildcards:
            for _ in range(4):
                self.cards.append(UNOCard(None, wildcard, 'wildcard'))

    def shuffle(self):
        random.shuffle(self.cards)

    def deal_card(self):
        if not self.cards:
            self.reshuffle_from_discard()
        return self.cards.pop() if self.cards else None

    def reshuffle_from_discard(self):
        if len(self.discarded) > 1:
            # Mantener la carta superior, barajar el resto
            top_card = self.discarded.pop()
            self.cards = self.discarded[:]
            self.discarded = [top_card]
            self.shuffle()


class UNOIntelligentGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎮 UNO - Agente Inteligente | Tecnológico de Monterrey")
        self.root.geometry("1400x900")
        self.root.configure(bg='#2C3E50')
        # Variables del juego
        self.deck = UNODeck()
        self.current_card = None
        self.current_player = 0  # 0=Jugador1, 1=Máquina, 2=Jugador2
        self.game_direction = 1
        self.game_started = False
        # Manos de jugadores
        self.player_hands = [[], [], []]  # [Jugador1, Máquina, Jugador2]
        self.player_names = ['Jugador 1', 'Máquina', 'Jugador 2']
        # Sistema de probabilidades
        self.init_probability_system()
        # Variables de interfaz
        self.selected_card_index = None
        self.animation_running = False
        # Crear interfaz
        self.create_interface()
        # Iniciar juego automáticamente
        self.start_new_game()
        self.jugada_stats = []  # Lista para registrar jugadas
        self.uno_declarado = {0: False, 1: False, 2: False}  # Estado de UNO por jugador

    def init_probability_system(self):
        self.colors = ['a', 'v', 'r', 'am']
        self.numbers = list(range(10))
        self.special_cards = ['r2', 'rev', 's']
        self.wildcards = ['c', 'r4']

        # Contadores de cartas restantes (inicializados con valores iniciales)
        self.card_counters = {
            'colors': {'a': 25, 'v': 25, 'r': 25, 'am': 25},  # Cartas por color
            'numbers': {i: 8 for i in range(1, 10)},  # Números 1-9
            'number_0': 4,  # Número 0
            'specials': {'r2': 8, 'rev': 8, 's': 8},  # Especiales
            'wildcards': {'c': 4, 'r4': 4}  # Comodines
        }

        # Probabilidades iniciales para jugadores humanos
        self.probabilities = {
            0: {  # Jugador 1
                'colors': {color: 25 / 108 for color in self.colors},
                'numbers': {num: 8 / 108 if num != 0 else 4 / 108 for num in self.numbers},
                'specials': {card: 8 / 108 for card in self.special_cards},
                'wildcards': {card: 4 / 108 for card in self.wildcards}
            },
            2: {  # Jugador 2
                'colors': {color: 25 / 108 for color in self.colors},
                'numbers': {num: 8 / 108 if num != 0 else 4 / 108 for num in self.numbers},
                'specials': {card: 8 / 108 for card in self.special_cards},
                'wildcards': {card: 4 / 108 for card in self.wildcards}
            }
        }

    def create_interface(self):
        """Crea la interfaz gráfica completa"""
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#2C3E50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        # Panel superior - Información del juego
        self.create_game_info_panel(main_frame)
        # Panel central - Mesa de juego
        self.create_game_table_panel(main_frame)
        # Panel derecho - Estadísticas y probabilidades
        self.create_stats_panel(main_frame)
        # Panel inferior - Controles
        self.create_controls_panel(main_frame)

    def create_game_info_panel(self, parent):
        """Panel de información del juego"""
        info_frame = tk.Frame(parent, bg='#34495E', relief=tk.RAISED, bd=2)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        # Título
        title_label = tk.Label(info_frame,
                               text="🎮 UNO - AGENTE INTELIGENTE",
                               font=('Arial', 16, 'bold'),
                               bg='#34495E', fg='white')
        title_label.pack(pady=5)
        # Estado del juego
        game_state_frame = tk.Frame(info_frame, bg='#34495E')
        game_state_frame.pack(fill=tk.X, padx=10, pady=5)
        self.current_player_label = tk.Label(game_state_frame,
                                             text="Turno: Jugador 1",
                                             font=('Arial', 12, 'bold'),
                                             bg='#34495E', fg='#E74C3C')
        self.current_player_label.pack(side=tk.LEFT)
        self.direction_label = tk.Label(game_state_frame,
                                       text="Dirección: →",
                                       font=('Arial', 12),
                                       bg='#34495E', fg='white')
        self.direction_label.pack(side=tk.RIGHT)

    def create_game_table_panel(self, parent):
        """Panel central de la mesa de juego"""
        table_frame = tk.Frame(parent, bg='#2C3E50')
        table_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # Jugador 2 (arriba)
        self.create_player_area(table_frame, 2, 'top')
        # Área central - Carta actual y mazo
        self.create_center_area(table_frame)
        # Jugador 1 (abajo)
        self.create_player_area(table_frame, 0, 'bottom')
        # Máquina (izquierda)
        self.create_machine_area(table_frame)

    def create_player_area(self, parent, player_id, position):
        """Crea el área de un jugador"""
        if position == 'top':
            player_frame = tk.Frame(parent, bg='#34495E', relief=tk.RAISED, bd=2)
            player_frame.pack(fill=tk.X, pady=(0, 10))
        else:  # bottom
            player_frame = tk.Frame(parent, bg='#34495E', relief=tk.RAISED, bd=2)
            player_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        # Información del jugador
        info_frame = tk.Frame(player_frame, bg='#34495E')
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        player_label = tk.Label(info_frame,
                               text=f"{self.player_names[player_id]}",
                               font=('Arial', 12, 'bold'),
                               bg='#34495E', fg='white')
        player_label.pack(side=tk.LEFT)
        card_count_label = tk.Label(info_frame,
                                   text="Cartas: 7",
                                   font=('Arial', 10),
                                   bg='#34495E', fg='#BDC3C7')
        card_count_label.pack(side=tk.RIGHT)
        # Frame con scroll horizontal para las cartas
        cards_container = tk.Frame(player_frame, bg='#34495E')
        cards_container.pack(fill=tk.X, padx=10, pady=(0, 10))
        # Canvas y scrollbar para scroll horizontal
        canvas = tk.Canvas(cards_container, bg='#34495E', highlightthickness=0, height=80)
        scrollbar = tk.Scrollbar(cards_container, orient=tk.HORIZONTAL, command=canvas.xview)
        cards_frame = tk.Frame(canvas, bg='#34495E')
        canvas.configure(xscrollcommand=scrollbar.set)
        canvas.pack(fill=tk.X)
        scrollbar.pack(fill=tk.X)
        # Crear ventana en el canvas
        canvas_window = canvas.create_window((0, 0), window=cards_frame, anchor='nw')
        # Función para actualizar el scroll
        def configure_scroll(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Ajustar altura del canvas al contenido
            canvas.configure(height=cards_frame.winfo_reqheight())
        cards_frame.bind("<Configure>", configure_scroll)
        # Función para redimensionar la ventana del canvas
        def configure_canvas_window(event):
            canvas_width = event.width
            canvas.itemconfig(canvas_window, width=canvas_width)
        canvas.bind("<Configure>", configure_canvas_window)
        # Guardar referencias
        if not hasattr(self, 'player_labels'):
            self.player_labels = {}
            self.player_card_frames = {}
            self.player_card_count_labels = {}
            self.player_canvases = {}
        self.player_card_frames[player_id] = cards_frame
        self.player_card_count_labels[player_id] = card_count_label
        self.player_canvases[player_id] = canvas

    def create_machine_area(self, parent):
        """Crea el área de la máquina (lado izquierdo)"""
        machine_frame = tk.Frame(parent, bg='#34495E', relief=tk.RAISED, bd=2)
        machine_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        # Encabezado
        header = tk.Label(machine_frame,
                         text="🤖 MÁQUINA",
                         font=('Arial', 12, 'bold'),
                         bg='#34495E', fg='#3498DB')
        header.pack(pady=10)
        # Contador de cartas
        self.machine_card_count = tk.Label(machine_frame,
                                          text="Cartas: 7",
                                          font=('Arial', 10),
                                          bg='#34495E', fg='#BDC3C7')
        self.machine_card_count.pack()
        # Frame con scroll para cartas de la máquina
        cards_container = tk.Frame(machine_frame, bg='#34495E')
        cards_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        # Canvas y scrollbar vertical para la máquina
        canvas = tk.Canvas(cards_container, bg='#34495E', highlightthickness=0, width=150)
        scrollbar = tk.Scrollbar(cards_container, orient=tk.VERTICAL, command=canvas.yview)
        machine_cards_frame = tk.Frame(canvas, bg='#34495E')
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # Crear ventana en el canvas
        canvas_window = canvas.create_window((0, 0), window=machine_cards_frame, anchor='nw')
        # Función para actualizar el scroll vertical
        def configure_machine_scroll(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
        machine_cards_frame.bind("<Configure>", configure_machine_scroll)
        # Función para redimensionar
        def configure_machine_canvas_window(event):
            canvas_height = event.height
            canvas.itemconfig(canvas_window, height=canvas_height)
        canvas.bind("<Configure>", configure_machine_canvas_window)
        # Área de decisión de IA
        decision_frame = tk.LabelFrame(machine_frame,
                                      text="Decisión IA",
                                      font=('Arial', 10, 'bold'),
                                      bg='#34495E', fg='white')
        decision_frame.pack(fill=tk.X, padx=10, pady=10)
        self.ai_decision_text = tk.Text(decision_frame,
                                       height=6, width=20,
                                       font=('Arial', 8),
                                       bg='#2C3E50', fg='white',
                                       wrap=tk.WORD)
        self.ai_decision_text.pack(fill=tk.BOTH, expand=True)
        # Guardar referencias
        self.machine_cards_frame = machine_cards_frame
        self.player_card_frames[1] = machine_cards_frame
        self.player_card_count_labels[1] = self.machine_card_count
        if not hasattr(self, 'player_canvases'):
            self.player_canvases = {}
        self.player_canvases[1] = canvas

    def create_center_area(self, parent):
        """Crea el área central con carta actual"""
        center_frame = tk.Frame(parent, bg='#2C3E50')
        center_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        # Frame para carta actual
        current_card_frame = tk.Frame(center_frame, bg='#2C3E50')
        current_card_frame.pack(expand=True)
        tk.Label(current_card_frame,
                text="CARTA ACTUAL",
                font=('Arial', 12, 'bold'),
                bg='#2C3E50', fg='white').pack()
        self.current_card_display = tk.Label(current_card_frame,
                                           text="",
                                           font=('Arial', 14, 'bold'),
                                           bg='white',
                                           relief=tk.RAISED,
                                           bd=3,
                                           width=15, height=3)
        self.current_card_display.pack(pady=10)
        # Botón de mazo
        deck_frame = tk.Frame(center_frame, bg='#2C3E50')
        deck_frame.pack()
        tk.Label(deck_frame,
                text="MAZO",
                font=('Arial', 10),
                bg='#2C3E50', fg='white').pack()
        self.deck_button = tk.Button(deck_frame,
                                    text="🂠\nROBAR",
                                    font=('Arial', 12, 'bold'),
                                    bg='#7F8C8D',
                                    fg='white',
                                    width=8, height=3,
                                    command=self.draw_card)
        self.deck_button.pack(pady=5)

    def create_stats_panel(self, parent):
        """Panel de estadísticas y probabilidades"""
        stats_frame = tk.Frame(parent, bg='#34495E', relief=tk.RAISED, bd=2)
        stats_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        # Título
        tk.Label(stats_frame,
                text="📊 ESTADÍSTICAS EN TIEMPO REAL",
                font=('Arial', 12, 'bold'),
                bg='#34495E', fg='white').pack(pady=10)
        # Notebook para pestañas
        notebook = ttk.Notebook(stats_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        # Pestaña de probabilidades
        prob_frame = tk.Frame(notebook, bg='#2C3E50')
        notebook.add(prob_frame, text="Probabilidades")
        self.probability_text = scrolledtext.ScrolledText(prob_frame,
                                                         width=30, height=20,
                                                         font=('Consolas', 9),
                                                         bg='#2C3E50', fg='white')
        self.probability_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        # Pestaña de contadores
        counters_frame = tk.Frame(notebook, bg='#2C3E50')
        notebook.add(counters_frame, text="Contadores")
        self.counters_text = scrolledtext.ScrolledText(counters_frame,
                                                      width=30, height=20,
                                                      font=('Consolas', 9),
                                                      bg='#2C3E50', fg='white')
        self.counters_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        # Pestaña de log
        log_frame = tk.Frame(notebook, bg='#2C3E50')
        notebook.add(log_frame, text="Log del Juego")
        self.game_log_text = scrolledtext.ScrolledText(log_frame,
                                                      width=30, height=20,
                                                      font=('Consolas', 8),
                                                      bg='#2C3E50', fg='white')
        self.game_log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def create_controls_panel(self, parent):
        """Panel de controles"""
        controls_frame = tk.Frame(parent, bg='#34495E', relief=tk.RAISED, bd=2)
        controls_frame.pack(fill=tk.X, pady=(10, 0))
        # Botones de control
        btn_frame = tk.Frame(controls_frame, bg='#34495E')
        btn_frame.pack(pady=10)
        self.new_game_btn = tk.Button(btn_frame,
                                     text="🎮 Nuevo Juego",
                                     font=('Arial', 10, 'bold'),
                                     bg='#27AE60', fg='white',
                                     command=self.start_new_game)
        self.new_game_btn.pack(side=tk.LEFT, padx=5)
        self.play_card_btn = tk.Button(btn_frame,
                                      text="🎯 Jugar Carta",
                                      font=('Arial', 10, 'bold'),
                                      bg='#3498DB', fg='white',
                                      command=self.play_selected_card,
                                      state=tk.DISABLED)
        self.play_card_btn.pack(side=tk.LEFT, padx=5)
        self.uno_btn = tk.Button(btn_frame,
                               text="🔔 UNO!",
                               font=('Arial', 10, 'bold'),
                               bg='#E74C3C', fg='white',
                               command=self.declare_uno)
        self.uno_btn.pack(side=tk.LEFT, padx=5)
        # Estado de selección
        self.selection_label = tk.Label(controls_frame,
                                       text="Selecciona una carta para jugar",
                                       font=('Arial', 10),
                                       bg='#34495E', fg='#BDC3C7')
        self.selection_label.pack(pady=5)

    def start_new_game(self):
        """Inicia un nuevo juego"""
        # Reiniciar variables
        self.deck = UNODeck()
        self.current_player = 0
        self.game_direction = 1
        self.selected_card_index = None
        self.game_started = True
        # Reiniciar probabilidades
        self.init_probability_system()
        # Repartir cartas
        self.deal_initial_cards()
        # Establecer carta inicial
        self.set_initial_card()
        # Actualizar interfaz
        self.update_all_displays()
        self.add_to_log("🎮 NUEVO JUEGO INICIADO")
        self.add_to_log(f"Carta inicial: {self.current_card.to_display_string()}")
        self.add_to_log("Orden: Jugador 1 → Máquina → Jugador 2")
        # Elimina o comenta la siguiente línea:
        # self.update_machine_hand_from_probabilities()
        self.update_statistics()

    def deal_initial_cards(self):
        """Reparta las cartas iniciales"""
        # Limpiar manos
        self.player_hands = [[], [], []]
        # Repartir 7 cartas a cada jugador
        for _ in range(7):
            for player in range(3):
                card = self.deck.deal_card()
                if card:
                    self.player_hands[player].append(card)
                    # Actualizar contadores globales para todos los jugadores
                    self.update_card_counters_remove(card)
    def set_initial_card(self):
        """Establece la carta inicial del juego"""
        while True:
            card = self.deck.deal_card()
            if card and card.card_type != 'wildcard':  # No empezar con comodín
                self.current_card = card
                self.deck.discarded.append(card)
                break

    def update_card_counters_remove(self, card):
        """Actualiza los contadores globales al remover una carta"""
        if card.card_type == 'number':
            if card.value == 0:
                self.card_counters['number_0'] = max(0, self.card_counters['number_0'] - 1)
            else:
                self.card_counters['numbers'][card.value] = max(0, self.card_counters['numbers'].get(card.value, 0) - 1)
            if card.color:
                self.card_counters['colors'][card.color] = max(0, self.card_counters['colors'].get(card.color, 0) - 1)
        elif card.card_type == 'special':
            self.card_counters['specials'][card.value] = max(0, self.card_counters['specials'].get(card.value, 0) - 1)
            if card.color:
                self.card_counters['colors'][card.color] = max(0, self.card_counters['colors'].get(card.color, 0) - 1)
        elif card.card_type == 'wildcard':
            self.card_counters['wildcards'][card.value] = max(0, self.card_counters['wildcards'].get(card.value, 0) - 1)
    
    def get_total_remaining_cards(self):
        """Calcula cuántas cartas quedan en juego (mazo + manos)"""
        return (
            sum(self.card_counters['colors'].values()) +
            self.card_counters['number_0'] +
            sum(self.card_counters['numbers'].values()) +
            sum(self.card_counters['specials'].values()) +
            sum(self.card_counters['wildcards'].values())
        )

    def create_card_button(self, parent, card, index, player_id):
        """Crea un widget para una carta (solo se ven las de la máquina y del jugador actual)"""
        card_text = card.to_display_string()
        color = card.get_color_hex()
        card_count = len(self.player_hands[player_id])
        # Configuración dinámica de tamaño
        if card_count <= 7:
            width, height = 12, 2
            font_size = 8
        elif card_count <= 10:
            width, height = 10, 2
            font_size = 7
        elif card_count <= 15:
            width, height = 8, 2
            font_size = 6
        else:
            width, height = 6, 1
            font_size = 6
        if player_id == 1:
            # Máquina: mostrar carta real
            btn = tk.Label(parent,
                           text=card_text,
                           font=('Arial', font_size, 'bold'),
                           bg=color,
                           fg='white',
                           width=width, height=height,
                           relief=tk.RAISED, bd=2)
        elif player_id == self.current_player:
            # Jugador actual: mostrar carta real y hacer clickeable
            btn = tk.Label(parent,
                           text=card_text,
                           font=('Arial', font_size, 'bold'),
                           bg=color,
                           fg='white',
                           width=width, height=height,
                           relief=tk.RAISED, bd=2)
            btn.bind('<Button-1>', lambda e, idx=index, pid=player_id: self.select_card(idx, pid))
        else:
            # Jugador humano que NO está en turno: mostrar carta oculta
            btn = tk.Label(parent,
                           text='🂠',
                           font=('Arial', font_size, 'bold'),
                           bg='#7F8C8D',
                           fg='white',
                           width=width, height=height,
                           relief=tk.RAISED, bd=2)
        return btn

    def select_card(self, index, player_id):
        """Selecciona una carta para jugar"""
        if player_id != self.current_player or player_id == 1:
            return
        self.selected_card_index = index
        card = self.player_hands[player_id][index]
        # Verificar si es válida
        if self.is_valid_play(card):
            self.selection_label.config(text=f"Carta seleccionada: {card.to_display_string()}")
            self.play_card_btn.config(state=tk.NORMAL)
        else:
            self.selection_label.config(text=f"Carta inválida: {card.to_display_string()}")
            self.play_card_btn.config(state=tk.DISABLED)

    def is_valid_play(self, card):
        """Verifica si una carta es válida para jugar"""
        if card.card_type == 'wildcard':
            return True
        if card.color == self.current_card.color:
            return True
        if (isinstance(card.value, int) and isinstance(self.current_card.value, int) and 
            card.value == self.current_card.value):
            return True
        if card.value == self.current_card.value:
            return True
        return False

    def play_selected_card(self):
        """Juega la carta seleccionada"""
        if (self.selected_card_index is None or 
            self.current_player == 1 or 
            self.selected_card_index >= len(self.player_hands[self.current_player])):
            return
        player_id = self.current_player
        card = self.player_hands[player_id][self.selected_card_index]
        if self.is_valid_play(card):
            # Remover carta de la mano
            self.player_hands[player_id].pop(self.selected_card_index)
            # Jugar carta
            self.play_card(player_id, card)
            # Limpiar selección
            self.selected_card_index = None
            self.play_card_btn.config(state=tk.DISABLED)
            self.selection_label.config(text="Carta jugada exitosamente")

    def play_card(self, player_id, card):
        """Ejecuta la jugada de una carta"""
        prev_color = self.current_card.color if self.current_card else None
        prev_value = self.current_card.value if self.current_card else None
        # Registrar jugada antes de actualizar la carta actual
        self.registrar_jugada(player_id, card, prev_color, prev_value)
        # Guarda la carta actual antes de actualizarla
        if card.card_type != 'wildcard':
            self.current_card = card
        # Agregar al descarte
        self.deck.discarded.append(card)
        # Log de la jugada
        self.add_to_log(f"{self.player_names[player_id]} juega: {card.to_display_string()}")
        # Verificar victoria
        if len(self.player_hands[player_id]) == 0:
            # Penalización si no declaró UNO
            if not self.uno_declarado.get(player_id, False):
                self.add_to_log(f"❌ {self.player_names[player_id]} no declaró UNO. Penalización: +2 cartas")
                for _ in range(2):
                    penal_card = self.deck.deal_card()
                    if penal_card:
                        self.player_hands[player_id].append(penal_card)
                self.update_all_displays()
                self.uno_declarado[player_id] = False
                return  # No termina el juego, sigue jugando
            else:
                self.uno_declarado[player_id] = False  # Reset
                self.game_over(player_id)
                return
        # Verificar UNO
        if len(self.player_hands[player_id]) == 1:
            self.add_to_log(f"¡{self.player_names[player_id]} tiene UNO!")
            if player_id == 1:
                self.declare_uno()  # La máquina declara UNO automáticamente
        # Efectos de cartas especiales
        self.apply_card_effects(card, player_id)
        # Actualizar probabilidades, pasando la carta anterior
        self.update_probabilities_after_play(player_id, card, prev_color, prev_value)
        # Avanzar turno
        self.advance_turn()
        # Actualizar interfaz
        self.update_all_displays()
        # Si el siguiente turno es de la máquina, programar su jugada
        if self.current_player == 1:
            self.root.after(1500, self.machine_play_turn)

    def apply_card_effects(self, card, player_id):
        """Aplica los efectos de las cartas especiales"""
        if card.value == 'rev':  # Reversa
            self.game_direction *= -1
            self.add_to_log("🔄 Orden de juego invertido")
        elif card.value == 's':  # Salta
            self.current_player = (self.current_player + self.game_direction) % 3
            self.add_to_log(f"⏭️ {self.player_names[self.current_player]} pierde su turno")
        elif card.value == 'r2':  # Roba 2
            next_player = (self.current_player + self.game_direction) % 3
            for _ in range(2):
                drawn_card = self.deck.deal_card()
                if drawn_card:
                    self.player_hands[next_player].append(drawn_card)
            self.add_to_log(f"📥 {self.player_names[next_player]} roba 2 cartas y pierde turno")
            self.current_player = (self.current_player + self.game_direction) % 3
        elif card.value == 'r4':  # Roba 4
            next_player = (self.current_player + self.game_direction) % 3
            for _ in range(4):
                drawn_card = self.deck.deal_card()
                if drawn_card:
                    self.player_hands[next_player].append(drawn_card)
            self.add_to_log(f"📥 {self.player_names[next_player]} roba 4 cartas y pierde turno")
            self.current_player = (self.current_player + self.game_direction) % 3

    def advance_turn(self):
        """Avanza al siguiente turno"""
        self.current_player = (self.current_player + self.game_direction) % 3

    def machine_play_turn(self):
        """Ejecuta el turno de la máquina con IA"""
        if self.current_player != 1:
            return
        self.add_to_log("🤖 Turno de la máquina...")
        # Obtener cartas válidas
        valid_cards = self.get_machine_valid_cards()
        if not valid_cards:
            # Debe robar
            self.add_to_log("🤖 Máquina roba una carta")
            drawn_card = self.deck.deal_card()
            if drawn_card:
                self.player_hands[1].append(drawn_card)
                # Verificar si puede jugar la carta robada
                if self.is_valid_play(drawn_card):
                    self.add_to_log(f"🤖 Máquina juega carta robada: {drawn_card.to_display_string()}")
                    self.player_hands[1].remove(drawn_card)
                    self.play_card(1, drawn_card)
                else:
                    self.add_to_log("🤖 Máquina no puede jugar carta robada")
                    self.advance_turn()
                    self.update_all_displays()
            return
        # Seleccionar carta usando IA
        selected_card_info = self.machine_select_card(valid_cards)
        if selected_card_info:
            index, card, reasoning = selected_card_info
            # Mostrar razonamiento de IA
            self.ai_decision_text.delete(1.0, tk.END)
            self.ai_decision_text.insert(tk.END, reasoning)
            # Jugar carta
            self.player_hands[1].pop(index)
            self.add_to_log(f"🤖 Máquina juega: {card.to_display_string()}")
            self.play_card(1, card)

    def get_machine_valid_cards(self):
        """Obtiene cartas válidas para la máquina"""
        valid_cards = []
        for i, card in enumerate(self.player_hands[1]):
            if self.is_valid_play(card):
                valid_cards.append((i, card))
        return valid_cards

    def machine_select_card(self, valid_cards):
        """IA para seleccionar carta (basado en PDF)"""
        if not valid_cards:
            return None
        reasoning = "🧠 ANÁLISIS IA:\n"
        # Estrategia 1: Jugador siguiente con pocas cartas
        next_player = (1 + self.game_direction) % 3
        next_player_cards = len(self.player_hands[next_player])
        if next_player_cards <= 3:
            reasoning += f"⚠️ {self.player_names[next_player]} tiene {next_player_cards} cartas!\n"
            reasoning += "Prioridad: Cartas defensivas\n"
            defensive_cards = []
            for i, card in valid_cards:
                if card.value in ['r2', 'r4', 's', 'rev']:
                    defensive_cards.append((i, card))
            if defensive_cards:
                selected = random.choice(defensive_cards)
                reasoning += f"✅ Seleccionada: {selected[1].to_display_string()}\n"
                reasoning += "Razón: Carta defensiva"
                return selected[0], selected[1], reasoning
        # Estrategia 2: Selección por probabilidades
        reasoning += "📊 Análisis probabilístico:\n"
        # a. Cartas que coinciden en color
        color_matches = []
        for i, card in valid_cards:
            if (card.color == self.current_card.color and 
                card.value != self.current_card.value):
                prob = self.get_probability_opponent_has_card(next_player, card)
                color_matches.append((i, card, prob))
                reasoning += f"{card.to_display_string()}: {prob:.2f}\n"
        if color_matches:
            # Ordenar por menor probabilidad
            color_matches.sort(key=lambda x: x[2])
            selected = color_matches[0]
            reasoning += f"\n✅ Mejor opción por color: {selected[1].to_display_string()}"
            return selected[0], selected[1], reasoning
        # b. Cartas que coinciden en número
        number_matches = []
        for i, card in valid_cards:
            if (isinstance(card.value, int) and isinstance(self.current_card.value, int) and
                card.value == self.current_card.value and card.color != self.current_card.color):
                prob = self.get_probability_opponent_has_card(next_player, card)
                number_matches.append((i, card, prob))
        if number_matches:
            number_matches.sort(key=lambda x: x[2])
            selected = number_matches[0]
            reasoning += f"\n✅ Mejor opción por número: {selected[1].to_display_string()}"
            return selected[0], selected[1], reasoning
        # c. Comodines (última opción)
        wildcard_matches = [(i, card) for i, card in valid_cards if card.card_type == 'wildcard']
        if wildcard_matches:
            selected = random.choice(wildcard_matches)
            reasoning += f"\n✅ Usando comodín: {selected[1].to_display_string()}"
            return selected[0], selected[1], reasoning
        # Cualquier carta válida
        selected = random.choice(valid_cards)
        reasoning += f"\n✅ Carta aleatoria: {selected[1].to_display_string()}"
        return selected[0], selected[1], reasoning

    def get_probability_opponent_has_card(self, player_id, card):
        """Calcula probabilidad de que oponente tenga carta similar"""
        if player_id == 1:  # Máquina
            return 0.0
        prob = 0.0
        count = 0
        if card.card_type == 'number':
            if card.color in self.probabilities[player_id]['colors']:
                prob += self.probabilities[player_id]['colors'][card.color]
                count += 1
            if card.value in self.probabilities[player_id]['numbers']:
                prob += self.probabilities[player_id]['numbers'][card.value]
                count += 1
        elif card.card_type == 'special':
            if card.color in self.probabilities[player_id]['colors']:
                prob += self.probabilities[player_id]['colors'][card.color]
                count += 1
            if card.value in self.probabilities[player_id]['specials']:
                prob += self.probabilities[player_id]['specials'][card.value]
                count += 1
        elif card.card_type == 'wildcard':
            if card.value in self.probabilities[player_id]['wildcards']:
                prob += self.probabilities[player_id]['wildcards'][card.value]
                count += 1
        return prob / max(count, 1)

    def update_probabilities_after_play(self, player_id, card, prev_color, prev_value):
        """Actualiza probabilidades después de una jugada"""
        if player_id == 1:  # No actualizar para la máquina
            return
        # Actualizar contadores globales
        self.update_card_counters_remove(card)
        # Calcular total de cartas restantes
        total_remaining = (
            sum(self.card_counters['colors'].values()) +
            self.card_counters['number_0'] +
            sum(self.card_counters['numbers'].values()) +
            sum(self.card_counters['specials'].values()) +
            sum(self.card_counters['wildcards'].values())
        )
        # Solo actualizar probabilidades para los oponentes humanos
        opponents = [0, 2] if player_id != 1 else []
        for target_player in opponents:
            if target_player not in self.probabilities:
                continue
            # --- ACTUALIZAR SOLO LO AFECTADO POR LA CARTA JUGADA ---
            if card.card_type == 'number':
                # Actualizar color
                if card.color:
                    self.probabilities[target_player]['colors'][card.color] = (
                        self.card_counters['colors'][card.color] / max(total_remaining, 1)
                    )
                # Actualizar número
                if card.value == 0:
                    self.probabilities[target_player]['numbers'][0] = (
                        self.card_counters['number_0'] / max(total_remaining, 1)
                    )
                else:
                    self.probabilities[target_player]['numbers'][card.value] = (
                        self.card_counters['numbers'].get(card.value, 0) / max(total_remaining, 1)
                    )
            elif card.card_type == 'special':
                # Actualizar color
                if card.color:
                    self.probabilities[target_player]['colors'][card.color] = (
                        self.card_counters['colors'][card.color] / max(total_remaining, 1)
                    )
                # Actualizar especial
                self.probabilities[target_player]['specials'][card.value] = (
                    self.card_counters['specials'].get(card.value, 0) / max(total_remaining, 1)
                )
            elif card.card_type == 'wildcard':
                # Actualizar comodín
                self.probabilities[target_player]['wildcards'][card.value] = (
                    self.card_counters['wildcards'].get(card.value, 0) / max(total_remaining, 1)
                )
            # --- CASOS ESPECIALES ---
            # Caso 1: Misma carta que el mazo (color y número)
            if card.card_type == 'number' and card.color == prev_color and card.value == prev_value:
                pass  # Ya se actualizó globalmente
            # Caso 2: Mismo color, diferente número
            elif card.card_type == 'number' and card.color == prev_color:
                pass  # No actualizar la probabilidad del número para los oponentes
            # Caso 4: Comodín o Roba 4
            elif card.card_type == 'wildcard':
                self.probabilities[target_player]['colors'][prev_color] = 0.0
                self.probabilities[target_player]['numbers'][prev_value] = 0.0
            # Caso 5: Carta especial (+2, reversa, salta)
            elif card.card_type == 'special':
                self.probabilities[target_player]['numbers'][prev_value] = 0.0

        # --- ACTUALIZAR PROPIA PROBABILIDAD SI JUGÓ MISMO NÚMERO, DIFERENTE COLOR ---
        if card.card_type == 'number' and card.value == prev_value and card.color != prev_color:
            self.probabilities[player_id]['colors'][prev_color] = 0.0
        if card.card_type == 'number' and card.color == prev_color and card.value != prev_value:
            self.probabilities[player_id]['numbers'][prev_value] = 0.0

    def registrar_jugada(self, player_id, card, prev_color, prev_value):
        # Guarda la jugada y las probabilidades de ambos jugadores humanos
        jugada = {
            'Partida': 'Actual',
            'Tiró': self.player_names[player_id],
            'Carta en juego': self.current_card.to_display_string() if self.current_card else '',
            'Carta tirada': card.to_display_string(),
        }
        # Probabilidades de Jugador 1 y Jugador 2
        for jugador in [0, 2]:
            base = f'J{jugador+1}_'
            probs = self.probabilities[jugador]
            jugada[base+'ROJO'] = probs['colors']['r']*100
            jugada[base+'VERDE'] = probs['colors']['v']*100
            jugada[base+'AZUL'] = probs['colors']['a']*100
            jugada[base+'AMARILLO'] = probs['colors']['am']*100
            for n in range(10):
                jugada[base+str(n)] = probs['numbers'][n]*100
            jugada[base+'Comodín'] = probs['wildcards']['c']*100
            jugada[base+'Come 2'] = probs['specials']['r2']*100
            jugada[base+'Come 4'] = probs['wildcards']['r4']*100
            jugada[base+'Salta'] = probs['specials']['s']*100
            jugada[base+'Reversa'] = probs['specials']['rev']*100
        self.jugada_stats.append(jugada)

    def draw_card(self):
        """Permite al jugador current_player robar una carta"""
        if self.current_player == 1:  # No permitir robo manual para la máquina
            return
        drawn_card = self.deck.deal_card()
        if drawn_card:
            self.player_hands[self.current_player].append(drawn_card)
            self.add_to_log(f"{self.player_names[self.current_player]} roba una carta")
            # Actualizar probabilidades (no tiene cartas válidas)
            self.update_probabilities_after_draw(self.current_player)
            # Verificar si puede jugar la carta robada
            if self.is_valid_play(drawn_card):
                messagebox.showinfo("Carta Robada", 
                    f"Robaste: {drawn_card.to_display_string()}\nJugarás esta carta automáticamente.")
                self.player_hands[self.current_player].remove(drawn_card)

                # Guardar color y valor de la carta previa (la que obligó a robar)
                prev_color = self.current_card.color
                prev_value = self.current_card.value
                jugador_que_robo = self.current_player
                otro_jugador = 0 if jugador_que_robo == 2 else 2

                self.play_card(jugador_que_robo, drawn_card)

                # Mantener probabilidades en 0 SOLO para el jugador que robó
                self.probabilities[jugador_que_robo]['colors'][prev_color] = 0.0
                self.probabilities[jugador_que_robo]['numbers'][prev_value] = 0.0
                return

        # No puede jugar, avanzar turno
        self.advance_turn()
        self.update_all_displays()
        # Si el siguiente es la máquina, programar su turno
        if self.current_player == 1:
            self.root.after(1500, self.machine_play_turn)

    def update_probabilities_after_draw(self, player_id):
        """
        Caso 6: Jugador roba del mazo porque no tiene cartas válidas
        """
        if player_id == 1:
            return
        current_color = self.current_card.color
        current_value = self.current_card.value
        current_type = self.current_card.card_type

        # Siempre baja a 0 el color y número actual
        self.probabilities[player_id]['colors'][current_color] = 0.0
        self.probabilities[player_id]['numbers'][current_value] = 0.0

        # Para cada carta especial, baja el contador y actualiza la probabilidad
        total_cards = (
            sum(self.card_counters['colors'].values()) +
            self.card_counters['number_0'] +
            sum(self.card_counters['numbers'].values()) +
            sum(self.card_counters['specials'].values()) +
            sum(self.card_counters['wildcards'].values())
        )
        for special in self.special_cards:
            # Baja el contador solo si hay cartas restantes
            if self.card_counters['specials'][special] > 0:
                self.card_counters['specials'][special] -= 1
            self.probabilities[player_id]['specials'][special] = (
                self.card_counters['specials'][special] / max(total_cards, 1)
            )

        # Si la carta actual es comodín, baja el contador y actualiza la probabilidad de comodines
        if current_type == 'wildcard':
            for wildcard in self.wildcards:
                if self.card_counters['wildcards'][wildcard] > 0:
                    self.card_counters['wildcards'][wildcard] -= 1
                self.probabilities[player_id]['wildcards'][wildcard] = (
                    self.card_counters['wildcards'][wildcard] / max(total_cards, 1)
                )

    def declare_uno(self):
        """Declara UNO"""
        player_id = self.current_player
        if len(self.player_hands[player_id]) == 1:
            self.add_to_log(f"🔔 {self.player_names[player_id]} declara UNO!")
            self.uno_declarado[player_id] = True
        else:
            self.add_to_log(f"❌ {self.player_names[player_id]} declara UNO incorrectamente")

    def game_over(self, winner_id):
        """Termina el juego"""
        self.game_started = False
        self.add_to_log(f"🎉 ¡{self.player_names[winner_id]} ha ganado!")
        messagebox.showinfo("¡Juego Terminado!", 
                          f"🎉 ¡{self.player_names[winner_id]} ha ganado la partida!")
        # Mostrar botón para exportar estadísticas
        self.export_btn = tk.Button(self.root, text="📊 Exportar Estadísticas a Excel", command=self.exportar_estadisticas_excel, bg="#F1C40F", font=("Arial", 12, "bold"))
        self.export_btn.place(relx=0.5, rely=0.95, anchor=tk.CENTER)

    def exportar_estadisticas_excel(self):
        if not self.jugada_stats:
            messagebox.showwarning("Sin datos", "No hay jugadas registradas para exportar.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")], title="Guardar estadísticas de la partida")
        if file_path:
            df = pd.DataFrame(self.jugada_stats)
            df.to_excel(file_path, index=False)
            messagebox.showinfo("Exportación exitosa", f"Estadísticas exportadas a:\n{file_path}")
            self.export_btn.destroy()

    def update_all_displays(self):
        """Actualiza todas las pantallas"""
        self.update_current_card_display()
        self.update_player_displays()
        self.update_game_state_display()
        self.update_statistics()

    def update_current_card_display(self):
        """Actualiza la visualización de la carta actual"""
        if self.current_card:
            self.current_card_display.config(
                text=self.current_card.to_display_string(),
                bg=self.current_card.get_color_hex()
            )

    def update_player_displays(self):
        """Actualiza las visualizaciones de los jugadores"""
        for player_id in range(3):
            # Limpiar frame de cartas
            for widget in self.player_card_frames[player_id].winfo_children():
                widget.destroy()
            # Actualizar contador de cartas
            card_count = len(self.player_hands[player_id])
            self.player_card_count_labels[player_id].config(text=f"Cartas: {card_count}")
            # Crear botones de cartas
            if player_id == 1:  # Máquina - mostrar cartas verticalmente
                for i, card in enumerate(self.player_hands[player_id]):
                    btn = self.create_card_button(self.player_card_frames[player_id], card, i, player_id)
                    btn.pack(pady=2, fill=tk.X)
            else:  # Jugadores humanos - mostrar horizontalmente
                for i, card in enumerate(self.player_hands[player_id]):
                    btn = self.create_card_button(self.player_card_frames[player_id], card, i, player_id)
                    btn.pack(side=tk.LEFT, padx=2)

    def update_game_state_display(self):
        """Actualiza el estado del juego"""
        # Actualizar jugador current_player
        current_name = self.player_names[self.current_player]
        self.current_player_label.config(text=f"Turno: {current_name}")
        # Actualizar dirección
        direction_text = "→" if self.game_direction == 1 else "←"
        self.direction_label.config(text=f"Dirección: {direction_text}")
        # Habilitar/deshabilitar controles
        if self.current_player == 1:  # Turno de máquina
            self.play_card_btn.config(state=tk.DISABLED)
            self.deck_button.config(state=tk.DISABLED)
            self.selection_label.config(text="🤖 Turno de la máquina...")
        else:  # Turno de jugador humano
            self.deck_button.config(state=tk.NORMAL)
            if self.selected_card_index is not None:
                self.play_card_btn.config(state=tk.NORMAL)
            else:
                self.play_card_btn.config(state=tk.DISABLED)
                self.selection_label.config(text="Selecciona una carta para jugar")

    def update_machine_hand_from_probabilities(self):
        """Actualiza contadores basado en la mano de la máquina"""
        for card in self.player_hands[1]:
            self.update_card_counters_remove(card)

    def update_statistics(self):
        """Actualiza las estadísticas en tiempo real"""
        self.probability_text.delete(1.0, tk.END)
        self.probability_text.insert(tk.END, "📊 PROBABILIDADES ACTUALES\n")
        self.probability_text.insert(tk.END, "=" * 40 + "\n")
        for player_id in [0, 2]:
            player_name = self.player_names[player_id]
            card_count = len(self.player_hands[player_id])
            self.probability_text.insert(tk.END, f"{player_name} ({card_count} cartas):\n")
            # Colores
            self.probability_text.insert(tk.END, "Colores:\n")
            for color in self.colors:
                prob = self.probabilities[player_id]['colors'][color]
                color_name = {'a': 'Azul', 'v': 'Verde', 'r': 'Rojo', 'am': 'Amarillo'}[color]
                self.probability_text.insert(tk.END, f"  {color_name}: {prob:.2%}\n")
            # Números
            self.probability_text.insert(tk.END, "Números:\n")
            for num in range(10):
                prob = self.probabilities[player_id]['numbers'][num]
                self.probability_text.insert(tk.END, f"  {num}: {prob:.2%}\n")
            # Especiales
            self.probability_text.insert(tk.END, "Especiales:\n")
            for special in self.special_cards:
                prob = self.probabilities[player_id]['specials'][special]
                special_name = {'r2': 'Roba2', 'rev': 'Reversa', 's': 'Salta'}[special]
                self.probability_text.insert(tk.END, f"  {special_name}: {prob:.2%}\n")
            # Comodines
            self.probability_text.insert(tk.END, "Comodines:\n")
            for wildcard in self.wildcards:
                prob = self.probabilities[player_id]['wildcards'][wildcard]
                wildcard_name = {'c': 'Comodín', 'r4': 'Roba4'}[wildcard]
                self.probability_text.insert(tk.END, f"  {wildcard_name}: {prob:.2%}\n")
            self.probability_text.insert(tk.END, "\n" + "-" * 30 + "\n")

        # Actualizar contadores
        self.counters_text.delete(1.0, tk.END)
        self.counters_text.insert(tk.END, "🎯 CONTADORES DE CARTAS\n")
        self.counters_text.insert(tk.END, "=" * 40 + "\n")
        # Colores
        self.counters_text.insert(tk.END, "Colores restantes:\n")
        for color, count in self.card_counters['colors'].items():
            color_name = {'a': 'Azul', 'v': 'Verde', 'r': 'Rojo', 'am': 'Amarillo'}[color]
            self.counters_text.insert(tk.END, f"  {color_name}: {count}\n")
        # Números
        self.counters_text.insert(tk.END, f"\nNúmero 0: {self.card_counters['number_0']}\n")
        self.counters_text.insert(tk.END, "Números 1-9:\n")
        for num, count in self.card_counters['numbers'].items():
            self.counters_text.insert(tk.END, f"  {num}: {count}\n")
        # Especiales
        self.counters_text.insert(tk.END, "\nEspeciales:\n")
        for special, count in self.card_counters['specials'].items():
            special_name = {'r2': 'Roba2', 'rev': 'Reversa', 's': 'Salta'}[special]
            self.counters_text.insert(tk.END, f"  {special_name}: {count}\n")
        # Comodines
        self.counters_text.insert(tk.END, "\nComodines:\n")
        for wildcard, count in self.card_counters['wildcards'].items():
            wildcard_name = {'c': 'Común', 'r4': 'Roba4'}[wildcard]
            self.counters_text.insert(tk.END, f"  {wildcard_name}: {count}\n")
        # Total de cartas en el mazo
        total_remaining = (
            sum(self.card_counters['colors'].values()) +
            self.card_counters['number_0'] +
            sum(self.card_counters['numbers'].values()) +
            sum(self.card_counters['specials'].values()) +
            sum(self.card_counters['wildcards'].values())
        )
        mazo_real = len(self.deck.cards)
        cartas_en_manos = sum(len(hand) for hand in self.player_hands)
        cartas_jugadas = len(self.deck.discarded)
        total_real = mazo_real + cartas_en_manos + cartas_jugadas
        self.counters_text.insert(tk.END, f"\nCartas en el mazo físico: {mazo_real}\n")
        self.counters_text.insert(tk.END, f"Cartas en manos de jugadores: {cartas_en_manos}\n")
        self.counters_text.insert(tk.END, f"Cartas jugadas: {cartas_jugadas}\n")
        self.counters_text.insert(tk.END, f"Total real de cartas: {total_real}\n")
    
    def add_to_log(self, message):
        """Añade mensaje al log del juego"""
        timestamp = time.strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        self.game_log_text.insert(tk.END, log_message)
        self.game_log_text.see(tk.END)  # Scroll automático

    def run(self):
        """Ejecuta la aplicación"""
        self.root.mainloop()


# Función principal
def main():
    """Función principal para ejecutar el juego"""
    try:
        app = UNOIntelligentGUI()
        app.run()
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
