import pygame
import json
import random
import sys
import time
import pyttsx3

# Initialize pygame and TTS
pygame.init()
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Improve Your English")
engine = pyttsx3.init()
engine.setProperty('volume', 1.0)
engine.setProperty('rate', 150)

# Colors and fonts
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
answerInputFont = pygame.font.Font('fonts/NotoSansTC-Regular.ttf', 32)
questionFont = pygame.font.Font('fonts/NotoSansTC-Regular.ttf', 32)
partOfSpeechFont = pygame.font.Font(None, 28)

# Scenes and selection
current_scene = "home" # home, quiz, vocab
selected_level = None
selected_count = None

# Globals for quiz
vocabularies = []
shuffled_vocab = []
current_index = 0
current_question = {}

class VocabView:
    def __init__(self, order: int, word: str, partOfSpeech: str, translation):
        self.order = order
        self.word = word
        self.partOfSpeech = partOfSpeech
        self.translation = translation
        self.width = 500
        self.height = 50
        self.spacing = 10
        self.rect = pygame.Rect(screen_width/2 - self.width/2, self.height*(self.order)+self.spacing*(self.order+1), self.width, self.height)
        self.txt_surface = answerInputFont.render(self.word+' '*10+self.partOfSpeech+' '*10+self.translation, True, BLACK)
    
    def draw(self):
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 1)
        screen.blit(self.txt_surface, self.rect)
        
