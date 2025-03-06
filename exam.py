import sys
import re
import os
import argparse
from typing import List, Dict, Tuple
import time


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
        for q_idx, q_text in enumerate(questions_raw, 1):
            # Extract question text before options (handle line breaks with <br/>)
            q_text = q_text.replace("<br/>", " ")

            # Try different option formats
            match = None
            # Format: '    - A. Option text'
            match = re.match(
                r'(.*?)\n((?:\s+- [A-E]\.\s.*\n)+)', q_text, re.DOTALL)

            if not match:
                # Alternative format: '    - A) Option text' or other variations
                match = re.match(
                    r'(.*?)\n((?:\s+- [A-E][\.\)]\s.*\n)+)', q_text, re.DOTALL)

            if not match:
                print(f"Warning: Could not parse question {q_idx}. Skipping.")
                continue

            question = match.group(1).strip()
            options_text = match.group(2)

            # Extract options (handle different formats)
            options = {}
            # Look for patterns like: '    - A. Text' or '    - A) Text' with any amount of spacing
            for opt_match in re.finditer(r'\s+- ([A-E])[\.\)]\s(.*?)(?=\n\s+- [A-E][\.\)]|\n\n|\n\s*<details|\n\s*$)', options_text, re.DOTALL):
                letter = opt_match.group(1)
                option_text = opt_match.group(2).strip()
                options[letter] = option_text

            # Extract correct answer(s)
            correct_answers = []

            # Look for the details section
            details_match = re.search(
                r'<details.*?>(.*?)</details>', q_text, re.DOTALL)
            if details_match:
                details_content = details_match.group(1)

                # First, look for "Correct Answer: X, Y" format
                correct_ans_match = re.search(
                    r'Correct [Aa]nswer:?\s*([A-E](,\s*[A-E])*)', details_content)
                if correct_ans_match:
                    ans_string = correct_ans_match.group(1).strip()
                    correct_answers = [a.strip() for a in re.split(
                        r',\s*', ans_string) if a.strip() in 'ABCDE']

                # If that didn't work, try looking for just the letters
                elif re.search(r'Answer</summary>\s*\n*\s*([A-E](,\s*[A-E])*)', details_content):
                    ans_string = re.search(
                        r'Answer</summary>\s*\n*\s*([A-E](,\s*[A-E])*)', details_content).group(1).strip()
                    correct_answers = [a.strip() for a in re.split(
                        r',\s*', ans_string) if a.strip() in 'ABCDE']

                # If still nothing, try looking for concatenated answers like "AC"
                elif re.search(r'Answer</summary>\s*\n*\s*([A-E]+)', details_content):
                    ans_string = re.search(
                        r'Answer</summary>\s*\n*\s*([A-E]+)', details_content).group(1).strip()
                    correct_answers = [a for a in ans_string if a in 'ABCDE']

            # If no answers found in details section, try elsewhere in the question
            if not correct_answers:
                answer_match = re.search(
                    r'Correct [Aa]nswer:?\s*([A-E](?:[,\s]+[A-E])*)', q_text, re.DOTALL)
                if answer_match:
                    ans_string = answer_match.group(1).strip()
                    if ',' in ans_string:
                        correct_answers = [a.strip() for a in re.split(
                            r',\s*', ans_string) if a.strip() in 'ABCDE']
                    elif ' ' in ans_string:
                        correct_answers = [
                            a for a in ans_string.split() if a in 'ABCDE']
                    else:
                        correct_answers = [
                            a for a in ans_string if a in 'ABCDE']

            # Validate correct answers exist in options
            valid_answers = [
                ans for ans in correct_answers if ans in options.keys()]

            # Skip question if no valid answers
            if not valid_answers:
                print(
                    f"Warning: No valid answers found for question {q_idx}. Skipping.")
                continue

            parsed_questions.append({
                'question': question,
                'options': options,
                'correct_answer': valid_answers,
                'multi_answer': len(valid_answers) > 1
            })

        return parsed_questions


