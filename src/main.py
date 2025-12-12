import pygame
import math
import numpy as np
import skfuzzy as fuzz
import pygad
import cv2
import csv
import datetime
import os

# ==========================================
# CONFIGURAÇÕES GERAIS
# ==========================================
CONFIG = {
    'WIDTH': 1000,
    'HEIGHT': 700,
    'FPS': 0,  # 0 para velocidade máxima
    'CAR_SCALE': 1.5,  # Escala visual do carro
    'SENSOR_RANGE': 100,  # Alcance dos sensores
    'MAX_FRAMES': 2000,  # Tempo limite por geração
    'TRACK_WIDTH': 100,


    'POPULATION_SIZE': 20,
    'PARENTS_MATING': 6,
    'ELITISM_COUNT': 2,
    'TOURNAMENT_K': 2,
    # --------------------------------------

    'CONVERGENCE_TARGET': 0.95,

    # Parâmetros de Mutação (Recozimento Simulado)
    'INITIAL_MUTATION': 25.0,
    'MIN_MUTATION': 1.0,
    'COOLING_RATE': 0.995,

    'RECORD_VIDEO': False,
    'VIDEO_FILENAME': 'video.mp4',
    'REPORT_FILE': 'relatorio.txt',
    'CSV_FILE': 'dados.csv'
}

COLORS = {
    'WHITE': (255, 255, 255), 'BLACK': (0, 0, 0), 'RED': (255, 0, 0),
    'GREEN': (0, 255, 0), 'BLUE': (0, 0, 255), 'GOLD': (255, 215, 0),
    'DARK_RED': (180, 0, 0), 'GREY': (50, 50, 50), 'TIRE': (30, 30, 30),
    'COCKPIT': (100, 100, 150)
}

TRACK_POINTS = [
    (150, 150), (500, 80), (850, 150),
    (920, 350), (850, 550), (500, 620),
    (150, 550), (200, 350)
]

FUZZY_UNIVERSE = np.arange(0, 101, 1)
STEERING_OPTIONS = [-45, -25, 0, 25, 45]

# Definição das funções de pertinência Fuzzy
fuzz_vc = fuzz.trimf(FUZZY_UNIVERSE, [0, 0, 25])
fuzz_c = fuzz.trimf(FUZZY_UNIVERSE, [0, 25, 50])
fuzz_m = fuzz.trimf(FUZZY_UNIVERSE, [25, 50, 75])
fuzz_f = fuzz.trimf(FUZZY_UNIVERSE, [50, 75, 100])
fuzz_vf = fuzz.trimf(FUZZY_UNIVERSE, [75, 100, 100])


def get_sensor_membership(distance):
    val = np.clip(distance, 0, 100)
    return [
        fuzz.interp_membership(FUZZY_UNIVERSE, fuzz_vc, val),
        fuzz.interp_membership(FUZZY_UNIVERSE, fuzz_c, val),
        fuzz.interp_membership(FUZZY_UNIVERSE, fuzz_m, val),
        fuzz.interp_membership(FUZZY_UNIVERSE, fuzz_f, val),
        fuzz.interp_membership(FUZZY_UNIVERSE, fuzz_vf, val)
    ]


