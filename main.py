# referencias: Master Python games tutorial, Lighting in Pygame y AI
# importamos los módulos necesarios, incluyendo math para la dinámica del juego
import os
import random
import math

import pygame

# estados del juego
ESTADO_INICIO = "inicio"
ESTADO_INSTRUCCIONES = "instrucciones"
ESTADO_JUGANDO = "jugando"
ESTADO_DERROTA = "derrota"
ESTADO_VICTORIA = "victoria"

# leo= agregué el estado de pausa
ESTADO_PAUSA = "pausa"

# rutas a la carpeta de imágenes de pantallas
DIR_PANTALLAS = os.path.join(os.path.dirname(__file__), "data", "pantallas")

# nombres de archivos de las imágenes de pantalla
# formatos soportados: PNG, JPG/JPEG, BMP, GIF
PANTALLA_INICIO = "pantalla_inicio.bmp"
PANTALLA_INSTRUCCIONES = "pantalla_instrucciones.bmp"
PANTALLA_VICTORIA = "pantalla_victoria.bmp"
PANTALLA_DERROTA = "pantalla_derrota.bmp"
PANTALLA_PAUSA = "pantalla_pausa.bmp"  # parte 3: imagen de pausa
PANTALLA_NIVEL2 = "pantalla_nivel2.bmp"  # parte 10: presentación nivel 2
PANTALLA_NIVEL3 = "pantalla_nivel3.bmp"  # parte 10: presentación jefe final

# velocidad mínima del jugador para evitar movimientos muy rápidos
RETRASO = 200

# códigos identificadores de los elementos del tablero

# leo= la manzana ahora funciona como caja de carga 
VACIO = 0
OBSTACULO = 1
JUGADOR = 2
MANZANA = 3

# leo= agregué nuevas variables de elementos
BOOST = 4
GASOLINA = 5
OBJETO = 6
LADRON = 7
ESCUDO = 8  # parte 3: elemento de protección

# parte 7: configuración de la cola estilo snake y penalización por ladrón
LIMITE_COLA = 12          # máximo de contenedores en la cola
PUNTOS_ROBADOS_LADRON = 5 # puntos perdidos al ser alcanzado por el ladrón

# parte 10: sistema progresivo de niveles con jefes
NIVEL_MAXIMO = 3
METAS_NIVEL = {1: 15, 2: 30, 3: 50}              # puntaje requerido por nivel
LADRONES_POR_NIVEL = {1: 1, 2: 2, 3: 3}          # cantidad de villanos por nivel
RETRASO_LADRON_POR_NIVEL = {1: 450, 2: 350, 3: 250}  # velocidad aumenta por nivel

# parte 12: habilidades especiales de villanos según el nivel
PROB_DASH_POR_NIVEL = {1: 0.0, 2: 0.15, 3: 0.25}  # probabilidad de salto doble
RADIO_PULSO_BOSS = 4          # alcance del ataque del jefe
COOLDOWN_PULSO_BOSS = 2500    # cooldown entre disparos del jefe
PUNTOS_PULSO_BOSS = 2         # puntos perdidos por disparo del jefe

# tamaño del tablero
# nota: cambiar estos valores requiere actualizar reiniciar()
FILAS = 20
COLUMNAS = 20

def aparecer_aleatorio(tablero, id_elem):
    """
    coloca un elemento en una posición aleatoria vacía del tablero.

    parámetros:
        - tablero: el tablero actual
        - id_elem: código del elemento a colocar

    retorna:
        - (columna, fila): tupla con la posición donde se colocó
    """

    # buscamos todas las casillas vacías del tablero
    vacios = []

    # recorremos filas y columnas para encontrar espacios libres
    for fila in range(FILAS):
        for columna in range(COLUMNAS):
            # obtenemos el elemento en la posición
            elem_pos = tablero[fila][columna]

            if elem_pos == VACIO:
                # agregamos la tupla (columna, fila) a la lista
                vacios.append((columna, fila))

    # alternativa: usar comprensión de listas
    # vacios = [(columna, fila) for fila in range(FILAS) for columna in range(COLUMNAS) if tablero[fila][columna] == VACIO]

    # si no hay espacios vacíos, retornamos valor especial
    if len(vacios) == 0:
        return -1, -1

    # elegimos una posición aleatoria de las disponibles
    columna, fila = random.choice(vacios)

    # colocamos el elemento en el tablero
    tablero[fila][columna] = id_elem

    return columna, fila


def poblar_tablero(tablero):
    """
    llena el tablero con obstáculos, objetos y power-ups.

    parámetros:
        - tablero: el tablero actual
    """

    # leo= bucle para generar los obstáculos, cambia el rango para más/menos
    
    for obst in range(30):
        aparecer_aleatorio(tablero, OBSTACULO)

    for roto in range(7):
        aparecer_aleatorio(tablero, OBJETO)

    aparecer_aleatorio(tablero, MANZANA)
    aparecer_aleatorio(tablero, BOOST)
    aparecer_aleatorio(tablero, GASOLINA)
    aparecer_aleatorio(tablero, ESCUDO)  
    # guardamos la posición para que el ladrón pueda perseguir

