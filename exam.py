import sys
import re
import os
import argparse
from typing import List, Dict, Tuple


class ExamParser:
    @staticmethod
    def parse_exam(file_path: str) -> List[Dict[str, str]]:
        """
        Parse a markdown exam file and extract questions and answers.

        Args:
            file_path (str): Path to the markdown exam file

        Returns:
            List of dictionaries containing question details
        """
        try:
            with open(file_path, 'r') as file:
                content = file.read()
        except IOError:
            print(f"Error: Cannot read file {file_path}")
            sys.exit(1)

        # Remove layout and title section
        content = re.sub(r'^---\n.*?---\n', '', content, flags=re.DOTALL)
        content = re.sub(r'# .*\n', '', content)

        # Split questions
        questions_raw = re.split(r'\n\d+\.\s', content)[1:]

        parsed_questions = []
        for q_text in questions_raw:
            # Extract question text before options
            match = re.match(
                r'(.*?)\n((?:    - [A-E]\.\s.*\n)+)', q_text, re.DOTALL)
            if not match:
                continue

            question = match.group(1).strip()
            options_text = match.group(2)

            # Extract options
            options = {}
            for opt_match in re.finditer(r'    - ([A-E])\.\s(.*?)(?=\n    -|\n\n|$)', options_text, re.DOTALL):
                letter = opt_match.group(1)
                option_text = opt_match.group(2).strip()
                options[letter] = option_text

            # Extract correct answer(s)
            answer_match = re.search(
                r'Correct answer:\s*([A-E](?:, [A-E])*)', q_text)

            # Default to empty list if no answer found
            correct_answers = answer_match.group(
                1).split(', ') if answer_match else []

            # Validate correct answers exist in options
            correct_answers = [
                ans for ans in correct_answers if ans in options.keys()]

            # Skip question if no valid answers
            if not correct_answers:
                print(
                    f"Warning: No valid answers found for question: {question}")
                continue

            parsed_questions.append({
                'question': question,
                'options': options,
                'correct_answer': correct_answers
            })

        return parsed_questions


class ExamTaker:
    @staticmethod
    def take_exam(questions: List[Dict[str, str]]) -> Tuple[int, int]:
        """
        Conduct the exam and track user's answers and score.

        Args:
            questions (List[Dict]): List of exam questions

        Returns:
            Tuple of (score, total possible score)
        """
        total_questions = len(questions)

        # Handle case with no questions
        if total_questions == 0:
            print("Error: No valid questions found in the exam file.")
            sys.exit(1)

        total_score = 1000  # AWS-style scoring
        points_per_question = total_score // total_questions
        user_score = 0

        print(f"\n--- Practice Exam ({total_questions} Questions) ---")

        for i, q in enumerate(questions, 1):
            print(f"\nQuestion {i}: {q['question']}")
            for letter, option in q['options'].items():
                print(f"{letter}. {option}")

            # Handle multiple correct answers
            if len(q['correct_answer']) > 1:
                print(
                    f"\n(Note: This question requires {len(q['correct_answer'])} correct answers)")
                user_answers = []
                while len(user_answers) < len(q['correct_answer']):
                    user_input = input(
                        f"Enter answer {len(user_answers) + 1} (A/B/C/D/E): ").upper()
                    if user_input in q['options'].keys() and user_input not in user_answers:
                        user_answers.append(user_input)
                    else:
                        print("Invalid input or duplicate answer. Please try again.")

                # Check if user's answers match all correct answers
                if set(user_answers) == set(q['correct_answer']):
                    user_score += points_per_question
                    print("✅ Correct!")
                else:
                    print(
                        f"❌ Incorrect. Correct answer(s) were {', '.join(q['correct_answer'])}.")

            # Single answer questions
            else:
                while True:
                    user_answer = input("\nYour answer (A/B/C/D/E): ").upper()
                    if user_answer in q['options'].keys():
                        break
                    print("Invalid input. Please enter A, B, C, D, or E.")

                if user_answer == q['correct_answer'][0]:
                    user_score += points_per_question
                    print("✅ Correct!")
                else:
                    print(
                        f"❌ Incorrect. Correct answer was {q['correct_answer'][0]}.")

        print(f"\n--- Exam Results ---")
        print(f"Total Score: {user_score}/{total_score}")
        print(f"Percentage: {user_score/total_score*100:.2f}%")

        return user_score, total_score


def main():
    parser = argparse.ArgumentParser(
        description='Take an exam from a markdown file')
    parser.add_argument('exam_file', help='Path to the markdown exam file')
    args = parser.parse_args()

    # Validate file exists and is a markdown file
    if not os.path.exists(args.exam_file):
        print(f"Error: File {args.exam_file} does not exist.")
        sys.exit(1)

    if not args.exam_file.lower().endswith('.md'):
        print("Error: File must be a markdown (.md) file.")
        sys.exit(1)

    # Parse exam
    questions = ExamParser.parse_exam(args.exam_file)

    # Take exam
    ExamTaker.take_exam(questions)


if __name__ == "__main__":
    main()