class RaceCar:
    def __init__(self, genome):
        self.genome = genome

        base_w, base_h = 24, 12
        w = int(base_w * CONFIG['CAR_SCALE'])
        h = int(base_h * CONFIG['CAR_SCALE'])

        self.image = pygame.Surface((w, h), pygame.SRCALPHA)

        # Desenho do carro
        body_points = [(0, h * 0.2), (w * 0.6, 0), (w, h * 0.3), (w, h * 0.7), (w * 0.6, h), (0, h * 0.8)]
        pygame.draw.polygon(self.image, COLORS['RED'], body_points)
        nose_points = [(w * 0.7, h * 0.15), (w, h * 0.3), (w, h * 0.7), (w * 0.7, h * 0.85)]
        pygame.draw.polygon(self.image, COLORS['DARK_RED'], nose_points)
        pygame.draw.ellipse(self.image, COLORS['COCKPIT'], (w * 0.35, h * 0.25, w * 0.25, h * 0.5))
        pygame.draw.rect(self.image, COLORS['DARK_RED'], (0, 0, w * 0.2, h))

        tire_w, tire_h = w * 0.15, h * 0.2
        for tx, ty in [(w * 0.1, -1), (w * 0.1, h - tire_h + 1), (w * 0.7, 0), (w * 0.7, h - tire_h + 1)]:
            pygame.draw.rect(self.image, COLORS['TIRE'], (tx, ty, tire_w, tire_h))

        self.original_image = self.image
        self.position = pygame.math.Vector2(TRACK_POINTS[0])
        self.angle = -10
        self.speed = 6
        self.is_alive = True
        self.has_crashed = False
        self.has_finished = False
        self.time_alive = 0
        self.distance_traveled = 0
        self.sensor_data = []
        self.sensor_readings = []
        self.center_map = pygame.math.Vector2(CONFIG['WIDTH'] // 2, CONFIG['HEIGHT'] // 2)
        self.total_radians = 0.0
        self.last_angle_rad = self._get_angle_to_center()

        # === CONTROLE ANTI-SPIN (ANTI-ZERINHO) ===
        self.spin_accumulator = 0  # Acumula graus virados
        self.distance_at_last_spin = 0  # Distância quando começou a contar o giro

    def _get_angle_to_center(self):
        dx = self.position.x - self.center_map.x
        dy = self.position.y - self.center_map.y
        return math.atan2(dy, dx)

    def draw(self, surface):
        rotated = pygame.transform.rotate(self.original_image, -self.angle)
        rect = rotated.get_rect(center=self.position)
        if self.is_alive:
            surface.blit(rotated, rect.topleft)
            if self.has_finished:
                pygame.draw.rect(surface, COLORS['GOLD'], rect.inflate(4, 4), 2)
            else:
                self._draw_sensors(surface)

    def _draw_sensors(self, surface):
        offset = 10 * CONFIG['CAR_SCALE']
        origin = self.position + pygame.math.Vector2(math.cos(math.radians(-self.angle)),
                                                     math.sin(math.radians(-self.angle))) * offset
        for dist, point in self.sensor_data:
            color = COLORS['GREEN'] if dist > 20 else (255, 100, 0)
            pygame.draw.line(surface, color, origin, point, 1)

    def cast_ray(self, angle_offset, track_mask):
        length = 0
        offset = 10 * CONFIG['CAR_SCALE']
        origin = self.position + pygame.math.Vector2(math.cos(math.radians(-self.angle)),
                                                     math.sin(math.radians(-self.angle))) * offset
        sx, sy = origin

        while length < CONFIG['SENSOR_RANGE']:
            length += 5
            rad = math.radians(360 - (self.angle + angle_offset))
            tx = int(sx + math.cos(rad) * length)
            ty = int(sy + math.sin(rad) * length)

            if not (0 <= tx < CONFIG['WIDTH'] and 0 <= ty < CONFIG['HEIGHT']): return length, (tx, ty)
            try:
                if track_mask.get_at((tx, ty)) == COLORS['BLACK']: return length, (tx, ty)
            except IndexError:
                return length, (tx, ty)
        return length, (int(sx + math.cos(rad) * length), int(sy + math.sin(rad) * length))

    def update_lap_progress(self):
        current_rad = self._get_angle_to_center()
        diff = current_rad - self.last_angle_rad

        if diff < -math.pi:
            diff += 2 * math.pi
        elif diff > math.pi:
            diff -= 2 * math.pi

        self.total_radians += diff
        self.last_angle_rad = current_rad

        # Regra: Matar se andar na contramão (voltar atrás da largada)
        if self.total_radians < -0.2:
            self.is_alive = False
            self.has_crashed = True
            self.total_radians = -5  # Penalidade forte
            return

        if self.total_radians >= 12.50:
            self.has_finished = True
            self.is_alive = False

    def decide_steering(self):
        force = 0
        total = 0
        mfs = [get_sensor_membership(val) for val in self.sensor_readings]
        g_idx = 0
        for s_idx in range(5):
            for l_idx in range(5):
                act = mfs[s_idx][l_idx]
                if act > 0.05:
                    gene = int(self.genome[g_idx]) % len(STEERING_OPTIONS)
                    force += STEERING_OPTIONS[gene] * act
                    total += act
                g_idx += 1
        return force / total if total > 0 else 0

    def update(self, track_mask):
        if not self.is_alive: return
        self.time_alive += 1

        # 1. Sensores
        angles = [-60, -30, 0, 30, 60]
        self.sensor_data = []
        self.sensor_readings = []
        for ang in angles:
            dist, pt = self.cast_ray(ang, track_mask)
            self.sensor_data.append((dist, pt))
            self.sensor_readings.append(min(100, (dist / CONFIG['SENSOR_RANGE']) * 100))

        # 2. Verifica Colisão
        if any(r < 5 for r in self.sensor_readings):
            self.is_alive = False
            self.has_crashed = True
            self.has_finished = False
            return

        # 3. Atualiza Progresso e Verifica Contramão
        self.update_lap_progress()
        if self.has_finished: return

        # 4. Calcula Steering e Move
        steering = self.decide_steering()
        self.angle += steering

        # === VERIFICAÇÃO ANTI-SPIN (ELIMINA CARROS QUE FICAM GIRANDO) ===
        self.spin_accumulator += steering

        # Se acumulou giro de 360 graus (para qualquer lado)
        if abs(self.spin_accumulator) >= 360:
            distance_covered = self.distance_traveled - self.distance_at_last_spin

            # Se girou 360 mas andou pouco (menos de 400px), é zerinho.
            if distance_covered < 400:
                self.is_alive = False
                self.has_crashed = True
                self.total_radians = -2  # Zera ou negativiza o fitness

            # Reseta contadores
            self.spin_accumulator = 0
            self.distance_at_last_spin = self.distance_traveled
        # ==============================================================

        rad = math.radians(360 - self.angle)
        self.position.x += math.cos(rad) * self.speed
        self.position.y += math.sin(rad) * self.speed
        self.distance_traveled += self.speed


def create_track_surface():
    s = pygame.Surface((CONFIG['WIDTH'], CONFIG['HEIGHT']))
    s.fill(COLORS['BLACK'])
    if len(TRACK_POINTS) > 1:
        pygame.draw.lines(s, COLORS['WHITE'], True, TRACK_POINTS, CONFIG['TRACK_WIDTH'] + 10)
    for p in TRACK_POINTS:
        pygame.draw.circle(s, COLORS['WHITE'], p, (CONFIG['TRACK_WIDTH'] + 10) // 2)
    pygame.draw.circle(s, COLORS['GREEN'], TRACK_POINTS[0], 10)
    return s


def calculate_fitness_scores(cars, max_time):
    scores = []
    any_finished = any(c.has_finished for c in cars)

    for car in cars:
        score = 0
        if car.has_finished:
            score = 100000 + (max_time - car.time_alive)
        else:
            if any_finished and car.has_crashed:
                score = 0
            else:
                # O fitness principal é o progresso angular (voltas na pista)
                score = car.total_radians * 1000
                # Se o carro for pego andando pra trás (total_radians negativo), score é 0
                if score < 0: score = 0

        scores.append(score)
    return scores


def save_final_report(stats_history, events_log, total_time_str, run_id):
    try:
        with open(CONFIG['CSV_FILE'], mode='w', newline='', encoding='utf-8-sig') as file:
            writer = csv.writer(file)
            writer.writerow(['Geracao', 'Melhor_Fitness', 'Media_Fitness', 'Vencedores', 'Taxa_Mutacao'])
            writer.writerows(stats_history)
        print(f"CSV salvo em: {CONFIG['CSV_FILE']}")
    except Exception as e:
        print(f"Erro ao salvar CSV: {e}")

    try:
        with open(CONFIG['REPORT_FILE'], 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write(f"RELATÓRIO TÉCNICO - {run_id}\n")
            f.write("=" * 60 + "\n\n")

            f.write("1. PARÂMETROS:\n")
            f.write(f"- População: {CONFIG['POPULATION_SIZE']}\n")
            f.write(f"- Convergência Alvo: {CONFIG['CONVERGENCE_TARGET'] * 100}%\n\n")

            best_fits = [row[1] for row in stats_history]
            avg_fits = [row[2] for row in stats_history]
            winners = [row[3] for row in stats_history]

            f.write("2. RESULTADOS:\n")
            f.write(f"- Duração: {total_time_str}\n")
            f.write(f"- Gerações: {len(stats_history)}\n")
            f.write(f"- Maior Fitness: {max(best_fits):.2f}\n")
            f.write(f"- Vencedores Máx: {max(winners)}\n\n")

            f.write("3. EVENTOS:\n")
            for event in events_log:
                f.write(f"- {event}\n")
            f.write("\n" + "=" * 60)
        print(f"Relatório salvo em: {CONFIG['REPORT_FILE']}")
    except Exception as e:
        print(f"Erro ao salvar Relatório: {e}")


def pygad_fitness_func(ga_instance, solution, solution_idx):
    return 0


def main():
    output_dir = "relatorios"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    run_id = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    print(f"Iniciando Experimento: {run_id}")

    CONFIG['VIDEO_FILENAME'] = os.path.join(output_dir, f"video_{run_id}.mp4")
    CONFIG['REPORT_FILE'] = os.path.join(output_dir, f"relatorio_{run_id}.txt")
    CONFIG['CSV_FILE'] = os.path.join(output_dir, f"dados_{run_id}.csv")

    pygame.init()
    screen = pygame.display.set_mode((CONFIG['WIDTH'], CONFIG['HEIGHT']))
    pygame.display.set_caption(f"Fuzzy AI (Pop: {CONFIG['POPULATION_SIZE']})")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 18)
    track_surface = create_track_surface()

    video_writer = None
    if CONFIG['RECORD_VIDEO']:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(CONFIG['VIDEO_FILENAME'], fourcc, 30.0, (CONFIG['WIDTH'], CONFIG['HEIGHT']))

    stats_history = []
    events_log = []
    start_time_real = datetime.datetime.now()
    first_win_recorded = False

    ga = pygad.GA(
        num_generations=1000,
        fitness_func=pygad_fitness_func,
        sol_per_pop=CONFIG['POPULATION_SIZE'],
        num_genes=25,
        init_range_low=0,
        init_range_high=4,
        mutation_percent_genes=int(CONFIG['INITIAL_MUTATION']),
        gene_type=int,
        num_parents_mating=CONFIG['PARENTS_MATING'],
        keep_parents=CONFIG['ELITISM_COUNT'],
        parent_selection_type="tournament",
        K_tournament=CONFIG['TOURNAMENT_K'],
    )

    generation_id = 1
    running = True

    try:
        while running:
            population_genomes = ga.population
            cars = [RaceCar(genome) for genome in population_genomes]
            frame_counter = 0
            simulating_generation = True

            while simulating_generation:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        simulating_generation = False

                screen.blit(track_surface, (0, 0))
                active_cars = 0
                finished_cars = 0

                for car in cars:
                    car.update(track_surface)
                    car.draw(screen)
                    if car.is_alive or car.has_finished: active_cars += 1
                    if car.has_finished: finished_cars += 1

                info_text = f"Gen: {generation_id} | Vivos: {active_cars}/{CONFIG['POPULATION_SIZE']} | Wins: {finished_cars} | mutação: {ga.mutation_percent_genes}%"
                screen.blit(font.render(info_text, True, COLORS['BLUE']), (20, 20))

                if CONFIG['RECORD_VIDEO'] and video_writer:
                    view = pygame.surfarray.array3d(screen).transpose([1, 0, 2])
                    frame = cv2.cvtColor(view, cv2.COLOR_RGB2BGR)
                    video_writer.write(frame)

                pygame.display.flip()
                clock.tick(CONFIG['FPS'])
                frame_counter += 1

                if active_cars == 0 or frame_counter >= CONFIG['MAX_FRAMES']:
                    simulating_generation = False
                if not running: break

            if not running: break

            fitness_results = calculate_fitness_scores(cars, CONFIG['MAX_FRAMES'])
            best_fitness = max(fitness_results)
            avg_fitness = np.mean(fitness_results)
            convergence_rate = finished_cars / CONFIG['POPULATION_SIZE']
            current_mutation = ga.mutation_percent_genes

            stats_history.append(
                [generation_id, round(best_fitness, 2), round(avg_fitness, 2), finished_cars, current_mutation])

            if finished_cars > 0 and not first_win_recorded:
                events_log.append(f"Gen {generation_id}: PRIMEIRO VENCEDOR! (Fit: {best_fitness:.2f})")
                first_win_recorded = True

            print(f"Gen {generation_id} | Best: {best_fitness:.0f} | Wins: {finished_cars}")

            if convergence_rate >= CONFIG['CONVERGENCE_TARGET']:
                events_log.append(f"Gen {generation_id}: CONVERGÊNCIA ATINGIDA!")
                print(">>> Convergência atingida.")
                running = False

            # Mutação Adaptativa
            new_mutation_rate = CONFIG['INITIAL_MUTATION'] * (CONFIG['COOLING_RATE'] ** generation_id)
            if new_mutation_rate < CONFIG['MIN_MUTATION']: new_mutation_rate = CONFIG['MIN_MUTATION']
            if finished_cars > (CONFIG['POPULATION_SIZE'] * 0.5): new_mutation_rate = max(1.0, new_mutation_rate / 2)
            ga.mutation_percent_genes = int(new_mutation_rate)

            ga.pop_fitness = np.array(fitness_results)
            parents, _ = ga.select_parents(ga.pop_fitness, ga.num_parents_mating)
            offspring_needed = (ga.sol_per_pop - parents.shape[0], ga.num_genes)
            offspring_cross = ga.crossover(parents, offspring_needed)
            offspring_mut = ga.mutation(offspring_cross)
            ga.population[0:parents.shape[0], :] = parents
            ga.population[parents.shape[0]:, :] = offspring_mut

            generation_id += 1

    finally:
        print("\nFinalizando...")
        end_time = datetime.datetime.now()
        duration = end_time - start_time_real
        save_final_report(stats_history, events_log, str(duration), run_id)
        if video_writer: video_writer.release()
        pygame.quit()


if __name__ == "__main__":
    main()