# leo= agregué puntaje a refrescar_tablero para mostrarlo
# david= activé las líneas restantes y agregué dirección como parámetro
def refrescar_tablero(screen,
                        tablero,
                        puntaje,
                        combustible,
                        sprite_jugador,
                        sprite_caja,
                        sprites_obstaculo,   # parte 4: lista de variantes de obstáculos
                        sprite_boost,
                        sprite_gasolina,
                        sprite_villano_actual,
                        sprite_escudo,
                        sprite_objeto,    # parte 5: sprite del ralentizador
                        sprite_container, # parte 7: sprite del contenedor de la cola
                        background,
                        direccion,                     
                        flash_color,      # parte 3: color del efecto flash (o None)
                        mostrar_flash,    # parte 3: si se dibuja el flash ahora
                        mostrar_pop_puntaje,  # parte 4: animación del puntaje al subir
                        cola_posiciones,  # parte 7: posiciones pasadas del jugador
                        pos_jugador,      # parte 9: posición actual para orientar la cola
                        ):

    """
    dibuja el estado actual del tablero en la pantalla.

    parámetros:
        - screen: la pantalla donde dibujamos
        - tablero: el estado actual del tablero
    """

    # leo= dibujamos el fondo del tablero
    screen.blit(background, (0,0))

    # leo= definimos las dimensiones del tablero

    ancho_tablero = 800
    largo_tablero = 800

    alto_elem = largo_tablero / FILAS
    ancho_elem = ancho_tablero / COLUMNAS

    # parte 9: cada segmento de la cola rota según la dirección
    # (mirando hacia el segmento siguiente)
    ROTACIONES_COLA = {
        (0, -1): 0,
        (0, 1): 180,
        (-1, 0): 90,
        (1, 0): -90,
    }

    for indice, (col_cola, fila_cola) in enumerate(cola_posiciones):
        pos_x_cola = col_cola * ancho_elem
        pos_y_cola = fila_cola * alto_elem

        # referencia para la rotación: el segmento siguiente
        if indice == 0:
            ref_col, ref_fila = pos_jugador
        else:
            ref_col, ref_fila = cola_posiciones[indice - 1]

        delta_col = ref_col - col_cola
        delta_fila = ref_fila - fila_cola
        delta_col = max(-1, min(1, delta_col))
        delta_fila = max(-1, min(1, delta_fila))

        angulo_cola = ROTACIONES_COLA.get((delta_col, delta_fila), 0)

        # efecto de profundidad: segmentos más atrás son más transparentes
        alpha_cola = max(90, 255 - indice * 14)
        sprite_cola = pygame.transform.rotate(sprite_container, angulo_cola)
        sprite_cola.set_alpha(alpha_cola)

        rect_cola = sprite_cola.get_rect(
            center=(pos_x_cola + ancho_elem / 2, pos_y_cola + alto_elem / 2)
        )
        screen.blit(sprite_cola, rect_cola)
    
    
    # Como el jugador es un círculo, se necesita el radio.
    radio = ancho_elem / 2

    # Posición en eje "y" en unidad de píxeles.
    pos_y = 0


    # leo= recorremos el tablero para dibujar los elementos

    for i in range(FILAS):
        #David: agregué la variable pos_x para que se dibuje correctamente el tablero y cambié el bucle for para que recorra las columnas
        pos_x = 0
        for j in range(COLUMNAS):
            if tablero[i][j] == OBSTACULO:
                # parte 4: elegimos variante según la posición en el mapa
                variante = (i + j) % len(sprites_obstaculo)
                screen.blit(sprites_obstaculo[variante], (pos_x, pos_y))
            
            elif tablero[i][j] == JUGADOR:
                
                ROTACIONES = {
                    (0, -1): 0,     
                    (0, 1): 180,    
                    (-1, 0): 90,    
                    (1, 0): -90,    
                }
                angulo = ROTACIONES.get(direccion, 0)
                sprite_rotado = pygame.transform.rotate(sprite_jugador, angulo)
                rect = sprite_rotado.get_rect(
                    center=(
                        pos_x + ancho_elem/2,
                        pos_y + alto_elem/2
                    )
                )
                screen.blit(sprite_rotado, rect)
                # david= rotamos el sprite según la dirección del movimiento 
            
            elif tablero[i][j] == MANZANA:
                dibujar_con_glow(screen, sprite_caja, (pos_x, pos_y), (60, 220, 90))

            elif tablero[i][j] == BOOST:
                dibujar_con_glow(screen, sprite_boost, (pos_x, pos_y), (80, 180, 255))
            
            elif tablero[i][j] == GASOLINA:
                dibujar_con_glow(screen, sprite_gasolina, (pos_x, pos_y), (255, 150, 60))


            elif tablero[i][j] == OBJETO: 
                # parte 5: sprite personalizado del ralentizador (sin efecto glow)
                screen.blit(sprite_objeto, (pos_x, pos_y))

            elif tablero[i][j] == LADRON:
                # dibujamos el sprite del villano actual
                screen.blit(sprite_villano_actual, (pos_x, pos_y))

            elif tablero[i][j] == ESCUDO:
                dibujar_con_glow(screen, sprite_escudo, (pos_x, pos_y), (80, 120, 255))


            # sumamos el ancho para avanzar a la siguiente columna
            pos_x += ancho_elem
        pos_y += alto_elem

    panel_hud = pygame.Rect(800, 0, 200, 800)
    pygame.draw.rect(screen, (18, 18, 22), panel_hud)
    pygame.draw.line(screen, (60, 60, 70), (800, 0), (800, 800), 2)

    #LEO= en esta parte hace que se dibuje el puntaje en la pantalla, pero lo saque de la IA
    #LEO Y DAVID= agregamos una animacion para que el puntaje se vea mas grande cuando sube y luego vuelve a su tamaño normal (((()))
    fuente = pygame.font.SysFont(None, 60 if mostrar_pop_puntaje else 40)
    color_puntaje = "gold" if mostrar_pop_puntaje else "white"

    texto = fuente.render(f"Puntaje: {puntaje}/50", True, color_puntaje)
    texto.set_alpha(250)
    screen.blit(texto, (810, 70))

    # parte 4: barra de combustible con gradiente de color según el nivel
    porcentaje = max(0, min(combustible, 100)) / 100
    color_barra = (
        int(220 * (1 - porcentaje)),
        int(200 * porcentaje),
        30,
    )
    ancho_barra_total = 170
    ancho_barra_actual = int(ancho_barra_total * porcentaje)

    pygame.draw.rect(screen, "gray20", pygame.Rect(810, 20, ancho_barra_total, 25))
    pygame.draw.rect(screen, color_barra, pygame.Rect(810, 20, ancho_barra_actual, 25))
    pygame.draw.rect(screen, "white", pygame.Rect(810, 20, ancho_barra_total, 25), 2)

    fuente_chica = pygame.font.SysFont(None, 26)
    texto_combustible = fuente_chica.render(f"{combustible}%", True, "white")
    screen.blit(texto_combustible, (818, 24))

    # actualizamos la pantalla con el contenido dibujado
    pygame.display.flip()




