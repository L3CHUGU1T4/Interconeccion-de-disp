# 🎮 UNO - Agente Inteligente

Un juego de UNO implementado en Python con una interfaz gráfica y un agente inteligente que utiliza probabilidades para tomar decisiones.

## 📋 Requisitos

- Python 3.6 o superior
- Tkinter (incluido en la mayoría de las instalaciones de Python)
- pandas

## 🚀 Instalación

1. Clona este repositorio o descarga los archivos:
```bash
git clone https://github.com/L3CHUGU1T4/Interconeccion-de-disp/tree/main
```

2. Instala las dependencias necesarias:
```bash
pip install pandas
```

## 🎲 Cómo Jugar

1. Ejecuta el juego:
```bash
python unointerfacev3.py
```

2. El juego se iniciará automáticamente con:
   - Jugador 1 (Tú)
   - Máquina (Agente Inteligente)
   - Jugador 2 (Tú)

### 📝 Reglas del Juego

- Cada jugador comienza con 7 cartas
- Debes jugar una carta que coincida con el color o número de la carta actual
- Las cartas especiales tienen efectos específicos:
  - 🎨 Comodín: Cambia el color
  - 🎨 Comodín +4: Cambia el color y el siguiente jugador roba 4 cartas
  - ⏭️ Salta: El siguiente jugador pierde su turno
  - 🔄 Reversa: Cambia la dirección del juego
  - 📥 Roba 2: El siguiente jugador roba 2 cartas y pierde su turno

### 🎯 Características

- Interfaz gráfica intuitiva
- Agente inteligente que utiliza probabilidades para tomar decisiones
- Sistema de registro de jugadas y estadísticas
- Exportación de estadísticas a Excel
- Visualización en tiempo real de probabilidades y contadores

### 🎮 Controles

- Haz clic en una carta para seleccionarla
- Usa el botón "Jugar Carta" para jugar la carta seleccionada
- Usa el botón "Robar" para tomar una carta del mazo
- Presiona "UNO!" cuando te quede una sola carta
- Usa "Nuevo Juego" para comenzar una nueva partida

## 📊 Estadísticas

El juego mantiene un registro detallado de:
- Probabilidades de cartas por jugador
- Contadores de cartas restantes
- Log de jugadas
- Posibilidad de exportar estadísticas a Excel

## 🤖 Agente Inteligente

La máquina utiliza un sistema de probabilidades para:
- Predecir las cartas de los oponentes
- Tomar decisiones estratégicas
- Adaptar su estrategia según el estado del juego

## 🐛 Reportar Problemas

Si encuentras algún problema o tienes sugerencias, por favor:
1. Abre un issue en el repositorio
2. Describe el problema o sugerencia
3. Incluye pasos para reproducir el problema (si aplica)

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.