class ExamTaker:
    @staticmethod
    def take_exam(questions: List[Dict[str, str]], timer_duration: int) -> Tuple[int, int]:
        """
        Conduct the exam and track user's answers and score, with a timer.

        Args:
            questions (List[Dict]): List of exam questions
            timer_duration (int): The duration of the exam in seconds (e.g., 900 for 15 minutes)

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
        print(f"Time limit: {timer_duration // 60} minutes")

        start_time = time.time()  # Start the timer
        for i, q in enumerate(questions, 1):
            # Check if the timer has run out before proceeding
            elapsed_time = time.time() - start_time
            if elapsed_time >= timer_duration:
                print(f"\nTime's up! The exam has ended.")
                break

            print(f"\nQuestion {i}/{total_questions}: {q['question']}")
            for letter in sorted(q['options'].keys()):
                print(f"{letter}. {q['options'][letter]}")

            # Handle multiple correct answers
            if q['multi_answer']:
                num_correct = len(q['correct_answer'])
                print(
                    f"\n(This question requires {num_correct} correct answers)")

                # Collect all answers before checking
                user_answers = []
                for j in range(num_correct):
                    while True:
                        user_input = input(
                            f"Enter answer {j+1}/{num_correct} (A-E): ").upper()
                        if user_input in q['options'].keys():
                            if user_input not in user_answers:
                                user_answers.append(user_input)
                                break
                            else:
                                print(
                                    "You've already entered this answer. Please choose another option.")
                        else:
                            print(
                                f"Invalid input. Please enter one of: {', '.join(sorted(q['options'].keys()))}")

                # Sort answers for consistent comparison
                user_answers.sort()
                correct_answers = sorted(q['correct_answer'])

                # Check answers only after collecting all responses
                if user_answers == correct_answers:
                    user_score += points_per_question
                    print("✅ Correct!")
                else:
                    print(
                        f"❌ Incorrect. Correct answer(s) were {', '.join(correct_answers)}.")

            # Single answer questions
            else:
                while True:
                    user_answer = input("\nYour answer (A-E): ").upper()
                    if user_answer in q['options'].keys():
                        break
                    print(
                        f"Invalid input. Please enter one of: {', '.join(sorted(q['options'].keys()))}")

                if user_answer == q['correct_answer'][0]:
                    user_score += points_per_question
                    print("✅ Correct!")
                else:
                    print(
                        f"❌ Incorrect. Correct answer was {q['correct_answer'][0]}.")

        print(f"\n--- Exam Results ---")
        print(f"Total Score: {user_score}/{total_score}")
        print(f"Percentage: {user_score/total_score*100:.2f}%")

        if user_score >= 700:
            print("Congratulations! You have PASSED the exam!")
        else:
            print("You have not passed the exam. Keep studying and try again!")

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

    # Prompt user to select the time limit
    print("\nSelect the time limit for the exam:")
    print("1. 🏃 Speedrunner (5 minutes)")
    print("2. ⚡ Blitz (10 minutes)")
    print("3. ⏱️ Standard (15 minutes)")
    print("4. 🕒 Extended (30 minutes)")
    print("5. 🐢 Tortoise (1 hour)")
    choice = input("Enter 1, 2, 3, 4, or 5: ")

    if choice == "1":
        timer_duration = 5 * 60  # 5 minutes
    elif choice == "2":
        timer_duration = 10 * 60  # 10 minutes
    elif choice == "3":
        timer_duration = 15 * 60  # 15 minutes
    elif choice == "4":
        timer_duration = 30 * 60  # 30 minutes
    elif choice == "5":
        timer_duration = 60 * 60  # 1 hour
    else:
        print("Invalid choice. Defaulting to 15 minutes.")
        timer_duration = 15 * 60  # Default to 15 minutes

    # Parse exam
    questions = ExamParser.parse_exam(args.exam_file)

    # Take exam
    ExamTaker.take_exam(questions, timer_duration)


if __name__ == "__main__":
    main()