# Button class
class Button:
    def __init__(self, x, y, w, h, text, bg_color, bg_color_triggered, text_color, text_color_triggered, click_time, callback):
        self.rect = pygame.Rect(x - w // 2, y - h // 2, w, h)
        self.text = text
        self.bg_color = bg_color
        self.bg_color_triggered = bg_color_triggered
        self.text_color = text_color
        self.text_color_triggered = text_color_triggered
        self.click_time = click_time
        self.callback = callback
        self.isTriggered = False
        self.trigger_start = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.isTriggered = True
            self.trigger_start = time.time()

    def update(self):
        if self.isTriggered and time.time() - self.trigger_start >= self.click_time:
            self.isTriggered = False
            self.callback()

    def draw(self, screen):
        color = self.bg_color_triggered if self.isTriggered else self.bg_color
        text_color = self.text_color_triggered if self.isTriggered else self.text_color
        pygame.draw.rect(screen, color, self.rect)
        text_surface = questionFont.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

# Load vocabularies
def load_json_to_list(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return json.load(file)

def get_next_question():
    global current_index, shuffled_vocab
    if current_index > len(shuffled_vocab):
        current_index = 0
        random.shuffle(shuffled_vocab)
    vocab = shuffled_vocab[current_index]
    current_index += 1
    return {
        'word': vocab['word'],
        'translation': vocab['definitions'][0]['text'],
        'partOfSpeech': vocab['definitions'][0]['partOfSpeech'],
        'letterCount': vocab['letterCount']
    }

def play_voice(word):
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[0].id)
    engine.say(word)
    engine.runAndWait()

class QuestionText:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x - w // 2, y - h // 2, w, h)
        self.update_text('', '')

    def update_text(self, text, part):
        self.text = text
        self.partOfSpeech = part
        self.txt_surface = questionFont.render(self.text, True, BLACK)
        self.part_surface = partOfSpeechFont.render(self.partOfSpeech, True, BLACK)
        cx, cy = self.rect.center
        self.text_rect = self.txt_surface.get_rect(center=(cx, cy))
        self.part_rect = self.part_surface.get_rect(center=(cx, cy + 40))

    def draw(self, screen):
        screen.blit(self.txt_surface, self.text_rect)
        screen.blit(self.part_surface, self.part_rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)

class InputBox:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x - w // 2, y - h // 2, w, h)
        self.color_inactive = pygame.Color('gray')
        self.color_active = pygame.Color('dodgerblue2')
        self.color = self.color_inactive
        self.text = ''
        self.txt_surface = answerInputFont.render(self.text, True, self.color)
        self.active = False

    def clear_text(self):
        self.text = ''
        self.txt_surface = answerInputFont.render(self.text, True, self.color)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.color = self.color_active if self.active else self.color_inactive
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                answer = self.text.strip()
                self.clear_text()
                return answer
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode
            self.txt_surface = answerInputFont.render(self.text, True, self.color)

    def draw(self, screen):
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
        pygame.draw.rect(screen, self.color, self.rect, 2)

# Quiz UI
questiontext = QuestionText(screen_width / 2, screen_height / 2 - 200, 500, 50)
inputbox = InputBox(screen_width / 2, screen_height / 2, 200, 50)

def create_voice_button():
    return Button(screen_width / 2, screen_height / 2 + 80, 100, 50, 'voice', (0,138,172), (137,214,255), BLACK, BLACK, 1,
                  lambda: play_voice(current_question['word']))

def next_question():
    global current_question, voice_button
    current_question = get_next_question()
    questiontext.update_text(current_question['translation'], current_question['partOfSpeech'])
    voice_button = create_voice_button()
    inputbox.clear_text()

# Home scene logic
def set_count(n):
    global selected_count
    selected_count = n

def set_level(level):
    global selected_level
    selected_level = level

def start_quiz():
    global current_scene, vocabularies, shuffled_vocab, current_index, vocab_view
    if selected_count and selected_level:
        filename = f"vocabularies/level{selected_level}.json"
        vocabularies = load_json_to_list(filename)
        random.shuffle(vocabularies)
        shuffled_vocab = shuffled_vocab[:selected_count]
        current_index = 0
        next_question()
        current_scene = "quiz"

def show_vocab():
    global current_scene
    current_scene = "vocab"

count_buttons = [
    Button(250 + i * 100, 250, 80, 40, f"{n}", (200, 200, 200), (150, 150, 150), BLACK, WHITE, 0.2, lambda n=n: set_count(n))
    for i, n in enumerate([10, 20, 30])
]

level_buttons = [
    Button(200 + i * 80, 320, 60, 40, f"L{i+1}", (180, 200, 250), (100, 150, 255), BLACK, WHITE, 0.2, lambda i=i: set_level(i + 1))
    for i in range(6)
]

start_quiz_button = Button(screen_width//2, 400, 200, 60, "開始測驗", (100, 180, 100), (50, 150, 50), BLACK, WHITE, 0.2, start_quiz)
view_vocab_button = Button(screen_width//2, 470, 200, 50, "查看單字表", (200, 160, 0), (255, 200, 0), BLACK, WHITE, 0.2, show_vocab)

vocab_views = []
for i in range(5):
    vocab_view = VocabView(i, 'hit', 'v.', '打')
    vocab_views.append(vocab_view)

# Game state
voice_button = create_voice_button()
next_question_button = Button(screen_width / 2 + 120, screen_height / 2 + 80, 100, 50, 'Next', (0,138,172), (137,214,255), BLACK, BLACK, 1, next_question)
feedback_mode = False
feedback_start_time = 0
feedback_duration = 2
correct = False

# Main loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if current_scene == "home":
            for btn in count_buttons + level_buttons + [start_quiz_button, view_vocab_button]:
                btn.handle_event(event)
        elif current_scene == "quiz":
            if not feedback_mode:
                answer = inputbox.handle_event(event)
                voice_button.handle_event(event)
                next_question_button.handle_event(event)
                if answer:
                    feedback_mode = True
                    feedback_start_time = time.time()
                    correct = answer.lower() == current_question['word'].lower()
                    feedback_text = '答對了' if correct else '答錯了'
                    questiontext.update_text(feedback_text, current_question['partOfSpeech'])

    screen.fill(WHITE)

    if current_scene == "home":
        title = questionFont.render("Improve Your English", True, BLACK)
        screen.blit(title, (screen_width//2 - title.get_width()//2, 100))
        info = answerInputFont.render("請選擇題數與等級", True, BLACK)
        screen.blit(info, (screen_width//2 - info.get_width()//2, 160))
        for btn in count_buttons + level_buttons + [start_quiz_button, view_vocab_button]:
            btn.update()
            btn.draw(screen)
        status = answerInputFont.render(f"選擇：{selected_count or '_'} 題, Level {selected_level or '_'}", True, BLACK)
        screen.blit(status, (screen_width//2 - status.get_width()//2, 540))

    elif current_scene == "quiz":
        if feedback_mode:
            if time.time() - feedback_start_time >= feedback_duration:
                feedback_mode = False
                if correct:
                    next_question()
                else:
                    questiontext.update_text(current_question['translation'], current_question['partOfSpeech'])
        inputbox.draw(screen)
        voice_button.update()
        voice_button.draw(screen)
        next_question_button.update()
        next_question_button.draw(screen)
        questiontext.draw(screen)
    
    elif current_scene == 'vocab':
        for i in range(5):            
            vocab_views[i].draw()

    pygame.display.flip()