def cambiar_direccion(keys, direccion_actual):
    """
    detecta las teclas presionadas y retorna la nueva dirección.

    parámetros:
        - keys: estado de las teclas presionadas
        - direccion_actual: dirección anterior

    retorna:
        - tupla con la nueva dirección del jugador
    """

    # tecla W: arriba
    if keys[pygame.K_w]:
        return (0, -1)

    # tecla S: abajo
    if keys[pygame.K_s]:
        return (0, 1)

    # tecla A: izquierda
    if keys[pygame.K_a]:
        return (-1, 0)

    # tecla D: derecha
    if keys[pygame.K_d]:
        return (1, 0)

    # si no hay entrada, mantenemos la dirección anterior
    return direccion_actual


def mover_ladron(tablero, pos_ladron, pos_jugador):
    """
    parte 4: mueve al ladrón un paso persiguiendo al jugador.

    retorna:
        - (nueva_pos_ladron, atrapo_al_jugador)
    """
    col_ladron, fila_ladron = pos_ladron
    col_jugador, fila_jugador = pos_jugador

    dir_col = 0
    dir_fila = 0

    if col_jugador > col_ladron:
        dir_col = 1
    elif col_jugador < col_ladron:
        dir_col = -1

    if fila_jugador > fila_ladron:
        dir_fila = 1
    elif fila_jugador < fila_ladron:
        dir_fila = -1

    # parte 7: 30% de chance de movimiento aleatorio para hacer el juego justo
    if random.random() < 0.30:
        dir_col = random.choice([-1, 0, 1])
        dir_fila = random.choice([-1, 0, 1])

    # Intenta moverse en diagonal; si hay obstáculo, prueba solo una dirección.
    intentos = [(dir_col, dir_fila), (dir_col, 0), (0, dir_fila)]

    for mov_col, mov_fila in intentos:
        if mov_col == 0 and mov_fila == 0:
            continue

        nueva_col = col_ladron + mov_col
        nueva_fila = fila_ladron + mov_fila

        if not (0 <= nueva_col < COLUMNAS and 0 <= nueva_fila < FILAS):
            continue

        if tablero[nueva_fila][nueva_col] == OBSTACULO:
            continue

        if (nueva_col, nueva_fila) == pos_jugador:
            return (nueva_col, nueva_fila), True

        if tablero[nueva_fila][nueva_col] == VACIO:
            tablero[fila_ladron][col_ladron] = VACIO
            tablero[nueva_fila][nueva_col] = LADRON
            return (nueva_col, nueva_fila), False

    return pos_ladron, False


