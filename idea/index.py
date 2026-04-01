import time
import random
from questions import R1_QUESTIONS, R2_QUESTIONS, R3_QUESTIONS

# Player class
class Player:
    def __init__(self, color, name="Player"):
        self.color = color
        self.name = name
        self.score = 0

    def __str__(self):
        return f"{self.color} {self.name} (Score: {self.score})"

# Game class
class KaustubhGame:
    def __init__(self):
        self.players = [
            Player("🔴 Red", "Player 1"),
            Player("🔵 Blue", "Player 2"),
            Player("🟢 Green", "Player 3")
        ]

    def rename_players(self):
        for player in self.players:
            new_name = input(f"{player.color}, enter your name (default {player.name}): ")
            if new_name.strip():
                player.name = new_name

    def display_board(self, answers, revealed):
        print("\nAnswer Board:")
        for i, ans in enumerate(answers):
            if i in revealed:
                print(f"{i+1}. {ans} - {revealed[i]}")
            else:
                print(f"{i+1}. [Covered]")

    def round1(self, question, answers):
        print("\n--- ROUND 1 ---")
        print(f"Question: {question}")
        revealed = {}
        for _ in range(3):  # 3 turns each
            for player in self.players:
                self.display_board(answers, revealed)
                guess = input(f"{player.color} {player.name}, enter your guess: ").strip().lower()
                if guess in [a.lower() for a in answers]:
                    idx = [a.lower() for a in answers].index(guess)
                    if idx not in revealed:
                        revealed[idx] = player.color
                        player.score += 10
                        print(f"Correct! {answers[idx]} revealed for {player.color}")
                    else:
                        print("Already claimed!")
                else:
                    print("Wrong guess.")
        # Reveal remaining
        for i in range(len(answers)):
            if i not in revealed:
                revealed[i] = "Grey"
        self.display_board(answers, revealed)

    def round2(self, questions):
        print("\n--- ROUND 2 ---")
        # Order based on scores (lowest first)
        order = sorted(self.players, key=lambda p: p.score)

        available_questions = questions[:]  # copy list

        for i, player in enumerate(order):
            print(f"\n{player.color} {player.name}, it's your turn!")

            # Show available questions
            for idx, (q, answers) in enumerate(available_questions):
                print(f"{idx+1}. {q}")

            # If only one question left, auto-assign
            if len(available_questions) == 1:
                chosen_q, chosen_answers = available_questions.pop(0)
                print(f"{player.color} {player.name} automatically gets: {chosen_q}")
            else:
                choice = int(input(f"Choose a question (1-{len(available_questions)}): "))
                chosen_q, chosen_answers = available_questions.pop(choice-1)

            print(f"\nQuestion: {chosen_q}")
            revealed = {}

            # Player has 50 seconds to recall answers
            start = time.time()
            while time.time() - start < 50:
                guess = input("Enter answer (or press Enter to stop): ").strip().lower()
                if not guess:
                    break
                if guess in [a.lower() for a in chosen_answers]:
                    idx = [a.lower() for a in chosen_answers].index(guess)
                    if idx not in revealed:
                        revealed[idx] = player.color
                        player.score += 15
                        print(f"Correct! {chosen_answers[idx]} revealed for {player.color}")
                    else:
                        print("Already claimed!")

            # Reveal remaining
            for i in range(len(chosen_answers)):
                if i not in revealed:
                    revealed[i] = "Grey"

            print("\nFinal Board for this question:")
            for i, ans in enumerate(chosen_answers):
                print(f"{ans} - {revealed[i]}")

    def round3(self, question, answers):
        print("\n--- ROUND 3 ---")
        print(f"Question: {question}")
        revealed = {}
        while len(revealed) < len(answers):
            for player in self.players:
                guess = input(f"{player.color} {player.name}, enter your guess: ").strip().lower()
                if guess in [a.lower() for a in answers]:
                    idx = [a.lower() for a in answers].index(guess)
                    if idx not in revealed:
                        revealed[idx] = player.color
                        player.score += 10
                        print(f"Correct! {answers[idx]} revealed for {player.color}")
                        if len(revealed) == len(answers):
                            player.score += 50
                            print(f"{player.color} {player.name} claimed the final answer! +50 bonus")
                            break
        # Reveal board
        self.display_board(answers, revealed)

    def show_scores(self):
        print("\n--- FINAL SCORES ---")
        for player in self.players:
            print(f"{player.color} {player.name}: {player.score} points")
        winner = max(self.players, key=lambda p: p.score)
        print(f"\n🏆 Winner: {winner.color} {winner.name} with {winner.score} points!")

# Example run
game = KaustubhGame()
game.rename_players()

# Round 1 example
r1_q = random.choice(R1_QUESTIONS)
game.round1(r1_q["q"], r1_q["a"])

# Round 2 example
# Pick 3 random questions for the round
r2_pool = random.sample(R2_QUESTIONS, 3)
questions = [(q["q"], q["a"]) for q in r2_pool]
game.round2(questions)

# Round 3 example
r3_q = random.choice(R3_QUESTIONS)
game.round3(r3_q["q"], r3_q["a"])

game.show_scores()
