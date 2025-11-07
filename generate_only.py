#!/usr/bin/env python3
"""
Standalone script to run only the generator without transformations or translations.
"""
import argparse
import os
from src.generators.generator import Generator
from src.utils import random, save_text
from src.generators.config import cfg
from src.translators.kotlin import KotlinTranslator
from src.translators.groovy import GroovyTranslator
from src.translators.java import JavaTranslator
from src.translators.typescript import TypeScriptTranslator

# Map of translators for different languages
TRANSLATORS = {
    'kotlin': KotlinTranslator,
    'groovy': GroovyTranslator,
    'java': JavaTranslator,
    'typescript': TypeScriptTranslator
}

def main():
    parser = argparse.ArgumentParser(description='Run generator only without transformations')
    parser.add_argument('--language',
                        choices=['kotlin', 'groovy', 'java', 'typescript'],
                        default='kotlin',
                        help='Target language')
    parser.add_argument('--max-depth',
                        type=int,
                        default=6,
                        help='Maximum depth for generation')
    parser.add_argument('--disable-use-site-variance',
                        action='store_true',
                        help='Disable use-site variance')
    parser.add_argument('--disable-bounded-type-parameters',
                        action='store_true',
                        help='Disable bounded type parameters')
    parser.add_argument('--disable-parameterized-functions',
                        action='store_true',
                        help='Disable parameterized functions')
    parser.add_argument('--output-dir',
                        default='./generated_programs',
                        help='Output directory for generated programs')
    parser.add_argument('--output-ir',
                        action='store_true',
                        help='Save the IR program as human-readable text')
    parser.add_argument('--translate',
                        action='store_true',
                        help='Also translate to target language (optional)')
    parser.add_argument('-n', '--num-programs',
                        type=int,
                        default=1,
                        help='Number of programs to generate')

    args = parser.parse_args()

    # Configure generator
    cfg.dis.use_site_variance = args.disable_use_site_variance
    cfg.limits.max_depth = args.max_depth
    if args.disable_bounded_type_parameters:
        cfg.prob.bounded_type_parameters = 0
    if args.disable_parameterized_functions:
        cfg.prob.parameterized_functions = 0

    # Setup random
    random.remove_reserved_words(args.language)

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    print(f"Generating {args.num_programs} program(s) for {args.language}...")
    print(f"Max depth: {args.max_depth}")
    print(f"Output directory: {args.output_dir}")
    print()

    for i in range(args.num_programs):
        print(f"Generating program {i+1}/{args.num_programs}...")

        # Generate program
        generator = Generator(
            language=args.language,
            logger=None,
            options={}
        )
        program = generator.generate()

        # Save IR if requested
        if args.output_ir:
            ir_file = os.path.join(args.output_dir, f'program_{i+1}.ir.txt')
            ir_string = str(program)
            save_text(ir_file, ir_string)
            print(f"  ✓ Saved IR to: {ir_file}")

        # Translate if requested
        if args.translate:
            translator = TRANSLATORS[args.language]('generated', {})
            translator.visit(program)
            code = translator.result()

            ext_map = {
                'kotlin': 'kt',
                'groovy': 'groovy',
                'java': 'java',
                'typescript': 'ts'
            }
            ext = ext_map[args.language]
            code_file = os.path.join(args.output_dir, f'program_{i+1}.{ext}')
            save_text(code_file, code)
            print(f"  ✓ Translated to: {code_file}")

        print(f"  ✓ Generated program {i+1} successfully")
        print()

    print(f"Done! Generated {args.num_programs} program(s)")

if __name__ == '__main__':
    main()