def avanzar(tablero, pos_jugador, direccion, escudo_activo):
    """
    mueve el jugador un paso en la dirección indicada y gestiona colisiones.

    parámetros:
        - tablero: el tablero actual
        - pos_jugador: posición actual como (columna, fila)
        - direccion: dirección del movimiento
        - escudo_activo: si el escudo está disponible

    retorna:
        - (resultado, nueva_pos): tipo de evento y nueva posición
    """

    # extraemos componentes de la dirección y posición
    dir_col, dir_fila = direccion
    ind_actual_col, ind_actual_fila = pos_jugador

    # calculamos la nueva posición
    ind_nueva_col = ind_actual_col + dir_col
    ind_nueva_fila = ind_actual_fila + dir_fila

    # verificamos si salimos del tablero
    if not (0 <= ind_nueva_col < COLUMNAS and 0 <= ind_nueva_fila < FILAS):
        return "derrota", pos_jugador

    # obtenemos el elemento en la nueva posición
    pos_elem = tablero[ind_nueva_fila][ind_nueva_col]

    if pos_elem == OBSTACULO:
        # parte 3: si hay escudo, absorbe el golpe y continúa
        if escudo_activo:
            tablero[ind_actual_fila][ind_actual_col] = VACIO
            tablero[ind_nueva_fila][ind_nueva_col] = JUGADOR
            return "escudo_usado", (ind_nueva_col, ind_nueva_fila)
        return "derrota", pos_jugador


    if pos_elem == MANZANA:
        
        tablero[ind_actual_fila][ind_actual_col] = VACIO
    
        tablero[ind_nueva_fila][ind_nueva_col] = JUGADOR

        aparecer_aleatorio(tablero, MANZANA)

        return "manzana", (ind_nueva_col, ind_nueva_fila)
    
    
    if pos_elem == BOOST:

        tablero[ind_actual_fila][ind_actual_col] = VACIO

        tablero[ind_nueva_fila][ind_nueva_col] = JUGADOR

        return "boost", (ind_nueva_col, ind_nueva_fila)
    

    if pos_elem == GASOLINA:

        tablero[ind_actual_fila][ind_actual_col] = VACIO

        tablero[ind_nueva_fila][ind_nueva_col] = JUGADOR

        return "gasolina", (ind_nueva_col, ind_nueva_fila)

    
    if pos_elem == OBJETO:

        tablero[ind_actual_fila][ind_actual_col] = VACIO

        tablero[ind_nueva_fila][ind_nueva_col] = JUGADOR

        return "objeto", (ind_nueva_col, ind_nueva_fila)
    
        
    if pos_elem == LADRON:
        # parte 7: chocar con ladrón resta puntos en lugar de matar
        if escudo_activo:
            tablero[ind_actual_fila][ind_actual_col] = VACIO
            tablero[ind_nueva_fila][ind_nueva_col] = JUGADOR
            return "escudo_usado", (ind_nueva_col, ind_nueva_fila)

        tablero[ind_actual_fila][ind_actual_col] = VACIO
        tablero[ind_nueva_fila][ind_nueva_col] = JUGADOR
        return "ladron_choque", (ind_nueva_col, ind_nueva_fila)
    
    # parte 3: recolectar el escudo de protección
    if pos_elem == ESCUDO:

        tablero[ind_actual_fila][ind_actual_col] = VACIO

        tablero[ind_nueva_fila][ind_nueva_col] = JUGADOR

        return "escudo", (ind_nueva_col, ind_nueva_fila)


    # Movimiento normal, si es que no encontramos manzana ni obstáculo.
    tablero[ind_actual_fila][ind_actual_col] = VACIO
    tablero[ind_nueva_fila][ind_nueva_col] = JUGADOR

    return "ok", (ind_nueva_col, ind_nueva_fila)


def reiniciar(nivel=1):
    """
    crea un tablero nuevo para iniciar la partida.

    retorna:
        - (tablero, pos_jugador, ladrones): tablero, posición inicial y posiciones de villanos
    """

    # nota: si cambias FILAS o COLUMNAS, actualiza este código
    tablero = []

    for fila in range(FILAS):
        fila_tablero = []
        for columna in range(COLUMNAS):
            fila_tablero.append(VACIO)
        tablero.append(fila_tablero)

    # alternativa: tablero = [[VACIO] * COLUMNAS for _ in range(FILAS)]

    poblar_tablero(tablero)

    # colocamos el jugador en posición aleatoria
    pos_jugador = aparecer_aleatorio(tablero, JUGADOR)

    # parte 10: cantidad de villanos según el nivel
    cantidad_ladrones = LADRONES_POR_NIVEL.get(nivel, 1)
    ladrones = []
    for _ in range(cantidad_ladrones):
        ladrones.append(aparecer_aleatorio(tablero, LADRON))

    return tablero, pos_jugador, ladrones


def mostrar_pantalla(screen, nombre_archivo):
    """
    carga y muestra una imagen escalada a la pantalla.

    parámetros:
        - screen: la pantalla donde dibujamos
        - nombre_archivo: nombre del archivo de imagen
    """

    ruta = os.path.join(DIR_PANTALLAS, nombre_archivo)

    try:
        imagen = pygame.image.load(ruta)
        imagen = pygame.transform.scale(imagen, screen.get_size())

        # dibujamos la imagen en (0, 0)
        screen.blit(imagen, (0, 0))

        # actualizamos la pantalla
        pygame.display.flip()
    except FileNotFoundError:
        # fallback: pantalla negra si falta la imagen
        screen.fill("black")
        pygame.display.flip()
        print(f"advertencia: no se encontró la imagen {ruta}")


def escalar_manteniendo_proporcion(sprite, alto_deseado):
    """
    parte 4: escala un sprite manteniendo su proporción ancho/alto.
    """
    proporcion = sprite.get_width() / sprite.get_height()
    ancho_deseado = int(alto_deseado * proporcion)
    return pygame.transform.smoothscale(sprite, (ancho_deseado, alto_deseado))


def dibujar_con_glow(screen, sprite, pos, color_glow):
    """
    parte 8: dibuja un sprite con efecto de brillo pulsante alrededor.
    """
    x, y = pos

    # calculamos el efecto de pulso
    tiempo = pygame.time.get_ticks()
    pulso = (math.sin(tiempo / 200) + 1) / 2

    grosor = int(2 + pulso * 3)
    alpha_contorno = int(140 + pulso * 100)

    # extraemos la silueta del sprite
    mascara = pygame.mask.from_surface(sprite)
    silueta = mascara.to_surface(setcolor=(*color_glow, 255), unsetcolor=(0, 0, 0, 0))
    silueta.set_alpha(alpha_contorno)

    # dibujamos el contorno en varias direcciones
    desplazamientos = [
        (-grosor, 0), (grosor, 0), (0, -grosor), (0, grosor),
        (-grosor, -grosor), (grosor, grosor), (-grosor, grosor), (grosor, -grosor),
    ]
    for dx, dy in desplazamientos:
        screen.blit(silueta, (x + dx, y + dy))

    screen.blit(sprite, pos)


def main():

    pygame.init()
    # creamos la ventana del juego
    screen = pygame.display.set_mode((1000, 800))
    pygame.display.set_caption("Juego Básico")

    # leo= cargamos las imágenes de objetos
    # david= agregué sprites, sonidos, imágenes y música de fondo

    DIR_SPRITES = os.path.join(os.path.dirname(__file__), "data", "sprite")
    
    DIR_BACKGROUND = os.path.join(os.path.dirname(__file__), "data", "background")

    # parte 11: fondos distintos por nivel
    backgrounds_por_nivel = {}
    for nivel_bg, archivo_bg in [
        (1, "suelo_nivel1.png"),
        (2, "suelo_nivel2.png"),
        (3, "suelo_nivel3.png"),
    ]:
        bg = pygame.image.load(os.path.join(DIR_BACKGROUND, archivo_bg)).convert()
        bg = pygame.transform.scale(bg, (800, 800))
        backgrounds_por_nivel[nivel_bg] = bg

    background = backgrounds_por_nivel[1]  # fondo inicial del nivel 1

    CASILLA = 40

    ALTO_VEHICULO = 78  # parte 8: aumentado para mejor visibilidad
    ALTO_ITEM = 62      # parte 8: aumentado para mejor visibilidad

    sprite_jugador = pygame.image.load(os.path.join(DIR_SPRITES, "camion.png")).convert_alpha()
    sprite_jugador = escalar_manteniendo_proporcion(sprite_jugador, ALTO_VEHICULO)

    sprite_caja = pygame.image.load(os.path.join(DIR_SPRITES, "caja.png")).convert_alpha()
    sprite_caja = escalar_manteniendo_proporcion(sprite_caja, ALTO_ITEM)

    # parte 4: 3 variantes de obstáculos para mayor variedad visual
    sprites_obstaculo = []
    for nombre_obstaculo in ("obstaculo1.png", "obstaculo2.png", "obstaculo3.png"):
        sprite = pygame.image.load(os.path.join(DIR_SPRITES, nombre_obstaculo)).convert_alpha()
        sprite = escalar_manteniendo_proporcion(sprite, ALTO_ITEM)
        sprites_obstaculo.append(sprite)

    sprite_gasolina = pygame.image.load(os.path.join(DIR_SPRITES, "gasolina.png")).convert_alpha()
    sprite_gasolina = escalar_manteniendo_proporcion(sprite_gasolina, ALTO_ITEM)

    sprite_boost = pygame.image.load(os.path.join(DIR_SPRITES, "boost.png")).convert_alpha()
    sprite_boost = escalar_manteniendo_proporcion(sprite_boost, ALTO_ITEM)

    # sprites de villanos según el nivel
    sprites_ladron_nivel = {}
    for nivel_sprite, archivo in [
        (1, "villano_nivel1.png"),
        (2, "villano_nivel2.png"),
        (3, "villano_nivel3_boss.png"),
    ]:
        sprite = pygame.image.load(os.path.join(DIR_SPRITES, archivo)).convert_alpha()
        alto_villano = ALTO_VEHICULO if nivel_sprite < 3 else int(ALTO_VEHICULO * 1.3)
        sprites_ladron_nivel[nivel_sprite] = escalar_manteniendo_proporcion(sprite, alto_villano)

    # sprite del escudo
    sprite_escudo = pygame.image.load(
        os.path.join(DIR_SPRITES, "escudo.png")
    ).convert_alpha()
    sprite_escudo = escalar_manteniendo_proporcion(sprite_escudo, ALTO_ITEM)

    # sprite del ralentizador
    sprite_objeto = pygame.image.load(
        os.path.join(DIR_SPRITES, "objeto.png")
    ).convert_alpha()
    sprite_objeto = escalar_manteniendo_proporcion(sprite_objeto, ALTO_ITEM)

    # parte 7: sprite del contenedor que forma la cola
    sprite_container = pygame.image.load(
        os.path.join(DIR_SPRITES, "container.png")
    ).convert_alpha()
    sprite_container = escalar_manteniendo_proporcion(sprite_container, int(ALTO_VEHICULO * 0.85))

    # ---- Sonidos ----
    DIR_SONIDOS = os.path.join(os.path.dirname(__file__), "data", "sonidos")

    sonido_caja = pygame.mixer.Sound(os.path.join(DIR_SONIDOS, "recoger_caja.mp3"))
    sonido_boost = pygame.mixer.Sound(os.path.join(DIR_SONIDOS, "boost.mp3"))
    sonido_gasolina = pygame.mixer.Sound(os.path.join(DIR_SONIDOS, "gasolina.mp3"))
    sonido_choque = pygame.mixer.Sound(os.path.join(DIR_SONIDOS, "choque.mp3"))
    sonido_ladron = pygame.mixer.Sound(os.path.join(DIR_SONIDOS, "ladron.mp3"))
    sonido_escudo = pygame.mixer.Sound(os.path.join(DIR_SONIDOS, "escudo.mp3"))

    # david= música de fondo que se reproduce en bucle
    LISTA_OST = [
        "musica_1.mp3",
        "musica_2.mp3",
        "musica_3.mp3",
    ]
    indice_cancion_actual = 0

    # cambia a la siguiente canción cuando termina la actual
    EVENTO_CANCION_TERMINO = pygame.USEREVENT + 1
    pygame.mixer.music.set_endevent(EVENTO_CANCION_TERMINO)

    pygame.mixer.music.load(os.path.join(DIR_SONIDOS, LISTA_OST[indice_cancion_actual]))
    pygame.mixer.music.set_volume(0.4)
    pygame.mixer.music.play()  



    # pantalla principal del juego
    screen = pygame.display.set_mode((1000, 800))
    pygame.display.set_caption("DASH & DASH")

    # leo= gestión del consumo de gasolina: 
    gasto = pygame.time.get_ticks()

    running = True

    # inicializamos las variables del juego
    estado = ESTADO_INICIO
    tablero = []
    pos_jugador = (0, 0)
    nivel_actual = 1                                     # parte 10
    ladrones = []                                        # parte 10: lista de villanos
    sprite_villano_actual = None                         # se asigna después
    cola_posiciones = []                                 # parte 7: posiciones pasadas
    direccion = (0, 0)
    tiempo_ultimo_mov = 0
    retraso = 200

    RETRASO_LADRON = RETRASO_LADRON_POR_NIVEL[1]  # parte 10: depende del nivel
    sprite_villano_actual = sprites_ladron_nivel[1]  # parte 10

    # leo= variables de puntuación y combustible
    puntaje = 0
    combustible = 100

    boost_activo = True
    tiempo_boost = 0

    ralentizado = False
    tiempo_ralentizado = 0

    escudo_activo = False  # parte 3: sin escudo al inicio

    flash_color = None      # parte 3: color del efecto flash
    mostrar_flash = False   # parte 3: si mostrar el flash
    mostrar_pop_puntaje = False  # parte 4: animación del puntaje
    
    mostrar_pantalla(screen, PANTALLA_INICIO)
    
    
    
    while running:
        # procesamos eventos de entrada
        for evento in pygame.event.get():
            # si el usuario cierra la ventana
            if evento.type == pygame.QUIT:
                running = False
            # david= cambiamos la canción cuando termina la anterior
            if evento.type == EVENTO_CANCION_TERMINO:
                indice_cancion_actual = (indice_cancion_actual + 1) % len(LISTA_OST)
                pygame.mixer.music.load(os.path.join(DIR_SONIDOS, LISTA_OST[indice_cancion_actual]))
                pygame.mixer.music.play()

            # si se presiona una tecla
            if evento.type == pygame.KEYDOWN:
                if estado == ESTADO_INICIO:
                    if evento.key == pygame.K_SPACE:
                        nivel_actual = 1  # parte 10: nueva partida en nivel 1
                        RETRASO_LADRON = RETRASO_LADRON_POR_NIVEL[nivel_actual]
                        sprite_villano_actual = sprites_ladron_nivel[nivel_actual]
                        background = backgrounds_por_nivel[nivel_actual]  # parte 11
                        tablero, pos_jugador, ladrones = reiniciar(nivel_actual)
                        direccion = (0, 0)
                        cola_posiciones = []  # parte 7: cola limpia al inicio
                        # guardamos el tiempo actual en milisegundos
                        tiempo_ultimo_mov = pygame.time.get_ticks()
                        tiempo_ultimo_mov_ladron = pygame.time.get_ticks()  # parte 4
                        estado = ESTADO_JUGANDO
                        refrescar_tablero(screen, tablero, puntaje, combustible, sprite_jugador, sprite_caja, sprites_obstaculo, sprite_boost, sprite_gasolina, sprite_villano_actual, sprite_escudo, sprite_objeto, sprite_container, background, direccion, flash_color, mostrar_flash, mostrar_pop_puntaje, cola_posiciones, pos_jugador)
                    elif evento.key == pygame.K_i:
                        estado = ESTADO_INSTRUCCIONES
                        mostrar_pantalla(screen, PANTALLA_INSTRUCCIONES)

                elif estado == ESTADO_INSTRUCCIONES:
                    estado = ESTADO_INICIO
                    mostrar_pantalla(screen, PANTALLA_INICIO)

                elif estado in (ESTADO_DERROTA, ESTADO_VICTORIA):
                    if evento.key == pygame.K_r:
                        tablero, pos_jugador, pos_ladron = reiniciar()
                        direccion = (0, 0)
                        # leo= reiniciamos las variables
                        puntaje = 0
                        combustible = 100

                        boost_activo = True 
                        tiempo_boost = 0
                        retraso = 200
                        ralentizado = False
                        tiempo_ralentizado = 0
                        escudo_activo = False  # parte 3
                        flash_color = None     # parte 3
                        mostrar_flash = False  # parte 3
                        mostrar_pop_puntaje = False  # parte 4

                        tiempo_ultimo_mov = pygame.time.get_ticks()
                        tiempo_ultimo_mov_ladron = pygame.time.get_ticks()  # parte 4
                        estado = ESTADO_JUGANDO
                        refrescar_tablero(screen, tablero, puntaje, combustible, sprite_jugador, sprite_caja, sprites_obstaculo, sprite_boost, sprite_gasolina, sprite_villano_actual, sprite_escudo, sprite_objeto, sprite_container, background, direccion, flash_color, mostrar_flash, mostrar_pop_puntaje, cola_posiciones, pos_jugador)

                    if evento.key == pygame.K_ESCAPE:
                        estado = ESTADO_INICIO
                        mostrar_pantalla(screen, PANTALLA_INICIO)
                        boost_activo = True
                        tiempo_boost = 0
                        retraso = 200

                        puntaje = 0
                        combustible = 100

                # leo= estado de pausa agregado
                elif estado == ESTADO_JUGANDO:

                    if evento.key == pygame.K_ESCAPE:
                        estado = ESTADO_PAUSA
                        mostrar_pantalla(screen, PANTALLA_PAUSA)  # parte 3: pantalla de pausa

                    else:
                        direccion = cambiar_direccion(
                            pygame.key.get_pressed(),
                                direccion
        )
                elif estado == ESTADO_PAUSA:

                    if evento.key == pygame.K_ESCAPE:
                        estado = ESTADO_JUGANDO
                        # parte 3: redibujar al volver de pausa para limpiar la pantalla
                        refrescar_tablero(screen, tablero, puntaje, combustible, sprite_jugador, sprite_caja, sprites_obstaculo, sprite_boost, sprite_gasolina, sprite_villano_actual, sprite_escudo, sprite_objeto, sprite_container, background, direccion, flash_color, mostrar_flash, mostrar_pop_puntaje, cola_posiciones, pos_jugador)
        
                
        if estado == ESTADO_JUGANDO:
            tiempo_actual = pygame.time.get_ticks()  # tiempo en milisegundos

            if not boost_activo:
                if tiempo_actual - tiempo_boost >= 5000:
                    aparecer_aleatorio(tablero, BOOST)
                    boost_activo = True
                    retraso = 200


            if ralentizado:
                if tiempo_actual - tiempo_ralentizado >= 5000:
                    ralentizado = False
                    retraso = 200


            # movemos a los villanos
            if tiempo_actual - tiempo_ultimo_mov_ladron >= RETRASO_LADRON:
                tiempo_ultimo_mov_ladron = tiempo_actual

                for indice_ladron in range(len(ladrones)):
                    ladrones[indice_ladron], atrapo = mover_ladron(tablero, ladrones[indice_ladron], pos_jugador)

                    # parte 12: habilidad de dash (salto extra) en niveles altos
                    if not atrapo and random.random() < PROB_DASH_POR_NIVEL[nivel_actual]:
                        ladrones[indice_ladron], atrapo = mover_ladron(tablero, ladrones[indice_ladron], pos_jugador)

                    if atrapo:
                        if escudo_activo:
                            escudo_activo = False
                            aparecer_aleatorio(tablero, ESCUDO)
                            sonido_escudo.play()
                            flash_color = (255, 255, 255)
                        else:
                            puntaje = max(0, puntaje - PUNTOS_ROBADOS_LADRON)
                            sonido_ladron.play()
                            flash_color = (200, 40, 40)

                            segmentos_deseados = min(puntaje, LIMITE_COLA)
                            cola_posiciones[:] = cola_posiciones[:segmentos_deseados]

                        mostrar_flash = True
                        refrescar_tablero(screen, tablero, puntaje, combustible, sprite_jugador, sprite_caja, sprites_obstaculo, sprite_boost, sprite_gasolina, sprite_villano_actual, sprite_escudo, sprite_objeto, sprite_container, background, direccion, flash_color, mostrar_flash, mostrar_pop_puntaje, cola_posiciones, pos_jugador)

                        if puntaje <= 0:
                            estado = ESTADO_DERROTA
                            sonido_choque.play()
                            mostrar_pantalla(screen, PANTALLA_DERROTA)
                            break  # ya perdiste, no seguimos moviendo al resto

                # parte 12: el jefe puede atacar a distancia si está alineado
                if nivel_actual == 3 and estado == ESTADO_JUGANDO:
                    for pos_boss in ladrones:
                        col_boss, fila_boss = pos_boss
                        col_jug, fila_jug = pos_jugador

                        alineado = (col_boss == col_jug) or (fila_boss == fila_jug)
                        distancia = abs(col_boss - col_jug) + abs(fila_boss - fila_jug)

                        if alineado and distancia <= RADIO_PULSO_BOSS and distancia > 0:
                            if tiempo_actual - tiempo_ultimo_pulso_boss >= COOLDOWN_PULSO_BOSS:
                                tiempo_ultimo_pulso_boss = tiempo_actual

                                if escudo_activo:
                                    escudo_activo = False
                                    aparecer_aleatorio(tablero, ESCUDO)
                                    sonido_escudo.play()
                                else:
                                    puntaje = max(0, puntaje - PUNTOS_PULSO_BOSS)
                                    sonido_ladron.play()

                                flash_color = (255, 60, 200)  # magenta, distinto al choque normal
                                mostrar_flash = True

                                # efecto visual del ataque del jefe (rayo simple)
                                pygame.draw.line(
                                    screen,
                                    "magenta",
                                    (col_boss * 40 + 20, fila_boss * 40 + 20),
                                    (col_jug * 40 + 20, fila_jug * 40 + 20),
                                    4,
                                )
                                pygame.display.update()

                                if puntaje <= 0:
                                    estado = ESTADO_DERROTA
                                    sonido_choque.play()
                                    mostrar_pantalla(screen, PANTALLA_DERROTA)
                                    break
            
            # el retraso controla la velocidad del jugador
            if direccion != (0, 0) and tiempo_actual - tiempo_ultimo_mov >= retraso and estado == ESTADO_JUGANDO:
                pos_jugador_anterior = pos_jugador  # parte 7
                resultado, pos_jugador = avanzar(tablero, pos_jugador, direccion, escudo_activo)

                # reiniciamos efectos (se activan solo si algo especial ocurre)
                mostrar_flash = False
                flash_color = None
                mostrar_pop_puntaje = False  # parte 4
                    

                if tiempo_actual - gasto >= 500:
                    combustible -= 1
                    gasto = tiempo_actual

                if combustible <= 0:
                    estado = ESTADO_DERROTA
                    mostrar_pantalla(screen, PANTALLA_DERROTA)

                # leo= sumamos puntaje
                # david= sonido al recoger caja, flash visual y velocidad aumenta cada 10 cajas
                if resultado == "manzana":
                    puntaje += 1
                    sonido_caja.play()  # sonido al recoger
                    mostrar_flash = True
                    flash_color = (60, 220, 90)  # verde
                    mostrar_pop_puntaje = True  # parte 4
                    # david= cada 10 cajas, el camión acelera
                    if puntaje % 10 == 0 and retraso > 80:
                        retraso -= 15

                    # parte 10: al alcanzar la meta, subes de nivel
                    if puntaje >= METAS_NIVEL[nivel_actual]:
                        if nivel_actual < NIVEL_MAXIMO:
                            nivel_actual += 1
                            RETRASO_LADRON = RETRASO_LADRON_POR_NIVEL[nivel_actual]
                            sprite_villano_actual = sprites_ladron_nivel[nivel_actual]
                            background = backgrounds_por_nivel[nivel_actual]  # parte 11

                            pantalla_transicion = PANTALLA_NIVEL2 if nivel_actual == 2 else PANTALLA_NIVEL3
                            mostrar_pantalla(screen, pantalla_transicion)
                            pygame.time.wait(1800)  # tiempo para leer el anuncio

                            tablero, pos_jugador, ladrones = reiniciar(nivel_actual)
                            direccion = (0, 0)
                            cola_posiciones = []  # cola limpia al cambiar de nivel
                            tiempo_ultimo_mov = pygame.time.get_ticks()
                            tiempo_ultimo_mov_ladron = pygame.time.get_ticks()
                            continue
                        else:
                            estado = ESTADO_VICTORIA
                            mostrar_pantalla(screen, PANTALLA_VICTORIA)
                            continue

                if resultado == "boost":
                    boost_activo = False
                    tiempo_boost = pygame.time.get_ticks()
                    retraso = 130
                    sonido_boost.play()  # sonido del turbo
                    mostrar_flash = True
                    flash_color = (80, 180, 255)  # cyan

                if resultado == "gasolina":
                    combustible += 25            
                    if combustible > 100:
                        combustible = 100
                    aparecer_aleatorio(tablero, GASOLINA)
                    sonido_gasolina.play()  # sonido al repostar
                    mostrar_flash = True
                    flash_color = (255, 150, 60)  # naranja

                if resultado == "objeto":
                    ralentizado = True
                    tiempo_ralentizado = pygame.time.get_ticks()
                    retraso = 400


                # parte 3: recoger escudo lo guarda para uso futuro
                if resultado == "escudo":
                    escudo_activo = True
                    sonido_escudo.play()  # sonido al recoger
                    mostrar_flash = True
                    flash_color = (80, 120, 255)  # azul

                # parte 3: el escudo absorbe un golpe
                if resultado == "escudo_usado":
                    escudo_activo = False
                    sonido_escudo.play()  # sonido al usar
                    aparecer_aleatorio(tablero, ESCUDO)  # nuevo escudo aparece
                    mostrar_flash = True
                    flash_color = (255, 255, 255)  # blanco

                # parte 7: golpear al ladrón directamente
                if resultado == "ladron_choque":
                    puntaje = max(0, puntaje - PUNTOS_ROBADOS_LADRON)
                    sonido_ladron.play()
                    mostrar_flash = True
                    flash_color = (200, 40, 40)

                    segmentos_deseados = min(puntaje, LIMITE_COLA)
                    cola_posiciones[:] = cola_posiciones[:segmentos_deseados]

                    if puntaje <= 0:
                        resultado = "derrota"

                if resultado == "derrota":
                    estado = ESTADO_DERROTA
                    sonido_choque.play()  # sonido de choque
                    mostrar_pantalla(screen, PANTALLA_DERROTA)
                elif resultado == "victoria":
                    estado = ESTADO_VICTORIA
                    mostrar_pantalla(screen, PANTALLA_VICTORIA)
                else:
                    tiempo_ultimo_mov = tiempo_actual

                    # PARTE 7: actualiza la cola tipo Snake
                    if pos_jugador != pos_jugador_anterior:
                        cola_posiciones.insert(0, pos_jugador_anterior)
                    segmentos_deseados = min(puntaje, LIMITE_COLA)
                    cola_posiciones[:] = cola_posiciones[:segmentos_deseados]

                    refrescar_tablero(screen, tablero, puntaje, combustible, sprite_jugador, sprite_caja, sprites_obstaculo, sprite_boost, sprite_gasolina, sprite_villano_actual, sprite_escudo, sprite_objeto, sprite_container, background, direccion, flash_color, mostrar_flash, mostrar_pop_puntaje, cola_posiciones, pos_jugador)

    # cerramos pygame
    pygame.quit()


if __name__ == "__main__":
    main()

